import logging
import os
import sys
import time
from pathlib import Path
from typing import Annotated

import typer
from requests import HTTPError
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential
from tqdm import tqdm

from clients.open_webui_client import get_open_webui_client
from confluence_markdown_exporter.api_clients import get_api_instances
from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.utils.config_interactive import main_config_menu_loop
from confluence_markdown_exporter.utils.content_collector import ContentCollector
from confluence_markdown_exporter.utils.content_collector import PageContentCollector
from confluence_markdown_exporter.utils.content_collector import SearchContentCollector
from confluence_markdown_exporter.utils.content_collector import SpaceContentCollector
from confluence_markdown_exporter.utils.export_validators import validate_cql_query
from confluence_markdown_exporter.utils.export_validators import validate_page_id
from confluence_markdown_exporter.utils.export_validators import validate_space_key
from confluence_markdown_exporter.utils.measure_time import measure
from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher
from confluence_markdown_exporter.utils.open_webui_exporter import OpenWebUIExporter

DEBUG: bool = bool(os.getenv("DEBUG"))

logger = logging.getLogger(__name__)

app = typer.Typer()

# MetadataEnricher integration
# The MetadataEnricher class is used to add comprehensive Confluence metadata to markdown files.
# It supports different metadata formats (YAML, JSON) and includes methods to add space details,
# page ancestors, attachment details, and compile complete metadata.
# The enricher is integrated with the export process to ensure all exported content includes
# relevant metadata in the frontmatter.
#
# Usage:
# 1. Initialize the MetadataEnricher with an OpenWebUI client
# 2. Use the enrich_page_content method to enrich page content with metadata
# 3. Use the enrich_attachment_content method to enrich attachment content with metadata


def override_output_path_config(value: Path | None) -> None:
    """Override the default output path if provided."""
    if value is not None:
        set_setting("export.output_path", value)


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
def execute_search(cql_query: str, limit: int = 100) -> list[int]:
    """Execute a CQL search with retry logic for transient errors."""
    from confluence_markdown_exporter.confluence import SearchResults

    try:
        results = SearchResults.from_cql(cql_query, limit=limit)
        return results.page_ids
    except HTTPError as e:
        if e.response and e.response.status_code in [429, 502, 503, 504]:
            # Rate limit or server error - will retry
            raise
        if e.response and e.response.status_code == 400:
            # Invalid CQL syntax
            print(f"ERROR: Invalid CQL query syntax: {cql_query}")
            print(
                "Please check CQL syntax. See: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/"
            )
            print("Common issues:")
            print("- Use 'AND' not '&' between conditions")
            print("- Use double quotes around values with spaces")
            print("- Check field names and operators")
            sys.exit(1)
        else:
            # Other HTTP errors
            print(
                f"ERROR: HTTP {e.response.status_code if e.response else 'Unknown'} when executing CQL query"
            )
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error when executing CQL query: {e!s}")
        sys.exit(1)


