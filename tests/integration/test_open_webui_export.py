"""Integration tests for Open-WebUI export operations."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from atlassian import Confluence as ConfluenceApiSdk

from clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.utils.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher
from confluence_markdown_exporter.utils.open_webui_exporter import OpenWebUIExporter


@pytest.fixture
def mock_open_webui_client():
    """Create a mock OpenWebUIClient."""
    client = MagicMock(spec=OpenWebUIClient)
    client.test_connection.return_value = True
    return client


@pytest.fixture
def mock_confluence():
    """Create a mock Confluence client."""
    mock = MagicMock(spec=ConfluenceApiSdk)
    mock.url = "https://confluence.example.com"
    return mock


@pytest.fixture
def mock_attachment_filter():
    """Create a mock AttachmentFilter."""
    filter = MagicMock(spec=AttachmentFilter)
    filter.filter_attachments.return_value = {"allowed": [], "blocked": []}
    return filter


@pytest.fixture
def mock_metadata_enricher():
    """Create a mock MetadataEnricher."""
    return MagicMock(spec=MetadataEnricher)


@pytest.fixture
def exporter(
    mock_open_webui_client, mock_confluence, mock_attachment_filter, mock_metadata_enricher
):
    """Create an OpenWebUIExporter with mocked dependencies."""
    return OpenWebUIExporter(
        open_webui_client=mock_open_webui_client,
        confluence=mock_confluence,
        attachment_filter=mock_attachment_filter,
        metadata_enricher=mock_metadata_enricher,
    )


def test_export_space_success(
    exporter, mock_open_webui_client, mock_confluence, mock_attachment_filter
):
    """Test that export_space handles successful export."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses
        mock_confluence.get_space.return_value = {"name": "Test Space"}
        mock_open_webui_client.get_knowledge.return_value = {"items": []}
        mock_open_webui_client.create_knowledge.return_value = {"id": "1", "name": "Test Space"}
        # Ensure the mock doesn't return duplicate content response
        mock_open_webui_client.add_file_to_knowledge.return_value = {"id": "file1"}
        mock_open_webui_client.is_duplicate_content_error.return_value = False

        # Mock _read_page_content to return dummy content
        with patch.object(exporter, "_read_page_content", return_value="# Test Page"):
            # Test data
            space_key = "TEST"
            output_path = temp_dir
            pages = [{"id": "1", "title": "Test Page"}]
            attachments = []

            # Call export_space
            summary = exporter.export_space(space_key, output_path, pages, attachments)

            # Verify results
            assert summary.knowledge_base_name == "Test Space"
            assert summary.knowledge_base_id == "1"
            assert summary.total_pages == 1
            assert summary.total_attachments == 0
            assert summary.successful_pages == 1
            assert summary.successful_attachments == 0
            assert summary.failed_pages == 0
            assert summary.failed_attachments == 0
            assert summary.skipped_pages == 0
            assert summary.skipped_attachments == 0


def test_export_space_failure_no_space_details(exporter, mock_confluence):
    """Test that export_space handles failure to get space details."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses
        mock_confluence.get_space.return_value = None

        # Test data
        space_key = "TEST"
        output_path = temp_dir
        pages = [{"id": "1", "title": "Test Page"}]
        attachments = []

        # Call export_space
        summary = exporter.export_space(space_key, output_path, pages, attachments)

        # Verify results
        assert summary.knowledge_base_name == space_key
        assert summary.knowledge_base_id == ""
        assert summary.total_pages == 1
        assert summary.total_attachments == 0
        assert summary.successful_pages == 0
        assert summary.successful_attachments == 0
        assert summary.failed_pages == 2
        assert summary.failed_attachments == 0
        assert "Could not retrieve space details" in summary.errors[0]


def test_export_space_failure_create_knowledge_base(
    exporter, mock_open_webui_client, mock_confluence
):
    """Test that export_space handles failure to create knowledge base."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses
        mock_confluence.get_space.return_value = {"name": "Test Space"}
        mock_open_webui_client.get_knowledge.return_value = {"items": []}
        mock_open_webui_client.create_knowledge.return_value = None

        # Mock _read_page_content to return dummy content
        with patch.object(exporter, "_read_page_content", return_value="# Test Page"):
            # Test data
            space_key = "TEST"
            output_path = temp_dir
            pages = [{"id": "1", "title": "Test Page"}]
            attachments = []

            # Call export_space
            summary = exporter.export_space(space_key, output_path, pages, attachments)

            # Verify results
            assert summary.knowledge_base_name == "Test Space"
            assert summary.knowledge_base_id == ""
            assert summary.total_pages == 1
            assert summary.total_attachments == 0
            assert summary.successful_pages == 0
            assert summary.successful_attachments == 0
            assert summary.failed_pages == 1
            assert summary.failed_attachments == 0
            assert "Failed to create knowledge base" in summary.errors[0]


