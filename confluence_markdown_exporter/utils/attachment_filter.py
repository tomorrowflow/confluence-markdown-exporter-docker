"""Module for filtering attachments based on file extensions."""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

logger = logging.getLogger(__name__)


class AttachmentFilter:
    """Filters attachments based on file extensions."""

    def __init__(self, filter_config: dict[str, Any] | None = None):
        """Initialize the attachment filter.

        Args:
            filter_config: Optional configuration dictionary with allowed and blocked extensions
        """
        self.allowed_extensions = (
            filter_config.get("allowed_extensions", []) if filter_config else []
        )
        self.blocked_extensions = (
            filter_config.get("blocked_extensions", []) if filter_config else []
        )
        self.default_allowed_extensions = [".txt", ".md", ".json", ".yaml", ".yml", ".csv"]
        self.default_blocked_extensions = [".exe", ".bat", ".sh", ".dll", ".so", ".dmg", ".iso"]

    def filter_attachments(
        self, attachments: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Filter attachments based on allowed and blocked extensions.

        Args:
            attachments: List of attachment dictionaries
        Returns:
            Dictionary with "allowed" and "blocked" lists of attachments
        """
        allowed = []
        blocked = []

        for attachment in attachments:
            extension = self._get_extension(attachment)
            if not extension:
                allowed.append(attachment)
                continue

            # Check if extension is explicitly blocked
            if extension.lower() in [e.lower() for e in self.blocked_extensions]:
                blocked.append(attachment)
                continue

            # Check if extension is explicitly allowed
            if extension.lower() in [e.lower() for e in self.allowed_extensions]:
                allowed.append(attachment)
                continue

            # If no explicit rule, use default behavior
            if extension.lower() in [e.lower() for e in self.default_allowed_extensions]:
                allowed.append(attachment)
            elif extension.lower() in [e.lower() for e in self.default_blocked_extensions]:
                blocked.append(attachment)
            else:
                # Default to allowing unknown extensions
                allowed.append(attachment)

        return {"allowed": allowed, "blocked": blocked}

    def _get_extension(self, attachment: dict[str, Any]) -> str | None:
        """Get the file extension from an attachment.

        Args:
            attachment: Attachment dictionary
        Returns:
            File extension (e.g., ".txt") or None if not found
        """
        # Try to get extension from title
        title = attachment.get("title", "")
        if "." in title:
            return "." + title.split(".")[-1].lower()

        # Try to get extension from filename
        filename = attachment.get("filename", "")
        if "." in filename:
            return "." + filename.split(".")[-1].lower()

        # Try to get extension from content_type
        content_type = attachment.get("content_type", "")
        if "/" in content_type:
            parts = content_type.split("/")
            if len(parts) > 1:
                return "." + parts[-1].lower()

        return None

    def is_text_file(self, filename: str) -> bool:
        """Check if a file is a text file based on its extension.

        Args:
            filename: Name of the file
        Returns:
            True if the file is a text file, False otherwise
        """
        text_extensions = [
            ".txt",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".csv",
            ".html",
            ".htm",
            ".xml",
            ".py",
            ".js",
            ".css",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".php",
            ".rb",
            ".pl",
            ".sh",
            ".sql",
        ]
        extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
        return extension in text_extensions

    def get_content_type(self, filename: str) -> str:
        """Get the content type for a file based on its extension.

        Args:
            filename: Name of the file
        Returns:
            Content type string (e.g., "text/plain", "image/png")
        """
        # Common content types mapping
        content_types = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
            ".csv": "text/csv",
            ".html": "text/html",
            ".htm": "text/html",
            ".xml": "application/xml",
            ".py": "text/x-python",
            ".js": "application/javascript",
            ".css": "text/css",
            ".java": "text/x-java-source",
            ".c": "text/x-csrc",
            ".cpp": "text/x-c++src",
            ".h": "text/x-c++hdr",
            ".php": "application/x-php",
            ".rb": "application/x-ruby",
            ".pl": "application/x-perl",
            ".sh": "application/x-sh",
            ".sql": "application/sql",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".zip": "application/zip",
            ".rar": "application/x-rar-compressed",
        }
        extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
        return content_types.get(extension, "application/octet-stream")

    def get_filter_summary(self):
        """Get a summary of the current filter configuration.

        Returns:
            dict: A dictionary with filter configuration details.
        """
        return {
            "allowed_extensions": self.allowed_extensions,
            "blocked_extensions": self.blocked_extensions,
            "default_allowed_extensions": self.default_allowed_extensions,
            "default_blocked_extensions": self.default_blocked_extensions,
        }
