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

from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.config_interactive import main_config_menu_loop
from confluence_markdown_exporter.utils.measure_time import measure

DEBUG: bool = bool(os.getenv("DEBUG"))

app = typer.Typer()


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

    # Always ensure we're filtering for pages if no explicit query is provided
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


if __name__ == "__main__":
    app()