def test_export_page_success(exporter, mock_open_webui_client):
    """Test that _export_page handles successful page export."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses
        exporter.knowledge_base_name = "Test KB"
        exporter.knowledge_base_id = "kb1"  # Set the knowledge base ID
        # Ensure the mock doesn't return duplicate content response
        mock_open_webui_client.add_file_to_knowledge.return_value = {"id": "file1"}
        mock_open_webui_client.is_duplicate_content_error.return_value = False

        # Test data
        page = {"id": "1", "title": "Test Page"}
        output_path = temp_dir

        # Call _export_page
        with patch.object(exporter, "_read_page_content", return_value="# Test Page"):
            with patch.object(
                exporter.metadata_enricher,
                "enrich_page_content",
                return_value="# Enriched Test Page",
            ):
                file_id = exporter._export_page(page, output_path, "TEST", 1, 1)

        # Verify results
        assert file_id == "file1"
        mock_open_webui_client.add_file_to_knowledge.assert_called_once()


def test_export_page_failure(exporter):
    """Test that _export_page handles failures."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test data
        page = {"id": "1", "title": "Test Page"}
        output_path = temp_dir

        # Call _export_page with exception
        with patch.object(exporter, "_read_page_content", side_effect=Exception("Read error")):
            file_id = exporter._export_page(page, output_path, "TEST", 1, 1)

        # Verify results
        assert file_id is None


def test_export_attachment_success(exporter, mock_open_webui_client):
    """Test that _export_attachment handles successful attachment export."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses
        exporter.knowledge_base_name = "Test KB"
        exporter.knowledge_base_id = "kb1"  # Set the knowledge base ID
        # Ensure the mock doesn't return duplicate content response
        mock_open_webui_client.add_file_to_knowledge.return_value = {"id": "file1"}
        mock_open_webui_client.is_duplicate_content_error.return_value = False

        # Test data
        attachment = {"id": "1", "title": "Test Attachment"}
        output_path = temp_dir

        # Call _export_attachment
        with patch.object(exporter, "_read_attachment_content", return_value=b"Test content"):
            with patch.object(exporter.attachment_filter, "is_text_file", return_value=True):
                with patch.object(
                    exporter.metadata_enricher,
                    "enrich_attachment_content",
                    return_value="Enriched content",
                ):
                    file_id = exporter._export_attachment(attachment, output_path, "TEST", 1, 1)

        # Verify results
        assert file_id == "file1"
        mock_open_webui_client.add_file_to_knowledge.assert_called_once()


def test_export_attachment_failure(exporter):
    """Test that _export_attachment handles failures."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test data
        attachment = {"id": "1", "title": "Test Attachment"}
        output_path = temp_dir

        # Call _export_attachment with exception
        with patch.object(
            exporter, "_read_attachment_content", side_effect=Exception("Read error")
        ):
            file_id = exporter._export_attachment(attachment, output_path, "TEST", 1, 1)

        # Verify results
        assert file_id is None


def test_export_page_duplicate_content(exporter, mock_open_webui_client):
    """Test that _export_page handles duplicate content detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses for duplicate content
        exporter.knowledge_base_name = "Test KB"
        exporter.knowledge_base_id = "kb1"
        mock_open_webui_client.add_file_to_knowledge.return_value = {
            "duplicate_content": True,
            "message": "Duplicate content detected",
            "filename": "Test Page.md",
        }
        mock_open_webui_client.is_duplicate_content_error.return_value = True

        # Test data
        page = {"id": "1", "title": "Test Page"}
        output_path = temp_dir

        # Call _export_page
        with patch.object(exporter, "_read_page_content", return_value="# Test Page"):
            with patch.object(
                exporter.metadata_enricher,
                "enrich_page_content",
                return_value="# Enriched Test Page",
            ):
                file_id = exporter._export_page(page, output_path, "TEST", 1, 1)

        # Verify results
        assert file_id == "DUPLICATE_CONTENT"
        mock_open_webui_client.add_file_to_knowledge.assert_called_once()
        mock_open_webui_client.is_duplicate_content_error.assert_called_once()


def test_export_space_with_duplicate_content(
    exporter, mock_open_webui_client, mock_confluence, mock_attachment_filter
):
    """Test that export_space properly handles duplicate content in summary."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock responses
        mock_confluence.get_space.return_value = {"name": "Test Space"}
        mock_open_webui_client.get_knowledge.return_value = {"items": []}
        mock_open_webui_client.create_knowledge.return_value = {"id": "1", "name": "Test Space"}

        # Mock duplicate content response
        mock_open_webui_client.add_file_to_knowledge.return_value = {
            "duplicate_content": True,
            "message": "Duplicate content detected",
            "filename": "Test Page.md",
        }
        mock_open_webui_client.is_duplicate_content_error.return_value = True

        # Mock _read_page_content to return dummy content
        with patch.object(exporter, "_read_page_content", return_value="# Test Page"):
            # Test data
            space_key = "TEST"
            output_path = temp_dir
            pages = [{"id": "1", "title": "Test Page"}]
            attachments = []

            # Call export_space
            summary = exporter.export_space(space_key, output_path, pages, attachments)

            # Verify results - page should be skipped, not failed
            assert summary.knowledge_base_name == "Test Space"
            assert summary.knowledge_base_id == "1"
            assert summary.total_pages == 1
            assert summary.total_attachments == 0
            assert summary.successful_pages == 0
            assert summary.successful_attachments == 0
            assert summary.failed_pages == 0
            assert summary.failed_attachments == 0
            assert summary.skipped_pages == 1
            assert summary.skipped_attachments == 0
            assert "Test Page" in summary.skipped_items[0]
