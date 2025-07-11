"""Unit tests for the AttachmentFilter class."""

import pytest

from confluence_markdown_exporter.utils.attachment_filter import AttachmentFilter


def test_attachment_filter_initialization():
    """Test that the attachment filter initializes correctly."""
    filter_config = {"allowed_extensions": [".txt", ".md"], "blocked_extensions": [".exe", ".bat"]}
    filter = AttachmentFilter(filter_config)

    assert filter.allowed_extensions == [".txt", ".md"]
    assert filter.blocked_extensions == [".exe", ".bat"]
    assert filter.default_allowed_extensions == [".txt", ".md", ".json", ".yaml", ".yml", ".csv"]
    assert filter.default_blocked_extensions == [
        ".exe",
        ".bat",
        ".sh",
        ".dll",
        ".so",
        ".dmg",
        ".iso",
    ]


def test_filter_attachments():
    """Test that filter_attachments correctly categorizes attachments."""
    filter_config = {"allowed_extensions": [".txt", ".md"], "blocked_extensions": [".exe", ".bat"]}
    filter = AttachmentFilter(filter_config)

    attachments = [
        {"filename": "document.txt", "title": "document.txt"},
        {"filename": "script.bat", "title": "script.bat"},
        {"filename": "readme.md", "title": "readme.md"},
        {"filename": "install.exe", "title": "install.exe"},
        {"filename": "data.json", "title": "data.json"},
    ]

    result = filter.filter_attachments(attachments)

    assert len(result["allowed"]) == 3  # Only .txt and .md allowed
    assert len(result["blocked"]) == 2  # .bat and .exe blocked
    assert (
        result["blocked"][0]["filename"] == "script.bat"
        or result["blocked"][1]["filename"] == "script.bat"
    )
    assert (
        result["blocked"][0]["filename"] == "install.exe"
        or result["blocked"][1]["filename"] == "install.exe"
    )


def test_filter_attachments_with_default_extensions():
    """Test that filter_attachments uses default extensions correctly."""
    filter = AttachmentFilter()  # No config, use defaults

    attachments = [
        {"filename": "document.txt", "title": "document.txt"},
        {"filename": "script.sh", "title": "script.sh"},
        {"filename": "readme.md", "title": "readme.md"},
        {"filename": "install.exe", "title": "install.exe"},
        {"filename": "data.json", "title": "data.json"},
    ]

    result = filter.filter_attachments(attachments)

    # Check that .sh is blocked by default
    assert len(result["allowed"]) == 3  # All text files except .sh
    assert len(result["blocked"]) == 2  # .sh and .exe blocked
    assert any(a["filename"] == "script.sh" for a in result["blocked"])
    assert any(a["filename"] == "install.exe" for a in result["blocked"])


def test_filter_attachments_with_no_extension():
    """Test that filter_attachments handles files with no extension."""
    filter = AttachmentFilter()

    attachments = [
        {"filename": "noextension", "title": "noextension"},
    ]

    result = filter.filter_attachments(attachments)

    assert len(result["allowed"]) == 1
    assert len(result["blocked"]) == 0


def test_get_extension_from_filename():
    """Test that _get_extension correctly extracts extension from filename."""
    filter = AttachmentFilter()

    # Test with various attachment formats
    assert filter._get_extension({"filename": "document.txt"}) == ".txt"
    assert filter._get_extension({"filename": "archive.ZIP"}) == ".zip"
    assert filter._get_extension({"filename": "no_extension"}) is None

    # Test with title when filename missing
    assert filter._get_extension({"title": "readme.MD"}) == ".md"

    # Test with content_type
    assert filter._get_extension({"content_type": "image/png"}) == ".png"


def test_is_text_file():
    """Test that is_text_file correctly identifies text files."""
    filter = AttachmentFilter()

    # Test with known text extensions
    assert filter.is_text_file("document.txt") is True
    assert filter.is_text_file("readme.md") is True
    assert filter.is_text_file("data.json") is True
    assert filter.is_text_file("script.py") is True

    # Test with binary extensions
    assert filter.is_text_file("image.png") is False
    assert filter.is_text_file("archive.zip") is False
    assert filter.is_text_file("install.exe") is False

    # Test with unknown extension
    assert filter.is_text_file("unknown.file") is False


def test_get_content_type():
    """Test that get_content_type returns the correct content type."""
    filter = AttachmentFilter()

    assert filter.get_content_type("document.txt") == "text/plain"
    assert filter.get_content_type("readme.md") == "text/markdown"
    assert filter.get_content_type("data.json") == "application/json"
    assert filter.get_content_type("script.py") == "text/x-python"
    assert filter.get_content_type("image.png") == "image/png"
    assert filter.get_content_type("archive.zip") == "application/zip"
    assert filter.get_content_type("unknown.file") == "application/octet-stream"


def test_get_filter_summary():
    """Test that get_filter_summary returns the expected summary."""
    filter_config = {"allowed_extensions": [".txt", ".md"], "blocked_extensions": [".exe", ".bat"]}
    filter = AttachmentFilter(filter_config)

    summary = filter.get_filter_summary()

    assert summary["allowed_extensions"] == [".txt", ".md"]
    assert summary["blocked_extensions"] == [".exe", ".bat"]
    assert summary["default_allowed_extensions"] == [
        ".txt",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".csv",
    ]
    assert summary["default_blocked_extensions"] == [
        ".exe",
        ".bat",
        ".sh",
        ".dll",
        ".so",
        ".dmg",
        ".iso",
    ]
