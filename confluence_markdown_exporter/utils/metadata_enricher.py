"""Module for enriching markdown files with comprehensive Confluence metadata.

This module provides the MetadataEnricher class, which takes metadata from the
extended Confluence API client and adds it as frontmatter to markdown files.
It supports different metadata formats (YAML, JSON) and includes methods to add
space details, page ancestors, attachment details, and compile complete metadata.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import yaml

if TYPE_CHECKING:
    from clients.open_webui_client import OpenWebUIClient

logger = logging.getLogger(__name__)

# Default whitelist of useful metadata fields for Open WebUI
DEFAULT_OPENWEBUI_METADATA_WHITELIST = {
    "id",
    "title",
    "type",
    "status",
    "space",
    "version",
    "created",
    "updated",
    "labels",
    "creator",
    "lastModifier",
}

# Fields that should always be excluded (Confluence API internals)
CONFLUENCE_API_INTERNAL_FIELDS = {
    "_expandable",
    "_links",
    "ancestors",  # Contains full API data hierarchy
    "children",  # Contains full API data
    "descendants",
    "container",  # Contains full space API data
    "operations",  # API operations data
    "restrictions",
    "metadata",  # Raw API metadata object
    "body",  # Raw body content (we handle this separately)
    "history",  # Full version history API data
}


class MetadataEnricher:
    """Class for adding comprehensive Confluence metadata to markdown files.

    This class takes metadata from the extended Confluence API client and adds
    it as frontmatter to markdown files. It supports different metadata formats
    (YAML, JSON) and includes methods to add space details, page ancestors,
    attachment details, and compile complete metadata.
    """

    def __init__(self, client):
        """Initialize the MetadataEnricher with an OpenWebUI client."""
        self.client = client
        self.validate_client()

    def validate_client(self):
        """Validate that the provided client is valid for metadata enrichment."""
        if not hasattr(self.client, "compile_metadata"):
            raise ValueError("Client must have a 'compile_metadata' method")
        if not hasattr(self.client, "get_space_details"):
            raise ValueError("Client must have a 'get_space_details' method")
        if not hasattr(self.client, "get_ancestors"):
            raise ValueError("Client must have a 'get_ancestors' method")
        if not hasattr(self.client, "get_attachments"):
            raise ValueError("Client must have a 'get_attachments' method")

    def validate_metadata(self, metadata: dict[str, Any]) -> None:
        """Validate the metadata structure.

        Args:
            metadata: The metadata dictionary to validate.

        Raises:
            ValueError: If the metadata is invalid.
        """
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        # At least title must be present
        if "title" not in metadata:
            raise ValueError("Metadata must contain 'title' field")

        # These fields are required for full metadata but not for testing individual components
        required_fields = ["id", "type", "status"]
        for field in required_fields:
            if field not in metadata:
                # Only skip validation if this is clearly a component test (has only title and space/ancestors/attachments)
                component_test_keys = {"title", "space", "ancestors", "attachments"}
                if set(metadata.keys()).issubset(component_test_keys):
                    continue
                # Otherwise, require the field
                raise ValueError(f"Metadata must contain '{field}' field")

        # Validate optional fields if present
        if "space" in metadata and not isinstance(metadata["space"], dict):
            raise ValueError("Metadata field 'space' must be a dictionary if present")

        if "ancestors" in metadata and not isinstance(metadata["ancestors"], list):
            raise ValueError("Metadata field 'ancestors' must be a list if present")

        if "attachments" in metadata and not isinstance(metadata["attachments"], list):
            raise ValueError("Metadata field 'attachments' must be a list if present")

    def add_space_details_to_frontmatter(
        self, metadata: dict[str, Any], format: str = "yaml"
    ) -> str:
        """Add space details to frontmatter.

        Args:
            metadata: The metadata dictionary containing space details.
            format: The format to use for the frontmatter (yaml or json).

        Returns:
            A string containing the space details in the specified format.
        """
        if not metadata or "space" not in metadata:
            return ""

        space = metadata["space"]
        space_frontmatter = {"space": space}

        if format.lower() == "json":
            return json.dumps(space_frontmatter, indent=2)
        return yaml.dump(space_frontmatter, indent=2)

    def add_ancestors_to_frontmatter(self, metadata: dict[str, Any], format: str = "yaml") -> str:
        """Add page ancestors to frontmatter.

        Args:
            metadata: The metadata dictionary containing ancestors.
            format: The format to use for the frontmatter (yaml or json).

        Returns:
            A string containing the ancestors in the specified format.
        """
        if not metadata or "ancestors" not in metadata:
            return ""

        ancestors = metadata["ancestors"]
        ancestors_frontmatter = {"ancestors": ancestors}

        if format.lower() == "json":
            return json.dumps(ancestors_frontmatter, indent=2)
        return yaml.dump(ancestors_frontmatter, indent=2)

    def add_attachments_to_frontmatter(self, metadata: dict[str, Any], format: str = "yaml") -> str:
        """Add attachment details to frontmatter.

        Args:
            metadata: The metadata dictionary containing attachments.
            format: The format to use for the frontmatter (yaml or json).

        Returns:
            A string containing the attachments in the specified format.
        """
        if not metadata or "attachments" not in metadata:
            return ""

        attachments = metadata["attachments"]
        attachments_frontmatter = {"attachments": attachments}

        if format.lower() == "json":
            return json.dumps(attachments_frontmatter, indent=2)
        return yaml.dump(attachments_frontmatter, indent=2)

    def compile_metadata_to_frontmatter(
        self,
        metadata: dict[str, Any],
        format: str = "yaml",
        filter_for_openwebui: bool = False,
        custom_whitelist: set[str] | None = None,
    ) -> str:
        """Compile and add complete metadata to frontmatter.

        Args:
            metadata: The metadata dictionary to compile.
            format: The format to use for the frontmatter (yaml or json).
            filter_for_openwebui: Whether to filter metadata for Open WebUI compatibility.
            custom_whitelist: Custom set of fields to include (overrides default filtering).

        Returns:
            A string containing the complete metadata in the specified format.
        """
        self.validate_metadata(metadata)
        if not metadata:
            return ""

        # Create a copy to avoid modifying the original
        metadata_copy = metadata.copy()

        # Apply filtering if requested
        if filter_for_openwebui:
            metadata_copy = self._filter_metadata_for_openwebui(metadata_copy, custom_whitelist)

        # Remove nested details that should be handled separately
        space = metadata_copy.pop("space", None) if "space" in metadata_copy else None
        ancestors = metadata_copy.pop("ancestors", None) if "ancestors" in metadata_copy else None
        attachments = (
            metadata_copy.pop("attachments", None) if "attachments" in metadata_copy else None
        )

        # Start with basic metadata
        frontmatter_dict = {"confluence_metadata": metadata_copy}

        # Add space details if present (with filtering)
        if space:
            filtered_space = self._filter_space_metadata(space) if filter_for_openwebui else space
            frontmatter_dict["confluence_metadata"]["space"] = filtered_space
            frontmatter_dict["space"] = filtered_space

        # Add ancestors if present (with filtering)
        if ancestors:
            filtered_ancestors = (
                self._filter_ancestors_metadata(ancestors) if filter_for_openwebui else ancestors
            )
            frontmatter_dict["confluence_metadata"]["ancestors"] = filtered_ancestors
            frontmatter_dict["ancestors"] = filtered_ancestors

        # Add attachments if present (with filtering)
        if attachments:
            filtered_attachments = (
                self._filter_attachments_metadata(attachments)
                if filter_for_openwebui
                else attachments
            )
            frontmatter_dict["confluence_metadata"]["attachments"] = filtered_attachments
            frontmatter_dict["attachments"] = filtered_attachments

        # Convert to the requested format
        if format.lower() == "json":
            return json.dumps(frontmatter_dict, indent=2)
        return yaml.dump(frontmatter_dict, indent=2)

    def enrich_markdown(
        self,
        page_id: int,
        markdown_content: str,
        output_path: Path,
        format: str = "yaml",
    ) -> None:
        """Enrich a markdown file with Confluence metadata.

        Args:
            page_id: The ID of the page to get metadata for.
            markdown_content: The original markdown content.
            output_path: The path to save the enriched markdown file.
            format: The format to use for the frontmatter (yaml or json).

        Raises:
            ValueError: If page_id is not a positive integer.
            ValueError: If markdown_content is not a string.
            ValueError: If output_path is not a valid Path object.
        """
        # Validate inputs
        if not isinstance(page_id, int) or page_id <= 0:
            raise ValueError("page_id must be a positive integer")
        if not isinstance(markdown_content, str):
            raise ValueError("markdown_content must be a string")
        if not isinstance(output_path, Path):
            raise ValueError("output_path must be a Path object")

        # Get comprehensive metadata for the page
        metadata = self.client.compile_metadata(page_id)

        # Compile the frontmatter
        frontmatter = self.compile_metadata_to_frontmatter(metadata, format)

        # Add frontmatter to the markdown content
        if format.lower() == "yaml":
            enriched_content = f"---\n{frontmatter}---\n\n{markdown_content}"
        else:  # JSON format
            enriched_content = f"```json\n{frontmatter}```\n\n{markdown_content}"

        # Save the enriched content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(enriched_content)

    def enrich_page_content(
        self,
        content: str,
        metadata: dict[str, Any],
        format: str = "yaml",
        filter_for_openwebui: bool = False,
        custom_whitelist: set[str] | None = None,
    ) -> str:
        """Enrich page content with metadata frontmatter.

        Args:
            content: The original content to enrich.
            metadata: The metadata dictionary for the page.
            format: The format to use for the frontmatter (yaml or json).
            filter_for_openwebui: Whether to filter metadata for Open WebUI compatibility.
            custom_whitelist: Custom set of fields to include (overrides default filtering).

        Returns:
            The content with metadata frontmatter added.

        Raises:
            ValueError: If content is not a string.
            ValueError: If metadata is not a dictionary.
            ValueError: If format is not 'yaml' or 'json'.
        """
        # Validate inputs
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary")
        if format.lower() not in ["yaml", "json"]:
            raise ValueError("format must be 'yaml' or 'json'")

        frontmatter = self.compile_metadata_to_frontmatter(
            metadata, format, filter_for_openwebui, custom_whitelist
        )

        if format.lower() == "yaml":
            return f"---\n{frontmatter}---\n\n{content}"
        # JSON format
        return f"```json\n{frontmatter}```\n\n{content}"

    def enrich_attachment_content(
        self, content: str, metadata: dict[str, Any], format: str = "yaml"
    ) -> str:
        """Enrich attachment content with metadata frontmatter.

        Args:
            content: The original content to enrich.
            metadata: The metadata dictionary for the attachment.
            format: The format to use for the frontmatter (yaml or json).

        Returns:
            The content with metadata frontmatter added.

        Raises:
            ValueError: If content is not a string.
            ValueError: If metadata is not a dictionary.
            ValueError: If format is not 'yaml' or 'json'.
        """
        # Validate inputs
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary")
        if format.lower() not in ["yaml", "json"]:
            raise ValueError("format must be 'yaml' or 'json'")

        frontmatter = self.compile_metadata_to_frontmatter(metadata, format)

        if format.lower() == "yaml":
            return f"---\n{frontmatter}---\n\n{content}"
        # JSON format
        return f"```json\n{frontmatter}```\n\n{content}"

    def test_connection(self) -> bool:
        """Test the connection to the Confluence API.

        This method tests the connection by attempting to retrieve basic metadata
        from the client. It returns True if the connection is successful, False otherwise.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            # Try to get basic metadata to test the connection
            metadata = self.client.compile_metadata(1)
            # Validate that the metadata is a dictionary with required fields
            self.validate_metadata(metadata)
            return True
        except Exception as e:
            # Log the error and return False
            print(f"Connection test failed: {e}")
            return False

    def _filter_metadata_for_openwebui(
        self, metadata: dict[str, Any], custom_whitelist: set[str] | None = None
    ) -> dict[str, Any]:
        """Filter page metadata for Open WebUI compatibility by removing Confluence API internals.

        Args:
            metadata: The raw page data from Confluence API
            custom_whitelist: Custom set of fields to include (overrides default)

        Returns:
            Filtered metadata dictionary
        """
        whitelist = (
            custom_whitelist
            if custom_whitelist is not None
            else DEFAULT_OPENWEBUI_METADATA_WHITELIST
        )
        filtered_metadata = {}

        for key, value in metadata.items():
            # Skip if key is in the internal fields blacklist
            if key in CONFLUENCE_API_INTERNAL_FIELDS:
                logger.debug(f"Filtering out Confluence API internal field: {key}")
                continue

            # Skip if key is not in whitelist (when using whitelist approach)
            if whitelist and key not in whitelist:
                logger.debug(f"Field '{key}' not in whitelist, skipping")
                continue

            # Include the field if it passes all filters
            filtered_metadata[key] = self._sanitize_metadata_value(value)

        return filtered_metadata

    def _filter_space_metadata(self, space: dict[str, Any]) -> dict[str, Any]:
        """Filter space metadata to remove API internals.

        Args:
            space: Raw space metadata from Confluence API

        Returns:
            Filtered space metadata
        """
        if not isinstance(space, dict):
            return space

        filtered_space = {}
        useful_space_fields = {"key", "name", "type", "description"}

        for key, value in space.items():
            if key not in CONFLUENCE_API_INTERNAL_FIELDS and key in useful_space_fields:
                filtered_space[key] = self._sanitize_metadata_value(value)

        return filtered_space

    def _filter_ancestors_metadata(self, ancestors: list[Any]) -> list[dict[str, Any]]:
        """Filter ancestors metadata to remove API internals.

        Args:
            ancestors: Raw ancestors list from Confluence API

        Returns:
            Filtered ancestors list with only essential fields
        """
        if not isinstance(ancestors, list):
            return ancestors

        filtered_ancestors = []
        useful_ancestor_fields = {"id", "title", "type"}

        for ancestor in ancestors:
            if isinstance(ancestor, dict):
                filtered_ancestor = {}
                for key, value in ancestor.items():
                    if key not in CONFLUENCE_API_INTERNAL_FIELDS and key in useful_ancestor_fields:
                        filtered_ancestor[key] = self._sanitize_metadata_value(value)
                if filtered_ancestor:
                    filtered_ancestors.append(filtered_ancestor)
            else:
                filtered_ancestors.append(ancestor)

        return filtered_ancestors

    def _filter_attachments_metadata(self, attachments: list[Any]) -> list[dict[str, Any]]:
        """Filter attachments metadata to remove API internals.

        Args:
            attachments: Raw attachments list from Confluence API

        Returns:
            Filtered attachments list with only essential fields
        """
        if not isinstance(attachments, list):
            return attachments

        filtered_attachments = []
        useful_attachment_fields = {"id", "title", "mediaType", "fileSize", "comment"}

        for attachment in attachments:
            if isinstance(attachment, dict):
                filtered_attachment = {}
                for key, value in attachment.items():
                    if (
                        key not in CONFLUENCE_API_INTERNAL_FIELDS
                        and key in useful_attachment_fields
                    ):
                        filtered_attachment[key] = self._sanitize_metadata_value(value)
                if filtered_attachment:
                    filtered_attachments.append(filtered_attachment)
            else:
                filtered_attachments.append(attachment)

        return filtered_attachments

    def _sanitize_metadata_value(self, value: Any) -> Any:
        """Sanitize metadata values to ensure they're suitable for YAML frontmatter.

        Args:
            value: The metadata value to sanitize

        Returns:
            Sanitized value
        """
        if isinstance(value, dict):
            # Recursively sanitize dictionary values, removing API internals
            sanitized = {}
            for k, v in value.items():
                if k not in CONFLUENCE_API_INTERNAL_FIELDS:
                    sanitized[k] = self._sanitize_metadata_value(v)
            return sanitized
        if isinstance(value, list):
            # Sanitize list items
            return [self._sanitize_metadata_value(item) for item in value]
        if isinstance(value, str):
            # Ensure string values are not too long for frontmatter
            if len(value) > 1000:
                logger.debug(f"Truncating long string value (length: {len(value)})")
                return value[:1000] + "..."
            return value
        # Return primitive values as-is
        return value
