#!/usr/bin/env python3
"""Test script to verify metadata filtering behavior."""

import json

from confluence_markdown_exporter.utils.metadata_enricher import (
    DEFAULT_OPENWEBUI_METADATA_WHITELIST,
)
from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher


class MockClient:
    """Mock client for testing."""

    def compile_metadata(self, page_id):
        return {}

    def get_space_details(self, space_key):
        return {}

    def get_ancestors(self, page_id):
        return []

    def get_attachments(self, page_id):
        return []


def test_metadata_filtering():
    """Test that unwanted fields are filtered out."""
    print("Testing metadata filtering...")
    print(f"Current DEFAULT_OPENWEBUI_METADATA_WHITELIST: {DEFAULT_OPENWEBUI_METADATA_WHITELIST}")

    # Create enricher with mock client
    client = MockClient()
    enricher = MetadataEnricher(client)

    # Test metadata with unwanted fields
    test_metadata = {
        "id": "123456",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "space": {"key": "TEST", "name": "Test Space"},
        "version": {"number": 1},
        "created": "2023-01-01T00:00:00.000Z",
        "updated": "2023-01-02T00:00:00.000Z",
        "labels": [{"name": "test"}],
        "creator": {"displayName": "Test User"},
        "lastModifier": {"displayName": "Test User"},
        # These should be filtered out:
        "extensions": {"position": 2534, "fileSize": 1234},
        "macroRenderedOutput": {},
        "_expandable": {"children": "/rest/api/content/123456/child"},
        "_links": {"webui": "/pages/viewpage.action?pageId=123456"},
        "body": {"storage": {"value": "<p>Content</p>"}},
    }

    print(f"\nOriginal metadata keys: {list(test_metadata.keys())}")

    # Test filtering
    filtered_metadata = enricher._filter_metadata_for_openwebui(test_metadata)
    print(f"Filtered metadata keys: {list(filtered_metadata.keys())}")

    # Check if unwanted fields are present
    unwanted_fields = ["extensions", "macroRenderedOutput", "_expandable", "_links", "body"]
    found_unwanted = []
    for field in unwanted_fields:
        if field in filtered_metadata:
            found_unwanted.append(field)

    if found_unwanted:
        print(f"\n❌ PROBLEM: Found unwanted fields in filtered metadata: {found_unwanted}")
        print("These fields should be filtered out!")
    else:
        print("\n✅ SUCCESS: All unwanted fields were filtered out")

    # Test with filter_for_openwebui=True in compile_metadata_to_frontmatter
    frontmatter = enricher.compile_metadata_to_frontmatter(
        test_metadata, format="json", filter_for_openwebui=True
    )

    parsed_frontmatter = json.loads(frontmatter)
    confluence_metadata = parsed_frontmatter.get("confluence_metadata", {})

    print(f"\nFrontmatter confluence_metadata keys: {list(confluence_metadata.keys())}")

    found_unwanted_in_frontmatter = []
    for field in unwanted_fields:
        if field in confluence_metadata:
            found_unwanted_in_frontmatter.append(field)

    if found_unwanted_in_frontmatter:
        print(f"❌ PROBLEM: Found unwanted fields in frontmatter: {found_unwanted_in_frontmatter}")
    else:
        print("✅ SUCCESS: No unwanted fields in frontmatter")

    # Show the actual filtered metadata
    print("\nActual filtered metadata:")
    for key, value in filtered_metadata.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_metadata_filtering()
