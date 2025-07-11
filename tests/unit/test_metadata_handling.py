"""Unit tests for metadata handling functionality."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher


@pytest.fixture
def mock_client():
    """Create a mock client for MetadataEnricher."""
    client = MagicMock()
    client.compile_metadata.return_value = {
        "id": "1",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "space": {"key": "TEST", "name": "Test Space"},
        "ancestors": [{"id": "1", "title": "Parent Page"}],
        "attachments": [{"id": "1", "title": "Test Attachment"}],
    }
    return client


@pytest.fixture
def enricher(mock_client):
    """Create a MetadataEnricher instance with a mock client."""
    return MetadataEnricher(mock_client)


def test_validate_metadata_valid(enricher):
    """Test that validate_metadata accepts valid metadata."""
    metadata = {"id": "1", "title": "Test Page", "type": "page", "status": "current"}
    # Should not raise any exception
    enricher.validate_metadata(metadata)


def test_validate_metadata_missing_required_field(enricher):
    """Test that validate_metadata rejects metadata missing required fields."""
    metadata = {"id": "1", "title": "Test Page", "status": "current"}
    with pytest.raises(ValueError):
        enricher.validate_metadata(metadata)


def test_validate_metadata_invalid_type(enricher):
    """Test that validate_metadata rejects metadata with invalid type."""
    metadata = "not a dictionary"
    with pytest.raises(ValueError):
        enricher.validate_metadata(metadata)


def test_add_space_details_to_frontmatter(enricher):
    """Test adding space details to frontmatter."""
    metadata = {"space": {"key": "TEST", "name": "Test Space"}}

    # Test YAML format
    yaml_result = enricher.add_space_details_to_frontmatter(metadata, "yaml")
    assert "space:" in yaml_result
    assert "key: TEST" in yaml_result
    assert "name: Test Space" in yaml_result

    # Test JSON format
    json_result = enricher.add_space_details_to_frontmatter(metadata, "json")
    assert '"space"' in json_result
    assert '"key": "TEST"' in json_result
    assert '"name": "Test Space"' in json_result


def test_add_ancestors_to_frontmatter(enricher):
    """Test adding ancestors to frontmatter."""
    metadata = {"ancestors": [{"id": "1", "title": "Parent Page"}]}

    # Test YAML format
    yaml_result = enricher.add_ancestors_to_frontmatter(metadata, "yaml")
    assert "ancestors:" in yaml_result
    assert "- id: '1'" in yaml_result
    assert "title: Parent Page" in yaml_result

    # Test JSON format
    json_result = enricher.add_ancestors_to_frontmatter(metadata, "json")
    assert '"ancestors"' in json_result
    assert '"id": "1"' in json_result
    assert '"title": "Parent Page"' in json_result


def test_add_attachments_to_frontmatter(enricher):
    """Test adding attachments to frontmatter."""
    metadata = {"attachments": [{"id": "1", "title": "Test Attachment"}]}

    # Test YAML format
    yaml_result = enricher.add_attachments_to_frontmatter(metadata, "yaml")
    assert "attachments:" in yaml_result
    assert "- id: '1'" in yaml_result
    assert "title: Test Attachment" in yaml_result

    # Test JSON format
    json_result = enricher.add_attachments_to_frontmatter(metadata, "json")
    assert '"attachments"' in json_result
    assert '"id": "1"' in json_result
    assert '"title": "Test Attachment"' in json_result


def test_compile_metadata_to_frontmatter(enricher):
    """Test compiling metadata to frontmatter."""
    metadata = {
        "id": "1",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "space": {"key": "TEST", "name": "Test Space"},
        "ancestors": [{"id": "1", "title": "Parent Page"}],
        "attachments": [{"id": "1", "title": "Test Attachment"}],
    }

    # Test YAML format
    yaml_result = enricher.compile_metadata_to_frontmatter(metadata, "yaml")
    assert "confluence_metadata:" in yaml_result
    assert "title: Test Page" in yaml_result
    assert "space:" in yaml_result
    assert "ancestors:" in yaml_result
    assert "attachments:" in yaml_result

    # Test JSON format
    json_result = enricher.compile_metadata_to_frontmatter(metadata, "json")
    assert '"confluence_metadata"' in json_result
    assert '"title": "Test Page"' in json_result
    assert '"space"' in json_result
    assert '"ancestors"' in json_result
    assert '"attachments"' in json_result


def test_enrich_page_content(enricher):
    """Test enriching page content with metadata."""
    content = "# Test Page\n\nThis is a test page."
    metadata = {
        "id": "1",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "space": {"key": "TEST", "name": "Test Space"},
        "ancestors": [{"id": "1", "title": "Parent Page"}],
        "attachments": [{"id": "1", "title": "Test Attachment"}],
    }

    # Test YAML format
    enriched_content = enricher.enrich_page_content(content, metadata, "yaml")
    assert enriched_content.startswith("---")
    assert "confluence_metadata:" in enriched_content
    assert "title: Test Page" in enriched_content
    assert "space:" in enriched_content
    assert "ancestors:" in enriched_content
    assert "attachments:" in enriched_content
    assert "---" in enriched_content
    assert "# Test Page" in enriched_content
    assert "This is a test page." in enriched_content

    # Test JSON format
    enriched_content_json = enricher.enrich_page_content(content, metadata, "json")
    assert enriched_content_json.startswith("```json")
    assert '"confluence_metadata"' in enriched_content_json
    assert '"title": "Test Page"' in enriched_content_json
    assert '"space"' in enriched_content_json
    assert '"ancestors"' in enriched_content_json
    assert '"attachments"' in enriched_content_json
    assert "```" in enriched_content_json
    assert "# Test Page" in enriched_content_json
    assert "This is a test page." in enriched_content_json


def test_enrich_attachment_content(enricher):
    """Test enriching attachment content with metadata."""
    content = "This is a test attachment."
    metadata = {"id": "1", "title": "Test Attachment", "type": "attachment", "status": "current"}

    # Test YAML format
    enriched_content = enricher.enrich_attachment_content(content, metadata, "yaml")
    assert enriched_content.startswith("---")
    assert "confluence_metadata:" in enriched_content
    assert "title: Test Attachment" in enriched_content
    assert "type: attachment" in enriched_content
    assert "---" in enriched_content
    assert "This is a test attachment." in enriched_content

    # Test JSON format
    enriched_content_json = enricher.enrich_attachment_content(content, metadata, "json")
    assert enriched_content_json.startswith("```json")
    assert '"confluence_metadata"' in enriched_content_json
    assert '"title": "Test Attachment"' in enriched_content_json
    assert '"type": "attachment"' in enriched_content_json
    assert "```" in enriched_content_json
    assert "This is a test attachment." in enriched_content_json