@app.command(help="Export a single Confluence page by ID or URL to Markdown.")
def page(
    page: Annotated[str, typer.Argument(help="Page ID or URL")],
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page

    with measure(f"Export page {page}"):
        override_output_path_config(output_path)
        _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
        _page.export()


@app.command(help="Export a Confluence page and all its descendant pages by ID or URL to Markdown.")
def page_with_descendants(
    page: Annotated[str, typer.Argument(help="Page ID or URL")],
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page

    with measure(f"Export page {page} with descendants"):
        override_output_path_config(output_path)
        _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
        _page.export_with_descendants()


@app.command(help="Export all Confluence pages of a single space to Markdown.")
def space(
    space_key: Annotated[str, typer.Argument()],
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Space

    with measure(f"Export space {space_key}"):
        override_output_path_config(output_path)
        space = Space.from_key(space_key)
        space.export()


@app.command(help="Export all Confluence pages across all spaces to Markdown.")
def all_spaces(
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Organization

    with measure("Export all spaces"):
        override_output_path_config(output_path)
        org = Organization.from_api()
        org.export()


@app.command(help="Search for Confluence pages using CQL and export to Markdown.")
def search(
    query: Annotated[str, typer.Argument(help="CQL query to search for pages")] = "",
    space: Annotated[str | None, typer.Option()] = None,
    title: Annotated[str | None, typer.Option()] = None,
    label: Annotated[str | None, typer.Option()] = None,
    content: Annotated[str | None, typer.Option()] = None,
    author: Annotated[str | None, typer.Option()] = None,
    limit: Annotated[int, typer.Option()] = 100,
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    """Search for Confluence pages using CQL and export to Markdown.

    This command supports flexible CQL queries with additional parameters.
    You can specify multiple criteria which will be combined with AND.
    """
    # Build CQL query from parameters
    cql_parts = []

    if space:
        cql_parts.append(f"space = '{space}'")
    if title:
        cql_parts.append(f"title ~ '{title}'")
    if label:
        cql_parts.append(f"label = '{label}'")
    if content:
        cql_parts.append(f"content ~ '{content}'")
    if author:
        cql_parts.append(f"author = '{author}'")

    # Add user-provided query if it exists
    if query:
        cql_parts.append(query)

    # Always ensure we're filtering for pages only
    if not query and not cql_parts:
        cql_query = "type = page"
    else:
        # Use the first part as the base query if parameters are provided
        cql_query = cql_parts[0]
        if len(cql_parts) > 1:
            cql_query = f"({cql_query}) AND {' AND '.join(cql_parts[1:])}"

    # Ensure we're always filtering for pages if no explicit query is provided
    if not query and "type = page" not in cql_query.lower():
        cql_query = f"({cql_query}) AND type = page"

    with measure(f"Search for pages with query: {cql_query}"):
        override_output_path_config(output_path)

        # Print the full CQL query
        print(f"Got CQL query: {cql_query}")

        # Execute search with retry logic
        page_ids = execute_search(cql_query, limit=limit)

        # Export results
        if page_ids:
            # Print the first three items from the results
            print("First three items from the results:")
            for i, page_id in enumerate(page_ids[:3]):
                print(f"  {i + 1}. Page ID: {page_id}")

            print(f"Exporting {len(page_ids)} pages...")
            for page_id in page_ids:
                from confluence_markdown_exporter.confluence import Page

                Page.from_id(page_id).export()
            print("Export completed successfully.")
        else:
            print("No pages found matching the search criteria.")


@app.command(help="Open the interactive configuration menu.")
def config(
    jump_to: str = typer.Option(
        None, help="Jump directly to a config submenu, e.g. 'auth.confluence'"
    ),
) -> None:
    """Interactive configuration menu."""
    main_config_menu_loop(jump_to)


@app.command(help="Get detailed information about a Confluence space.")
def space_details(
    space_key: Annotated[str, typer.Argument(help="Space key")],
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    """Get detailed information about a Confluence space."""
    with measure(f"Get space details for {space_key}"):
        override_output_path_config(output_path)
        # Get Confluence client
        confluence, _ = get_api_instances()
        try:
            # Get space details using Confluence API
            space_details = confluence.get_space(space_key, expand="description,homepage")
            if not space_details:
                print(f"Error: No space found with key '{space_key}'")
                return

            print(f"Space details for {space_key}:")
            print(f"  Name: {space_details.get('name', 'N/A')}")
            description = space_details.get("description", {})
            if isinstance(description, dict):
                plain = description.get("plain", {})
                if isinstance(plain, dict):
                    print(f"  Description: {plain.get('value', 'No description')}")
                else:
                    print("  Description: No description")
            else:
                print("  Description: No description")

            homepage = space_details.get("homepage", {})
            if isinstance(homepage, dict):
                print(f"  Homepage: {homepage.get('id', 'N/A')}")
            else:
                print("  Homepage: N/A")
        except Exception as e:
            print(f"Error retrieving space details: {e}")


@app.command(help="Get the ancestor hierarchy for a Confluence page.")
def page_ancestors(
    page_id: Annotated[int, typer.Argument(help="Page ID")],
) -> None:
    """Get the ancestor hierarchy for a Confluence page."""
    with measure(f"Get ancestors for page {page_id}"):
        client = get_open_webui_client()
        ancestors = client.get_page_ancestors(page_id)
        print(f"Ancestors for page {page_id}:")
        for i, ancestor in enumerate(ancestors, 1):
            print(f"  {i}. ID: {ancestor.get('id')}, Title: {ancestor.get('title')}")


@app.command(help="Get detailed information about a Confluence attachment.")
def attachment_details(
    attachment_id: Annotated[str, typer.Argument(help="Attachment ID")],
) -> None:
    """Get detailed information about a Confluence attachment."""
    with measure(f"Get details for attachment {attachment_id}"):
        client = get_open_webui_client()
        details = client.get_attachment_details(attachment_id)
        print(f"Details for attachment {attachment_id}:")
        print(f"  Title: {details.get('title')}")
        print(f"  File size: {details.get('extensions', {}).get('fileSize', 0)} bytes")
        print(f"  Media type: {details.get('extensions', {}).get('mediaType', '')}")
        print(f"  Version: {details.get('version', {}).get('number', 0)}")


@app.command(help="Compile complete metadata for a Confluence page.")
def page_metadata(
    page_id: Annotated[int, typer.Argument(help="Page ID")],
    output_path: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    """Compile complete metadata for a Confluence page."""
    import json

    with measure(f"Compile metadata for page {page_id}"):
        override_output_path_config(output_path)
        client = get_open_webui_client()
        metadata = client.compile_metadata(page_id)

        # Print summary
        print(f"Metadata for page {page_id}:")
        print(f"  Title: {metadata.get('title')}")
        print(f"  Space: {metadata.get('space', {}).get('key')}")
        print(f"  Ancestors: {len(metadata.get('ancestors', []))}")
        print(f"  Attachments: {len(metadata.get('attachments', []))}")

        # Save to file
        output_file = (
            output_path / f"page_{page_id}_metadata.json"
            if output_path
            else Path(f"page_{page_id}_metadata.json")
        )
        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {output_file}")


# Create a subapp for export-to-open-webui with subcommands
export_app = typer.Typer(help="Export content to Open-WebUI knowledge base.")
app.add_typer(export_app, name="export-to-open-webui")


def _export_content_to_open_webui(
    content_collector: ContentCollector,
    output_path: Path,
    show_progress: bool = True,
    retry_errors: bool = True,
    max_retries: int = 3,
    filter_image_types: bool = False,
    filter_document_types: bool = False,
    min_size_kb: int | None = None,
    max_size_kb: int | None = None,
) -> None:
    """Export Confluence content to Open-WebUI knowledge base using a content collector.

    This function provides the core export functionality that can be used by different
    export modes (space, page, search) through content collectors.

    Args:
        content_collector: Content collector that defines what to export
        output_path: Directory to save exported files
        show_progress: Display progress information during export
        retry_errors: Enable retry on export errors
        max_retries: Maximum number of retry attempts
        filter_image_types: Filter out common image file types
        filter_document_types: Filter out common document file types
        min_size_kb: Minimum attachment size in KB to include
        max_size_kb: Maximum attachment size in KB to include
    """
    from confluence_markdown_exporter.confluence import Page

    # Step 1: Collect pages using the content collector
    with measure(f"Collect content using {type(content_collector).__name__}"):
        override_output_path_config(output_path)

        if show_progress:
            print(f"Step 1: Collecting content using {content_collector.get_description()}...")

        # Collect pages from the content collector
        pages = content_collector.collect_pages()
        page_ids = [page.id for page in pages]

        # Export pages to local markdown files
        for page in pages:
            page.export()

        if show_progress:
            print(f"Local export completed. Files saved to: {output_path}")

    # Step 2: Upload local files to Open-WebUI
    if show_progress:
        print("Step 2: Uploading local files to Open-WebUI...")

    # Initialize clients
    open_webui_client = get_open_webui_client()

    # Get attachments from all collected pages
    attachments = [att for page in pages for att in page.attachments]

    # Convert attachments to dictionaries for the filter
    attachment_dicts = [
        {
            "id": att.id,
            "title": att.title,
            "filename": att.filename,
            "file_size": att.file_size,
            "file_id": att.file_id,
        }
        for att in attachments
    ]

    # Log attachment data being passed to exporter
    logger.debug(f"Created {len(attachment_dicts)} attachment dictionaries")
    for i, att_dict in enumerate(attachment_dicts[:3]):  # Show first 3
        logger.debug(f"Attachment {i + 1}: {att_dict}")

    # Initialize attachment filter
    attachment_filter = AttachmentFilter()

    # Set environment variables for filter configuration
    if filter_image_types:
        os.environ["FILTER_IMAGE_TYPES"] = "true"
    else:
        os.environ["FILTER_IMAGE_TYPES"] = "false"

    if filter_document_types:
        os.environ["FILTER_DOCUMENT_TYPES"] = "true"
    else:
        os.environ["FILTER_DOCUMENT_TYPES"] = "false"

    if min_size_kb is not None:
        os.environ["MIN_SIZE_KB"] = str(min_size_kb)
    if max_size_kb is not None:
        os.environ["MAX_SIZE_KB"] = str(max_size_kb)

    # Filter attachments
    filtered_result = attachment_filter.filter_attachments(attachment_dicts)
    filtered_attachments = filtered_result["allowed"]
    logger.debug(
        f"After combined filtering: {len(filtered_attachments)} attachments allowed, {len(filtered_result['blocked'])} blocked"
    )

    # Initialize metadata enricher
    metadata_enricher = MetadataEnricher(client=open_webui_client)

    # Initialize exporter
    from confluence_markdown_exporter.api_clients import get_api_instances

    confluence, _ = get_api_instances()

    exporter = OpenWebUIExporter(
        open_webui_client=open_webui_client,
        confluence=confluence,
        attachment_filter=attachment_filter,
        metadata_enricher=metadata_enricher,
        use_batch_upload=True,
    )

    # Convert pages to dictionaries
    page_dicts = [{"id": str(page.id), "title": page.title} for page in pages]

    # Export with progress reporting
    if show_progress:
        print(f"Found {len(pages)} pages and {len(attachments)} attachments")
        print(f"After filtering: {len(filtered_attachments)} attachments will be processed")

    # Export with retry logic
    retry_count = 0
    success = False

    while retry_count <= max_retries:
        try:
            # Show progress bar if enabled
            if show_progress and (len(pages) > 0 or len(filtered_attachments) > 0):
                print("\nUploading pages and attachments to Open-WebUI...")

                # Create a combined progress bar for all items
                total_items = len(pages) + len(filtered_attachments)
                with tqdm(total=total_items, desc="Upload Progress", unit="item") as pbar:
                    # Define a progress callback function
                    def progress_callback(current, total):
                        pbar.update(1)

                    # Export content with progress reporting
                    summary = exporter.export_content(
                        content_collector=content_collector,
                        output_path=str(output_path),
                        pages=page_dicts,
                        attachments=filtered_attachments,
                        progress_callback=progress_callback,
                    )

                    # Update progress for any remaining items
                    pbar.update(total_items - pbar.n)

            else:
                # Export without progress bar
                summary = exporter.export_content(
                    content_collector=content_collector,
                    output_path=str(output_path),
                    pages=page_dicts,
                    attachments=filtered_attachments,
                    progress_callback=None,
                )

            if show_progress:
                print("\nExport Summary:")
                print(f"Total pages: {summary.total_pages}")
                print(f"Total attachments: {summary.total_attachments}")
                print(f"Successful pages: {summary.successful_pages}")
                print(f"Successful attachments: {summary.successful_attachments}")
                print(f"Failed pages: {summary.failed_pages}")
                print(f"Failed attachments: {summary.failed_attachments}")
                print(f"Skipped pages (duplicate): {summary.skipped_pages}")
                print(f"Skipped attachments (duplicate): {summary.skipped_attachments}")
                print(f"Filtered attachments: {summary.filtered_attachments}")

                if summary.failed_pages > 0 or summary.failed_attachments > 0:
                    print("\nFailed items:")
                    for error in summary.errors:
                        print(f"  - {error}")

                if summary.skipped_pages > 0 or summary.skipped_attachments > 0:
                    print("\nSkipped items (duplicate content):")
                    for item in summary.skipped_items:
                        print(f"  - {item}")

                if summary.filtered_attachments > 0:
                    print("\nFiltered items (extension/size filters):")
                    for item in summary.filtered_items:
                        print(f"  - {item}")

            success = True
            break

        except Exception as e:
            retry_count += 1
            if retry_errors and retry_count <= max_retries:
                print(f"Error during export (Attempt {retry_count}/{max_retries}): {e}")
                print("Retrying...")
                time.sleep(2)  # Wait before retry
            else:
                print(f"Error during export: {e}")
                break

    if success:
        print("\nExport completed successfully.")
    else:
        print("\nExport failed after multiple attempts.")


@export_app.command(name="space", help="Export a Confluence space to Open-WebUI knowledge base.")
def export_space(
    space_key: Annotated[str, typer.Argument(help="Confluence space key")],
    output_path: Annotated[Path, typer.Argument(help="Output path for exported files")] = Path(
        "exports"
    ),
    show_progress: Annotated[bool, typer.Option()] = True,
    retry_errors: Annotated[bool, typer.Option()] = True,
    max_retries: Annotated[int, typer.Option()] = 3,
    filter_image_types: Annotated[bool, typer.Option()] = False,
    filter_document_types: Annotated[bool, typer.Option()] = False,
    min_size_kb: Annotated[int | None, typer.Option()] = None,
    max_size_kb: Annotated[int | None, typer.Option()] = None,
) -> None:
    """Export a complete Confluence space to Open-WebUI knowledge base.

    Examples:
    # Export space with default settings
    confluence-markdown-exporter export-to-open-webui space MYSPACE

    # Export with filtering options
    confluence-markdown-exporter export-to-open-webui space MYSPACE --filter-image-types --max-retries 5
    """
    # Validate space key
    try:
        validate_space_key(space_key)
    except ValueError as e:
        print(f"Error: {e}")
        raise typer.Exit(1)

    # Create space content collector
    content_collector = SpaceContentCollector(space_key)

    # Export using the generalized function
    _export_content_to_open_webui(
        content_collector=content_collector,
        output_path=output_path,
        show_progress=show_progress,
        retry_errors=retry_errors,
        max_retries=max_retries,
        filter_image_types=filter_image_types,
        filter_document_types=filter_document_types,
        min_size_kb=min_size_kb,
        max_size_kb=max_size_kb,
    )


@export_app.command(
    name="page", help="Export a single Confluence page to Open-WebUI knowledge base."
)
def export_page(
    page_id: Annotated[str, typer.Argument(help="Confluence page ID")],
    output_path: Annotated[Path, typer.Argument(help="Output path for exported files")] = Path(
        "exports"
    ),
    show_progress: Annotated[bool, typer.Option()] = True,
    retry_errors: Annotated[bool, typer.Option()] = True,
    max_retries: Annotated[int, typer.Option()] = 3,
    filter_image_types: Annotated[bool, typer.Option()] = False,
    filter_document_types: Annotated[bool, typer.Option()] = False,
    min_size_kb: Annotated[int | None, typer.Option()] = None,
    max_size_kb: Annotated[int | None, typer.Option()] = None,
) -> None:
    """Export a single Confluence page to Open-WebUI knowledge base.

    Examples:
    # Export single page
    confluence-markdown-exporter export-to-open-webui page 123456

    # Export with filtering options
    confluence-markdown-exporter export-to-open-webui page 123456 --filter-image-types
    """
    # Validate page ID
    try:
        validate_page_id(page_id)
    except ValueError as e:
        print(f"Error: {e}")
        raise typer.Exit(1)

    # Create page content collector
    content_collector = PageContentCollector(page_id)

    # Export using the generalized function
    _export_content_to_open_webui(
        content_collector=content_collector,
        output_path=output_path,
        show_progress=show_progress,
        retry_errors=retry_errors,
        max_retries=max_retries,
        filter_image_types=filter_image_types,
        filter_document_types=filter_document_types,
        min_size_kb=min_size_kb,
        max_size_kb=max_size_kb,
    )


@export_app.command(
    name="search", help="Export pages found by CQL search to Open-WebUI knowledge base."
)
def export_search(
    cql_query: Annotated[str, typer.Argument(help="CQL query to search for pages")],
    output_path: Annotated[Path, typer.Argument(help="Output path for exported files")] = Path(
        "exports"
    ),
    limit: Annotated[int, typer.Option()] = 100,
    show_progress: Annotated[bool, typer.Option()] = True,
    retry_errors: Annotated[bool, typer.Option()] = True,
    max_retries: Annotated[int, typer.Option()] = 3,
    filter_image_types: Annotated[bool, typer.Option()] = False,
    filter_document_types: Annotated[bool, typer.Option()] = False,
    min_size_kb: Annotated[int | None, typer.Option()] = None,
    max_size_kb: Annotated[int | None, typer.Option()] = None,
) -> None:
    """Export pages found by CQL search to Open-WebUI knowledge base.

    Examples:
    # Export pages from specific space
    confluence-markdown-exporter export-to-open-webui search "space = MYSPACE"

    # Export pages with specific label
    confluence-markdown-exporter export-to-open-webui search "label = important" --limit 50
    """
    # Validate CQL query
    try:
        validate_cql_query(cql_query, limit)
    except ValueError as e:
        print(f"Error: {e}")
        raise typer.Exit(1)

    # Create search content collector
    content_collector = SearchContentCollector(cql_query, limit)

    # Export using the generalized function
    _export_content_to_open_webui(
        content_collector=content_collector,
        output_path=output_path,
        show_progress=show_progress,
        retry_errors=retry_errors,
        max_retries=max_retries,
        filter_image_types=filter_image_types,
        filter_document_types=filter_document_types,
        min_size_kb=min_size_kb,
        max_size_kb=max_size_kb,
    )


if __name__ == "__main__":
    app()
