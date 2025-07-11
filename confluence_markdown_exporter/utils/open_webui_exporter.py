"""Module for exporting content to Open-WebUI."""

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from atlassian import Confluence as ConfluenceApiSdk
from typing_extensions import TypedDict

from clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.utils.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.utils.content_collector import ContentCollector
from confluence_markdown_exporter.utils.export import sanitize_filename
from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher
from confluence_markdown_exporter.utils.open_webui_export_summary import OpenWebUIExportSummary

logger = logging.getLogger(__name__)


class OpenWebUIExporter:
    """Exports Confluence content to Open-WebUI knowledge base."""

    def __init__(
        self,
        open_webui_client: OpenWebUIClient,
        confluence: ConfluenceApiSdk,
        attachment_filter: AttachmentFilter,
        metadata_enricher: MetadataEnricher,
        use_batch_upload: bool = True,
    ):
        """Initialize the Open-WebUI exporter.

        Args:
            open_webui_client: Client for Open-WebUI API
            confluence: Client for Confluence API
            attachment_filter: Filter for attachments
            metadata_enricher: Enricher for metadata
            use_batch_upload: Whether to use batch upload for better performance

        Raises:
            ValueError: If any required parameter is missing or invalid
        """
        # Validate required parameters
        if not open_webui_client:
            raise ValueError("Open-WebUI client must be provided")
        if not confluence:
            raise ValueError("Confluence client must be provided")
        if not attachment_filter:
            raise ValueError("Attachment filter must be provided")
        if not metadata_enricher:
            raise ValueError("Metadata enricher must be provided")

        self.open_webui_client = open_webui_client
        self.confluence = confluence
        self.attachment_filter = attachment_filter
        self.metadata_enricher = metadata_enricher
        self.use_batch_upload = use_batch_upload
        self.knowledge_base_name = None
        self.knowledge_base_id = None

        # Test connection to Open-WebUI
        if not self.open_webui_client.test_connection():
            raise ConnectionError("Failed to connect to Open-WebUI API")

        logger.info("Initialized Open-WebUI exporter")

    def export_content(
        self,
        content_collector: ContentCollector,
        output_path: str,
        pages: list[dict[str, Any]],
        attachments: list[dict[str, Any]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OpenWebUIExportSummary:
        """Export Confluence content to Open-WebUI using a content collector.

        Args:
            content_collector: Content collector that defines what to export
            output_path: Local output path for files
            pages: List of page dictionaries
            attachments: List of attachment dictionaries
            progress_callback: Optional callback for progress reporting

        Returns:
            Export summary with results

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate required parameters
        if not content_collector:
            raise ValueError("Content collector must be provided")
        if not output_path:
            raise ValueError("Output path must be provided")
        if not pages:
            raise ValueError("At least one page must be provided")
        if not isinstance(pages, list):
            raise ValueError("Pages must be provided as a list")

        start_time = datetime.now()

        # Get spaces involved and determine knowledge base name
        space_keys = content_collector.get_spaces_involved()
        if not space_keys:
            logger.error("Content collector returned no spaces")
            return self._create_failed_summary(
                "Unknown", "No spaces found for content", len(pages), len(attachments)
            )

        # Use the first space for knowledge base naming (primary space)
        primary_space_key = space_keys[0]

        # Get space details to determine knowledge base name
        try:
            space_details = self.confluence.get_space(primary_space_key, expand="homepage")
            knowledge_base_name = (
                space_details.get("name", primary_space_key) if space_details else primary_space_key
            )
        except Exception as e:
            logger.warning(f"Could not get space details for {primary_space_key}: {e}")
            knowledge_base_name = primary_space_key

        # Create description based on content collector
        description = content_collector.get_description()

        # Filter attachments first to get accurate counts
        filtered_attachments = self.attachment_filter.filter_attachments(attachments)
        allowed_attachments = filtered_attachments["allowed"]
        blocked_attachments = filtered_attachments["blocked"]

        # Initialize summary with correct counts
        summary = OpenWebUIExportSummary(
            knowledge_base_name=knowledge_base_name,
            knowledge_base_id="",
            total_pages=len(pages),
            total_attachments=len(attachments),  # Total includes both allowed and blocked
            successful_pages=0,
            successful_attachments=0,
            failed_pages=0,
            failed_attachments=0,
            skipped_pages=0,
            skipped_attachments=0,
            filtered_attachments=len(blocked_attachments),  # Track filtered attachments
            start_time=start_time,
        )

        try:
            # Create or get knowledge base
            knowledge_base = self._create_or_get_knowledge_base(knowledge_base_name, description)
            if not knowledge_base:
                logger.error(f"Failed to create knowledge base for {knowledge_base_name}")
                summary.add_page_failure("Failed to create knowledge base")
                return summary

            kb_id = knowledge_base.get("id")
            if not kb_id:
                logger.error(f"Knowledge base ID is missing for {knowledge_base_name}")
                summary.add_page_failure("Knowledge base ID is missing")
                return summary

            summary.knowledge_base_id = kb_id

            logger.info(f"Using knowledge base: {knowledge_base.get('name')} (ID: {kb_id})")

            # Store knowledge base name and ID for logging and uploads
            self.knowledge_base_name = knowledge_base_name
            self.knowledge_base_id = kb_id

            logger.info(f"Processing {len(pages)} pages and {len(allowed_attachments)} attachments")
            logger.debug(
                f"Attachment filtering results: {len(allowed_attachments)} allowed, {len(blocked_attachments)} blocked"
            )

            # Add filtered attachments to summary with details
            for blocked_attachment in blocked_attachments:
                attachment_title = blocked_attachment.get("title", "Unknown")
                # Determine the reason for filtering
                extension = self.attachment_filter._get_extension(blocked_attachment)
                reason = f"extension filter ({extension})" if extension else "extension filter"
                summary.add_attachment_filtered(attachment_title, reason)

            # Export pages
            uploaded_file_ids = []
            for i, page in enumerate(pages):
                try:
                    file_id = self._export_page(
                        page, output_path, primary_space.key, i + 1, len(pages)
                    )
                    if file_id == "DUPLICATE_CONTENT":
                        # Handle duplicate content as skipped, not failed
                        summary.add_page_skipped(page.get("title", "Unknown"))
                    elif file_id:
                        uploaded_file_ids.append(file_id)
                        summary.add_page_success()
                    else:
                        summary.add_page_failure(
                            f"Failed to export page {page.get('title', 'Unknown')}"
                        )
                except Exception as e:
                    logger.error(f"Error exporting page {page.get('title', 'Unknown')}: {e}")
                    summary.add_page_failure(str(e))

                # Update progress if callback provided
                if progress_callback:
                    progress_callback(i + 1, len(pages))

            # Export attachments
            for i, attachment in enumerate(allowed_attachments):
                try:
                    file_id = self._export_attachment(
                        attachment, output_path, primary_space_key, i + 1, len(allowed_attachments)
                    )
                    if file_id == "DUPLICATE_CONTENT":
                        # Handle duplicate content as skipped, not failed
                        summary.add_attachment_skipped(attachment.get("title", "Unknown"))
                    elif file_id:
                        uploaded_file_ids.append(file_id)
                        summary.add_attachment_success()
                    else:
                        summary.add_attachment_failure(
                            f"Failed to export attachment {attachment.get('title', 'Unknown')}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error exporting attachment {attachment.get('title', 'Unknown')}: {e}"
                    )
                    summary.add_attachment_failure(str(e))

                # Update progress if callback provided
                if progress_callback:
                    page_count = len(pages)
                    attachment_index = i + 1
                    total_items = page_count + len(allowed_attachments)
                    current_item = page_count + attachment_index
                    progress_callback(current_item, total_items)

            # Register files with knowledge base
            if uploaded_file_ids and kb_id:
                # Validate file IDs before uploading
                if not all(isinstance(file_id, str) and file_id for file_id in uploaded_file_ids):
                    logger.error("Invalid file ID detected, skipping file registration")
                else:
                    # Batch upload not available, use individual uploads
                    for file_id in uploaded_file_ids:
                        try:
                            response = self.open_webui_client.add_file_to_knowledge(
                                kb_id, {"file_id": file_id}
                            )
                            if not response or not response.get("success"):
                                logger.error(
                                    f"Failed to register file {file_id} with knowledge base"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error registering file {file_id} with knowledge base: {e}"
                            )

            # OpenWebUIExportSummary.end_time is Optional[datetime]
            if summary.end_time is None:
                summary.end_time = None  # Type: ignore

            logger.info(
                f"Export completed: {summary.total_successful}/{summary.total_files} files successful"
            )
            logger.info(summary.get_summary_text())

            return summary

        except Exception as e:
            logger.error(f"Export failed: {e}")
            summary.add_page_failure(f"Export failed: {e!s}")
            # OpenWebUIExportSummary.end_time is Optional[datetime]
            if summary.end_time is None:
                summary.end_time = None  # Type: ignore
            return summary

    def export_space(
        self,
        space_key: str,
        output_path: str,
        pages: list[dict[str, Any]],
        attachments: list[dict[str, Any]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OpenWebUIExportSummary:
        """Export a complete Confluence space to Open-WebUI.

        This method provides backward compatibility with the original interface.
        It creates a SpaceContentCollector and delegates to export_content.

        Args:
            space_key: The Confluence space key
            output_path: Local output path for files
            pages: List of page dictionaries
            attachments: List of attachment dictionaries
            progress_callback: Optional callback for progress reporting

        Returns:
            Export summary with results

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        from confluence_markdown_exporter.utils.content_collector import SpaceContentCollector

        # Create a space content collector for backward compatibility
        content_collector = SpaceContentCollector(space_key)

        # Delegate to the generalized export_content method
        return self.export_content(
            content_collector=content_collector,
            output_path=output_path,
            pages=pages,
            attachments=attachments,
            progress_callback=progress_callback,
        )

    def _create_or_get_knowledge_base(
        self, knowledge_base_name: str, description: str
    ) -> dict[str, Any] | None:
        """Create or get knowledge base.

        Args:
            knowledge_base_name: Name for the knowledge base
            description: Description for the knowledge base

        Returns:
            Knowledge base object or None if failed
        """
        try:
            knowledge_bases = self.open_webui_client.get_knowledge()

            # Check if knowledge base already exists
            # Handle both list and dict responses for API compatibility
            if isinstance(knowledge_bases, list):
                kb_list = knowledge_bases
            else:
                kb_list = knowledge_bases.get("items", [])

            for kb in kb_list:
                # Ensure kb is a dictionary before accessing attributes
                if isinstance(kb, dict) and kb.get("name") == knowledge_base_name:
                    logger.info(
                        f"Found existing knowledge base: {kb.get('name')} (ID: {kb.get('id')})"
                    )
                    return kb

            # Create new knowledge base
            data = {"name": knowledge_base_name, "description": description}
            result = self.open_webui_client.create_knowledge(data)
            logger.info(
                f"Created new knowledge base: {result.get('name')} (ID: {result.get('id')})"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to create/get knowledge base: {e}")
            return None

    def _export_page(
        self, page: dict[str, Any], output_path: str, space_key: str, current: int, total: int
    ) -> str | None:
        """Export a single page to Open-WebUI.

        Args:
            page: Page dictionary
            output_path: Local output path
            space_key: Confluence space key
            current: Current page number
            total: Total pages

        Returns:
            File ID if successful, None otherwise
        """
        page_id = page.get("id")
        page_title = page.get("title", "Unknown")

        try:
            logger.info(f"Exporting page {current}/{total}: {page_title}")

            # Get complete page metadata
            page_metadata = self.confluence.get_page_by_id(
                page_id,
                expand="body.view,body.export_view,body.editor2,metadata.labels,metadata.properties,ancestors",
            )

            # Read page content from local file
            page_content = self._read_page_content(output_path, page, space_key)
            if not page_content:
                logger.error(f"Could not read content for page {page_title}")
                return None

            # Ensure page_metadata is a dict
            if isinstance(page_metadata, dict):
                # Use filtering for Open WebUI to remove Confluence API internals
                enriched_content = self.metadata_enricher.enrich_page_content(
                    page_content, page_metadata, filter_for_openwebui=True
                )
            else:
                enriched_content = page_content

            # Generate filename
            filename = self._generate_safe_filename(page_title, ".md")

            # Create file data
            file_data = {
                "filename": filename,
                "content": enriched_content,
                "content_type": "text/markdown",
            }

            # Ensure knowledge_base_id is set
            if self.knowledge_base_id:
                file_obj = self.open_webui_client.add_file_to_knowledge(
                    self.knowledge_base_id, file_data
                )

                # Check if this is a duplicate content response
                if self.open_webui_client.is_duplicate_content_error(file_obj):
                    logger.info(
                        f"Uploading '{filename}' to knowledge base '{self.knowledge_base_name}'... "
                        f"Skipped (duplicate content detected)"
                    )
                    return "DUPLICATE_CONTENT"

            else:
                logger.error("Knowledge base ID not set, cannot upload file")
                return None

            logger.info(
                f"Uploading '{filename}' to knowledge base '{self.knowledge_base_name}'... Success"
            )
            return file_obj.get("id")

        except Exception as e:
            logger.error(
                f"Uploading '{page_title}' to knowledge base '{self.knowledge_base_name}'... Failed: {e!s}"
            )
            return None

    def _export_attachment(
        self, attachment: dict[str, Any], output_path: str, space_key: str, current: int, total: int
    ) -> str | None:
        """Export a single attachment to Open-WebUI.

        Args:
            attachment: Attachment dictionary
            output_path: Local output path
            space_key: Confluence space key
            current: Current attachment number
            total: Total attachments

        Returns:
            File ID if successful, None otherwise
        """
        attachment_id = attachment.get("id")
        attachment_title = attachment.get("title", "Unknown")

        try:
            logger.info(f"Exporting attachment {current}/{total}: {attachment_title}")

            # Read attachment content from local file
            attachment_content = self._read_attachment_content(output_path, attachment, space_key)
            if attachment_content is None:
                logger.error(f"Could not read content for attachment {attachment_title}")
                return None

            # Determine if this is a text file that can be enriched
            is_text = self.attachment_filter.is_text_file(attachment_title)

            if is_text and isinstance(attachment_content, str):
                # For text files, we can add basic metadata without API calls
                enriched_content = f"# {attachment_title}\n\n{attachment_content}"
            else:
                # Binary content - use as-is
                enriched_content = attachment_content

            # Generate safe filename
            filename = self._generate_safe_filename(attachment_title)

            # Get content type
            content_type = self.attachment_filter.get_content_type(attachment_title)

            # Create file data
            file_data = {
                "filename": filename,
                "content": enriched_content,
                "content_type": content_type,
            }

            # Ensure knowledge_base_id is set
            if self.knowledge_base_id:
                file_obj = self.open_webui_client.add_file_to_knowledge(
                    self.knowledge_base_id, file_data
                )

                # Check if this is a duplicate content response
                if self.open_webui_client.is_duplicate_content_error(file_obj):
                    logger.info(
                        f"Uploading '{filename}' to knowledge base '{self.knowledge_base_name}'... "
                        f"Skipped (duplicate content detected)"
                    )
                    return "DUPLICATE_CONTENT"

            else:
                logger.error("Knowledge base ID not set, cannot upload file")
                return None

            logger.info(
                f"Uploading '{filename}' to knowledge base '{self.knowledge_base_name}'... Success"
            )
            return file_obj.get("id")

        except Exception as e:
            logger.error(
                f"Uploading '{attachment_title}' to knowledge base '{self.knowledge_base_name}'... Failed: {e!s}"
            )
            return None

    def _read_page_content(
        self, output_path: str, page: dict[str, Any], space_key: str
    ) -> str | None:
        """Read page content from local file.

        Args:
            output_path: Local output path
            page: Page dictionary
            space_key: Confluence space key

        Returns:
            Page content as string or None if failed
        """
        try:
            # Get space details to find the actual space name
            space_details = self.confluence.get_space(space_key)
            space_name = space_details.get("name", space_key) if space_details else space_key

            # Construct file path based on export configuration
            page_title = page.get("title", "")
            safe_title = self._generate_safe_filename(page_title, ".md")

            # Try different possible paths based on actual export structure
            possible_paths = [
                # Standard export structure: space_name/space_name/page.md
                Path(space_name) / space_name / safe_title,
                Path(space_name) / space_name / f"{page_title}.md",
                # Alternative structures
                Path(output_path) / space_key / safe_title,
                Path(output_path) / space_key / page_title / f"{page_title}.md",
                Path(output_path) / safe_title,
                Path(output_path) / space_name / safe_title,
                Path(output_path) / space_name / space_name / safe_title,
            ]

            for file_path in possible_paths:
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()

            logger.error(f"Could not find page file for {page_title}")
            logger.debug(f"Searched paths: {[str(p) for p in possible_paths]}")
            return None

        except Exception as e:
            logger.error(f"Error reading page content: {e}")
            return None

    def _read_attachment_content(
        self, output_path: str, attachment: dict[str, Any], space_key: str
    ) -> bytes | None:
        """Read attachment content from local file.

        Args:
            output_path: Local output path
            attachment: Attachment dictionary
            space_key: Confluence space key

        Returns:
            Attachment content as bytes or None if failed
        """
        try:
            # Get space details to find the actual space name
            space_details = self.confluence.get_space(space_key)
            space_name = space_details.get("name", space_key) if space_details else space_key

            # Construct file path based on export configuration
            attachment_title = attachment.get("title", "")
            attachment_id = attachment.get("id", "")
            attachment_file_id = attachment.get("file_id", "")  # This is the key field!
            attachment_filename = attachment.get("filename", "")

            # Log attachment processing for debugging
            logger.debug(
                f"Processing attachment - title: '{attachment_title}', id: '{attachment_id}', file_id: '{attachment_file_id}', filename: '{attachment_filename}'"
            )

            # Try different possible paths based on actual export structure
            # Priority: Use file_id-based filenames first, then fallback to other patterns
            possible_paths = []

            # PRIORITY 1: Use the filename property if available (file_id + extension)
            if attachment_filename:
                possible_paths.extend(
                    [
                        Path(space_name) / "attachments" / attachment_filename,
                        Path(output_path) / space_name / "attachments" / attachment_filename,
                    ]
                )

            # PRIORITY 2: Use file_id with common extensions if file_id is available
            if attachment_file_id:
                common_extensions = [
                    ".svg",
                    ".pdf",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".docx",
                    ".xlsx",
                    ".pptx",
                    ".txt",
                ]
                for ext in common_extensions:
                    possible_paths.extend(
                        [
                            Path(space_name) / "attachments" / f"{attachment_file_id}{ext}",
                            Path(output_path)
                            / space_name
                            / "attachments"
                            / f"{attachment_file_id}{ext}",
                        ]
                    )

            # PRIORITY 3: Use attachment title as filename
            if attachment_title:
                possible_paths.extend(
                    [
                        Path(space_name) / "attachments" / attachment_title,
                        Path(output_path) / space_name / "attachments" / attachment_title,
                        Path(output_path) / space_key / "attachments" / attachment_title,
                        Path(output_path) / "attachments" / attachment_title,
                        Path(output_path) / attachment_title,
                    ]
                )

            # PRIORITY 4: Fallback to attachment_id with common extensions
            if attachment_id:
                common_extensions = [
                    ".svg",
                    ".pdf",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".docx",
                    ".xlsx",
                    ".pptx",
                    ".txt",
                ]
                for ext in common_extensions:
                    possible_paths.extend(
                        [
                            Path(space_name) / "attachments" / f"{attachment_id}{ext}",
                            Path(output_path)
                            / space_name
                            / "attachments"
                            / f"{attachment_id}{ext}",
                        ]
                    )

            for file_path in possible_paths:
                if file_path.exists():
                    mode = "r" if self.attachment_filter.is_text_file(str(file_path)) else "rb"
                    encoding = "utf-8" if mode == "r" else None

                    logger.debug(f"Successfully found attachment at: {file_path}")
                    with open(file_path, mode, encoding=encoding) as f:
                        return f.read()

            logger.error(f"Could not find attachment file for {attachment_title}")
            logger.debug(f"Searched paths: {[str(p) for p in possible_paths]}")
            return None

        except Exception as e:
            logger.error(f"Error reading attachment content: {e}")
            return None

    def _register_files_with_knowledge_base(self, knowledge_base_id: str, file_ids: list[str]):
        """Register files with knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base
            file_ids: List of file IDs to register
        """
        try:
            # Batch upload not available, use individual uploads
            for file_id in file_ids:
                self.open_webui_client.add_file_to_knowledge(
                    knowledge_base_id, {"file_id": file_id}
                )

            logger.info(f"Successfully registered {len(file_ids)} files with knowledge base")

        except Exception as e:
            logger.error(f"Failed to register files with knowledge base: {e}")

    def _generate_safe_filename(self, title: str, extension: str = "") -> str:
        """Generate a safe filename for Open-WebUI.

        Args:
            title: Original title
            extension: File extension to add

        Returns:
            Safe filename
        """
        # Clean up the title
        safe_title = sanitize_filename(title)

        # Add extension if not present
        if extension and not safe_title.endswith(extension):
            safe_title += extension

        return safe_title

    def _create_failed_summary(
        self,
        knowledge_base_name: str,
        error_message: str,
        total_pages: int = 0,
        total_attachments: int = 0,
    ) -> OpenWebUIExportSummary:
        """Create a summary for failed export.

        Args:
            knowledge_base_name: The knowledge base name
            error_message: Error message
            total_pages: Total number of pages (default: 0)
            total_attachments: Total number of attachments (default: 0)

        Returns:
            Export summary with failure
        """
        summary = OpenWebUIExportSummary(
            knowledge_base_name=knowledge_base_name,
            knowledge_base_id="",
            total_pages=total_pages,
            total_attachments=total_attachments,
            successful_pages=0,
            successful_attachments=0,
            failed_pages=1,
            failed_attachments=0,
            skipped_pages=0,
            skipped_attachments=0,
            filtered_attachments=0,
            start_time=datetime.now(),
        )
        summary.add_page_failure(error_message)
        return summary

    def test_connection(self) -> bool:
        """Test connection to Open-WebUI.

        Returns:
            True if connection is successful, False otherwise
        """
        return self.open_webui_client.test_connection()

    def get_export_statistics(self) -> dict[str, Any]:
        """Get export statistics and configuration.

        Returns:
            Dictionary with export statistics
        """
        return {
            "attachment_filter": self.attachment_filter.get_filter_summary(),
            "batch_upload_enabled": self.use_batch_upload,
            "metadata_enrichment_enabled": True,
        }
