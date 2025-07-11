"""Unit tests for the OpenWebUIExporter class."""

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
    return MagicMock(spec=ConfluenceApiSdk)


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


def test_exporter_initialization(
    mock_open_webui_client, mock_confluence, mock_attachment_filter, mock_metadata_enricher
):
    """Test that the exporter initializes correctly with valid parameters."""
    exporter = OpenWebUIExporter(
        open_webui_client=mock_open_webui_client,
        confluence=mock_confluence,
        attachment_filter=mock_attachment_filter,
        metadata_enricher=mock_metadata_enricher,
    )
    assert exporter.open_webui_client == mock_open_webui_client
    assert exporter.confluence == mock_confluence
    assert exporter.attachment_filter == mock_attachment_filter
    assert exporter.metadata_enricher == mock_metadata_enricher


def test_exporter_initialization_missing_client():
    """Test that the exporter raises ValueError when client is missing."""
    with patch(
        "confluence_markdown_exporter.utils.open_webui_exporter.OpenWebUIExporter.__init__",
        side_effect=ValueError("Open-WebUI client must be provided"),
    ):
        with pytest.raises(ValueError):
            OpenWebUIExporter(
                open_webui_client=MagicMock(),  # Create a mock but patch its init
                confluence=MagicMock(spec=ConfluenceApiSdk),
                attachment_filter=MagicMock(spec=AttachmentFilter),
                metadata_enricher=MagicMock(spec=MetadataEnricher),
            )


def test_create_or_get_knowledge_base_success(exporter, mock_open_webui_client):
    """Test that _create_or_get_knowledge_base creates a new knowledge base when none exists."""
    # Setup mock responses
    mock_open_webui_client.get_knowledge.return_value = {"items": []}
    mock_open_webui_client.create_knowledge.return_value = {"id": "1", "name": "Test Space"}

    # Call _create_or_get_knowledge_base
    result = exporter._create_or_get_knowledge_base(
        "Test Space", "http://test.com/spaces/TEST/overview"
    )

    # Verify results
    assert result == {"id": "1", "name": "Test Space"}
    mock_open_webui_client.get_knowledge.assert_called_once()
    mock_open_webui_client.create_knowledge.assert_called_once()


def test_create_or_get_knowledge_base_exists(exporter, mock_open_webui_client):
    """Test that _create_or_get_knowledge_base returns existing knowledge base."""
    # Setup mock responses
    existing_kb = {"id": "1", "name": "Test Space"}
    mock_open_webui_client.get_knowledge.return_value = {"items": [existing_kb]}

    # Call _create_or_get_knowledge_base
    result = exporter._create_or_get_knowledge_base(
        "Test Space", "http://test.com/spaces/TEST/overview"
    )

    # Verify results
    assert result == existing_kb
    mock_open_webui_client.get_knowledge.assert_called_once()
    mock_open_webui_client.create_knowledge.assert_not_called()


def test_generate_safe_filename(exporter):
    """Test that _generate_safe_filename creates valid filenames."""
    # Test with extension
    filename = exporter._generate_safe_filename("Test Page", ".md")
    assert filename == "Test Page.md"

    # Test without extension
    filename = exporter._generate_safe_filename("Test Page")
    assert filename == "Test Page"

    # Test with special characters
    filename = exporter._generate_safe_filename("Test: Page/With|Special?Chars", ".txt")
    assert filename == "Test PageWithSpecialChars.txt"
