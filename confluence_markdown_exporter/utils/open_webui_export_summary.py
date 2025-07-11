"""Module for Open-WebUI export summary tracking."""

from datetime import datetime
from typing import List
from typing import Optional


class OpenWebUIExportSummary:
    """Tracks the progress and results of an Open-WebUI export operation.

    Attributes:
        knowledge_base_name (str): Name of the knowledge base being exported to
        knowledge_base_id (str): ID of the knowledge base
        total_pages (int): Total number of pages to export
        total_attachments (int): Total number of attachments to export
        successful_pages (int): Number of successfully exported pages
        successful_attachments (int): Number of successfully exported attachments
        failed_pages (int): Number of pages that failed to export
        failed_attachments (int): Number of attachments that failed to export
        skipped_pages (int): Number of pages skipped due to duplicate content
        skipped_attachments (int): Number of attachments skipped due to duplicate content
        filtered_attachments (int): Number of attachments filtered out by extension/size filters
        start_time (datetime): When the export operation started
        end_time (Optional[datetime]): When the export operation ended, or None if still in progress
    """

    def __init__(
        self,
        knowledge_base_name: str,
        knowledge_base_id: str,
        total_pages: int,
        total_attachments: int,
        successful_pages: int = 0,
        successful_attachments: int = 0,
        failed_pages: int = 0,
        failed_attachments: int = 0,
        skipped_pages: int = 0,
        skipped_attachments: int = 0,
        filtered_attachments: int = 0,
        start_time: datetime | None = None,
    ):
        """Initialize the export summary.

        Args:
            knowledge_base_name: Name of the knowledge base
            knowledge_base_id: ID of the knowledge base
            total_pages: Total number of pages to export
            total_attachments: Total number of attachments to export
            successful_pages: Number of successfully exported pages (default: 0)
            successful_attachments: Number of successfully exported attachments (default: 0)
            failed_pages: Number of pages that failed to export (default: 0)
            failed_attachments: Number of attachments that failed to export (default: 0)
            skipped_pages: Number of pages skipped due to duplicate content (default: 0)
            skipped_attachments: Number of attachments skipped due to duplicate content (default: 0)
            filtered_attachments: Number of attachments filtered out by extension/size filters (default: 0)
            start_time: When the export operation started (default: now)
        """
        self.knowledge_base_name = knowledge_base_name
        self.knowledge_base_id = knowledge_base_id
        self.total_pages = total_pages
        self.total_attachments = total_attachments
        self.successful_pages = successful_pages
        self.successful_attachments = successful_attachments
        self.failed_pages = failed_pages
        self.failed_attachments = failed_attachments
        self.skipped_pages = skipped_pages
        self.skipped_attachments = skipped_attachments
        self.filtered_attachments = filtered_attachments
        self.start_time = start_time or datetime.now()
        self.end_time = None
        self.errors = []
        self.skipped_items = []
        self.filtered_items = []

    @property
    def total_files(self) -> int:
        """Get the total number of files (pages + attachments)."""
        return self.total_pages + self.total_attachments

    @property
    def total_successful(self) -> int:
        """Get the total number of successfully exported files."""
        return self.successful_pages + self.successful_attachments

    @property
    def total_failed(self) -> int:
        """Get the total number of failed exports."""
        return self.failed_pages + self.failed_attachments

    @property
    def total_skipped(self) -> int:
        """Get the total number of skipped exports (duplicate content)."""
        return self.skipped_pages + self.skipped_attachments

    def add_page_success(self) -> None:
        """Record a successfully exported page."""
        self.successful_pages += 1

    def add_attachment_success(self) -> None:
        """Record a successfully exported attachment."""
        self.successful_attachments += 1

    def add_page_failure(self, error: str | None = None) -> None:
        """Record a failed page export.

        Args:
            error: Optional error message
        """
        self.failed_pages += 1
        if error:
            self.errors.append(f"Page: {error}")

    def add_attachment_failure(self, error: str | None = None) -> None:
        """Record a failed attachment export.

        Args:
            error: Optional error message
        """
        self.failed_attachments += 1
        if error:
            self.errors.append(f"Attachment: {error}")

    def add_page_skipped(self, item_name: str | None = None) -> None:
        """Record a page skipped due to duplicate content.

        Args:
            item_name: Optional name of the skipped item
        """
        self.skipped_pages += 1
        if item_name:
            self.skipped_items.append(f"Page: {item_name}")

    def add_attachment_skipped(self, item_name: str | None = None) -> None:
        """Record an attachment skipped due to duplicate content.

        Args:
            item_name: Optional name of the skipped item
        """
        self.skipped_attachments += 1
        if item_name:
            self.skipped_items.append(f"Attachment: {item_name}")

    def add_attachment_filtered(
        self, item_name: str | None = None, reason: str = "extension filter"
    ) -> None:
        """Record an attachment filtered out by extension or size filters.

        Args:
            item_name: Optional name of the filtered item
            reason: Reason for filtering (default: "extension filter")
        """
        self.filtered_attachments += 1
        if item_name:
            self.filtered_items.append(f"Attachment: {item_name} (filtered: {reason})")

    def get_summary_text(self) -> str:
        """Get a text summary of the export operation.

        Returns:
            A string summarizing the export results
        """
        if not self.start_time:
            return "Export summary not available"

        duration = self.get_duration()

        # Calculate success rate based on items that were actually processed (excluding filtered items)
        processed_files = self.total_files - self.filtered_attachments
        success_rate = self.total_successful / processed_files * 100 if processed_files > 0 else 0

        summary_lines = [
            f"Export to {self.knowledge_base_name} completed in {duration}",
            f"Total files: {self.total_files}, Processed: {processed_files}, Successful: {self.total_successful} ({success_rate:.1f}%), "
            f"Failed: {self.total_failed}, Skipped (duplicate): {self.total_skipped}, Filtered: {self.filtered_attachments}",
            f"Pages: {self.total_pages} total, {self.successful_pages} successful, {self.failed_pages} failed, "
            f"{self.skipped_pages} skipped (duplicate content)",
            f"Attachments: {self.total_attachments} total, {self.successful_attachments} successful, "
            f"{self.failed_attachments} failed, {self.skipped_attachments} skipped (duplicate), {self.filtered_attachments} filtered",
        ]

        # Add note about duplicate content handling if any items were skipped
        if self.total_skipped > 0:
            summary_lines.append("")
            summary_lines.append(
                "Note: Skipped items indicate duplicate content that already exists in the knowledge base."
            )
            summary_lines.append("This is expected behavior and not an error condition.")

        # Add note about filtered items if any were filtered
        if self.filtered_attachments > 0:
            summary_lines.append("")
            summary_lines.append(
                "Note: Filtered items were intentionally excluded by extension or size filters."
            )
            summary_lines.append("This is expected behavior and not an error condition.")

        return "\n".join(summary_lines)

    def get_duration(self) -> str:
        """Get the duration of the export operation.

        Returns:
            A string representing the duration (e.g., "1 hour, 30 minutes")
        """
        if not self.end_time or not self.start_time:
            return "Unknown duration"

        delta = self.end_time - self.start_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        duration_parts = []
        if hours > 0:
            duration_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            duration_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

        return ", ".join(duration_parts) if duration_parts else "Less than a minute"
