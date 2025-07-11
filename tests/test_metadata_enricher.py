"""Tests for the MetadataEnricher class."""

import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pytest_mock import MockerFixture

if TYPE_CHECKING:
    from confluence_markdown_exporter.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher


@pytest.fixture
def mock_client(mocker: MockerFixture) -> MockerFixture:
    """Mock the OpenWebUI client."""
    return mocker.patch("confluence_markdown_exporter.open_webui_client.OpenWebUIClient")


@pytest.fixture
def enricher(mock_client: MockerFixture, mocker: MockerFixture) -> MetadataEnricher:
    """Create a MetadataEnricher instance with a mocked client."""
    mock_instance = mocker.MagicMock()
    mock_instance.compile_metadata.return_value = {
        "title": "Test Page",
        "space": {"key": "TEST", "name": "Test Space"},
        "ancestors": [{"id": 1, "title": "Parent Page"}],
        "attachments": [{"id": "abc", "title": "Test Attachment"}],
    }
    return MetadataEnricher(mock_instance)


def test_add_space_details_to_frontmatter(enricher: MetadataEnricher) -> None:
    """Test adding space details to frontmatter."""
    metadata = {"space": {"key": "TEST", "name": "Test Space"}}
    yaml_result = enricher.add_space_details_to_frontmatter(metadata, "yaml")
    json_result = enricher.add_space_details_to_frontmatter(metadata, "json")

    assert "space:" in yaml_result
    assert "key: TEST" in yaml_result
    assert '"space"' in json_result
    assert '"key": "TEST"' in json_result


def test_add_ancestors_to_frontmatter(enricher: MetadataEnricher) -> None:
    """Test adding ancestors to frontmatter."""
    metadata = {"ancestors": [{"id": 1, "title": "Parent Page"}]}
    yaml_result = enricher.add_ancestors_to_frontmatter(metadata, "yaml")
    json_result = enricher.add_ancestors_to_frontmatter(metadata, "json")

    assert "ancestors:" in yaml_result
    assert "- id: 1" in yaml_result
    assert '"ancestors"' in json_result
    assert '"id": 1' in json_result


def test_add_attachments_to_frontmatter(enricher: MetadataEnricher) -> None:
    """Test adding attachments to frontmatter."""
    metadata = {"attachments": [{"id": "abc", "title": "Test Attachment"}]}
    yaml_result = enricher.add_attachments_to_frontmatter(metadata, "yaml")
    json_result = enricher.add_attachments_to_frontmatter(metadata, "json")

    assert "attachments:" in yaml_result
    assert "- id: abc" in yaml_result
    assert '"attachments"' in json_result
    assert '"id": "abc"' in json_result


def test_compile_metadata_to_frontmatter(enricher: MetadataEnricher) -> None:
    """Test compiling metadata to frontmatter."""
    metadata = {
        "title": "Test Page",
        "space": {"key": "TEST"},
        "ancestors": [{"id": 1, "title": "Parent Page"}],
        "attachments": [{"id": "abc", "title": "Test Attachment"}],
    }
    yaml_result = enricher.compile_metadata_to_frontmatter(metadata, "yaml")
    json_result = enricher.compile_metadata_to_frontmatter(metadata, "json")

    assert "confluence_metadata:" in yaml_result
    assert "title: Test Page" in yaml_result
    assert "space:" in yaml_result
    assert "ancestors:" in yaml_result
    assert "attachments:" in yaml_result

    parsed_json = json.loads(json_result)
    assert parsed_json["confluence_metadata"]["title"] == "Test Page"
    assert parsed_json["space"]["key"] == "TEST"
    assert len(parsed_json["ancestors"]) == 1
    assert len(parsed_json["attachments"]) == 1


def test_enrich_markdown(enricher: MetadataEnricher, mocker: MockerFixture) -> None:
    """Test enriching markdown content with metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_page.md"

        # Original markdown content
        markdown_content = "# Test Page\n\nThis is a test page."

        # Mock mkdir and open
        mocker.patch("pathlib.Path.mkdir", return_value=None)
        mocker.patch(
            "builtins.open",
            mocker.mock_open(),
        )

        # Enrich with metadata
        enricher.enrich_markdown(
            page_id=123, markdown_content=markdown_content, output_path=output_path, format="yaml"
        )

        # Verify mkdir was called with parents=True and exist_ok=True
        Path.mkdir.assert_called_with(parents=True, exist_ok=True)

        # Verify open was called with write mode and utf-8 encoding
        open_mock = mocker.mock_open()
        mocker.patch("builtins.open", open_mock)
        enricher.enrich_markdown(
            page_id=123, markdown_content=markdown_content, output_path=output_path, format="yaml"
        )
        open_mock.assert_called_with(output_path, "w", encoding="utf-8")

        # Verify the content written to the file
        handle = open_mock()
        written_content = handle.write.call_args[0][0]
        assert written_content.startswith("---")
        assert "confluence_metadata:" in written_content
        assert "title: Test Page" in written_content
        assert "space:" in written_content
        assert "ancestors:" in written_content
        assert "attachments:" in written_content
        assert "---" in written_content
        assert "# Test Page" in written_content
        assert "This is a test page." in written_content
