"""Tests for Open-WebUI metadata functionality."""

import json
import os
from pathlib import Path

import pytest
import typer
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.main import app


@pytest.fixture
def mock_client(mocker: MockerFixture) -> MockerFixture:
    """Mock the OpenWebUI client."""
    return mocker.patch("clients.open_webui_client.OpenWebUIClient.from_auth_config")


@pytest.fixture
def runner() -> CliRunner:
    """Create a test runner."""
    return CliRunner()


def test_space_details_command(
    runner: CliRunner, mock_client: MockerFixture, mocker: MockerFixture
) -> None:
    """Test the space_details command."""
    # Setup mock response
    mock_instance = mocker.MagicMock(spec=OpenWebUIClient)
    mock_client.return_value = mock_instance
    mock_instance.get_space_details.return_value = {
        "key": "TEST",
        "name": "Test Space",
        "description": {"plain": {"value": "Test space description"}},
        "homepage": {"id": 123},
    }

    # Run command
    result = runner.invoke(app, ["space-details", "TEST"])

    # Assertions
    assert result.exit_code == 0
    assert "Space details for TEST:" in result.output
    assert "Name: Test Space" in result.output
    assert "Description: Test space description" in result.output
    assert "Homepage: 123" in result.output


def test_page_ancestors_command(
    runner: CliRunner, mock_client: MockerFixture, mocker: MockerFixture
) -> None:
    """Test the page_ancestors command."""
    # Setup mock response
    mock_instance = mocker.MagicMock(spec=OpenWebUIClient)
    mock_client.return_value = mock_instance
    mock_instance.get_page_ancestors.return_value = [
        {"id": 1, "title": "Parent Page"},
        {"id": 2, "title": "Grandparent Page"},
    ]

    # Run command
    result = runner.invoke(app, ["page-ancestors", "123"])

    # Assertions
    assert result.exit_code == 0
    assert "Ancestors for page 123:" in result.output
    assert "1. ID: 1, Title: Parent Page" in result.output
    assert "2. ID: 2, Title: Grandparent Page" in result.output


def test_attachment_details_command(
    runner: CliRunner, mock_client: MockerFixture, mocker: MockerFixture
) -> None:
    """Test the attachment_details command."""
    # Setup mock response
    mock_instance = mocker.MagicMock(spec=OpenWebUIClient)
    mock_client.return_value = mock_instance
    mock_instance.get_attachment_details.return_value = {
        "title": "Test File",
        "extensions": {"fileSize": 1234, "mediaType": "text/plain"},
        "version": {"number": 1},
    }

    # Run command
    result = runner.invoke(app, ["attachment-details", "abc123"])

    # Assertions
    assert result.exit_code == 0
    assert "Details for attachment abc123:" in result.output
    assert "Title: Test File" in result.output
    assert "File size: 1234 bytes" in result.output
    assert "Media type: text/plain" in result.output
    assert "Version: 1" in result.output


def test_page_metadata_command(
    runner: CliRunner, mock_client: MockerFixture, mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test the page_metadata command."""
    # Setup mock response
    mock_instance = mocker.MagicMock(spec=OpenWebUIClient)
    mock_client.return_value = mock_instance
    mock_instance.compile_metadata.return_value = {
        "title": "Test Page",
        "space": {"key": "TEST"},
        "ancestors": [{"id": 1, "title": "Parent"}],
        "attachments": [{"id": "abc"}],
    }

    # Run command with temporary directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(app, ["page-metadata", "123", str(output_dir)])

    # Assertions
    assert result.exit_code == 0
    assert "Metadata for page 123:" in result.output
    assert "Title: Test Page" in result.output
    assert "Space: TEST" in result.output
    assert "Ancestors: 1" in result.output
    assert "Attachments: 1" in result.output

    # Check if file was created
    metadata_file = output_dir / "page_123_metadata.json"
    assert metadata_file.exists()

    # Verify file content
    with open(metadata_file, "r") as f:
        data = json.load(f)
        assert data["title"] == "Test Page"
        assert data["space"]["key"] == "TEST"
        assert len(data["ancestors"]) == 1
        assert len(data["attachments"]) == 1
