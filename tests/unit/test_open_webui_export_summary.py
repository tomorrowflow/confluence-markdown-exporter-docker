"""Unit tests for the OpenWebUIExportSummary class."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from confluence_markdown_exporter.utils.open_webui_export_summary import OpenWebUIExportSummary


def test_export_summary_initialization():
    """Test that the export summary initializes correctly with valid parameters."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=4,
        successful_attachments=2,
        failed_pages=1,
        failed_attachments=1,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    assert summary.knowledge_base_name == "Test KB"
    assert summary.knowledge_base_id == "1"
    assert summary.total_pages == 5
    assert summary.total_attachments == 3
    assert summary.successful_pages == 4
    assert summary.successful_attachments == 2
    assert summary.failed_pages == 1
    assert summary.failed_attachments == 1
    assert summary.skipped_pages == 0
    assert summary.skipped_attachments == 0
    assert summary.start_time is not None
    assert summary.end_time is None


def test_export_summary_add_success():
    """Test that adding success updates the counts correctly."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=0,
        successful_attachments=0,
        failed_pages=0,
        failed_attachments=0,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    # Add page success
    summary.add_page_success()
    assert summary.successful_pages == 1
    assert summary.failed_pages == 0

    # Add attachment success
    summary.add_attachment_success()
    assert summary.successful_attachments == 1
    assert summary.failed_attachments == 0


def test_export_summary_add_failure():
    """Test that adding failure updates the counts correctly."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=0,
        successful_attachments=0,
        failed_pages=0,
        failed_attachments=0,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    # Add page failure
    summary.add_page_failure("Test failure")
    assert summary.successful_pages == 0
    assert summary.failed_pages == 1
    assert "Page: Test failure" in summary.errors

    # Add attachment failure
    summary.add_attachment_failure("Test failure")
    assert summary.successful_attachments == 0
    assert summary.failed_attachments == 1
    assert "Attachment: Test failure" in summary.errors


def test_export_summary_add_skipped():
    """Test that adding skipped items updates the counts correctly."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=0,
        successful_attachments=0,
        failed_pages=0,
        failed_attachments=0,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    # Add page skipped
    summary.add_page_skipped("Test page")
    assert summary.skipped_pages == 1
    assert summary.failed_pages == 0
    assert "Page: Test page" in summary.skipped_items

    # Add attachment skipped
    summary.add_attachment_skipped("Test attachment")
    assert summary.skipped_attachments == 1
    assert summary.failed_attachments == 0
    assert "Attachment: Test attachment" in summary.skipped_items


def test_export_summary_get_summary_text():
    """Test that get_summary_text returns the expected summary text."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=4,
        successful_attachments=2,
        failed_pages=1,
        failed_attachments=1,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    summary_text = summary.get_summary_text()
    assert "Export to Test KB completed" in summary_text
    assert "Total files: 8" in summary_text
    assert "Successful: 6" in summary_text
    assert "Failed: 2" in summary_text
    assert "Skipped (duplicate): 0" in summary_text
    assert "Pages: 5 total, 4 successful, 1 failed, 0 skipped" in summary_text
    assert "Attachments: 3 total, 2 successful, 1 failed, 0 skipped" in summary_text


def test_export_summary_get_summary_text_with_skipped():
    """Test that get_summary_text includes duplicate content note when items are skipped."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=3,
        successful_attachments=2,
        failed_pages=1,
        failed_attachments=0,
        skipped_pages=1,
        skipped_attachments=1,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    summary_text = summary.get_summary_text()
    assert "Skipped (duplicate): 2" in summary_text
    assert "Note: Skipped items indicate duplicate content" in summary_text
    assert "This is expected behavior and not an error condition" in summary_text


def test_export_summary_add_filtered():
    """Test that adding filtered attachments updates the counts correctly."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=0,
        successful_attachments=0,
        failed_pages=0,
        failed_attachments=0,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=0,
        start_time=datetime.now(),
    )

    # Add filtered attachment
    summary.add_attachment_filtered("test.svg", "extension filter")
    assert summary.filtered_attachments == 1
    assert summary.failed_attachments == 0
    assert "Attachment: test.svg (filtered: extension filter)" in summary.filtered_items


def test_export_summary_get_summary_text_with_filtered():
    """Test that get_summary_text includes filtered attachments note when items are filtered."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=5,
        successful_pages=4,
        successful_attachments=2,
        failed_pages=1,
        failed_attachments=1,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=2,
        start_time=datetime.now(),
    )

    summary_text = summary.get_summary_text()
    assert "Total files: 10" in summary_text
    assert "Successful: 6" in summary_text
    assert "Failed: 2" in summary_text
    assert "Filtered: 2" in summary_text
    assert (
        "Note: Filtered items were intentionally excluded by extension or size filters"
        in summary_text
    )
    assert "This is expected behavior and not an error condition" in summary_text


def test_export_summary_success_rate_excludes_filtered():
    """Test that success rate calculation excludes filtered items."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=10,
        successful_pages=4,
        successful_attachments=3,
        failed_pages=1,
        failed_attachments=2,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=5,  # 5 filtered attachments should not count as failures
        start_time=datetime.now(),
    )

    summary_text = summary.get_summary_text()

    # Total processed items should be 15 (5 pages + 10 attachments)
    # But filtered items (5) should be excluded from success rate calculation
    # So success rate should be based on 10 processed items (5 pages + 5 non-filtered attachments)
    # Successful: 7 (4 pages + 3 attachments)
    # Failed: 3 (1 page + 2 attachments)
    # Success rate: 7/10 = 70%

    assert "Total files: 15" in summary_text
    assert "Successful: 7" in summary_text
    assert "Failed: 3" in summary_text
    assert "Filtered: 5" in summary_text

    # The success rate should be calculated excluding filtered items
    # 7 successful out of 10 processed (excluding 5 filtered) = 70%
    assert "Successful: 7 (70.0%)" in summary_text


def test_export_summary_initialization_with_filtered():
    """Test that the export summary initializes correctly with filtered attachments."""
    summary = OpenWebUIExportSummary(
        knowledge_base_name="Test KB",
        knowledge_base_id="1",
        total_pages=5,
        total_attachments=3,
        successful_pages=4,
        successful_attachments=2,
        failed_pages=1,
        failed_attachments=1,
        skipped_pages=0,
        skipped_attachments=0,
        filtered_attachments=2,
        start_time=datetime.now(),
    )

    assert summary.filtered_attachments == 2
    assert summary.filtered_items == []
