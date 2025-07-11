#!/usr/bin/env python3
"""Test script to verify metadata filtering is working correctly.
This will test the current implementation and show before/after metadata.
"""

import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_metadata_filtering():
    """Test the metadata filtering functionality."""
    # Import the MetadataEnricher
    from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher

    # Create a mock client for testing
    class MockClient:
        def compile_metadata(self, page_id):
            return {}

        def get_space_details(self, space_key):
            return {}

        def get_ancestors(self, page_id):
            return []

        def get_attachments(self, page_id):
            return []

    # Create enricher instance
    enricher = MetadataEnricher(MockClient())

    # Create test metadata with problematic fields (simulating raw Confluence API response)
    test_metadata = {
        "id": "123456",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "_expandable": {
            "children": "/rest/api/content/123456/child",
            "descendants": "/rest/api/content/123456/descendant",
        },
        "_links": {
            "webui": "/pages/viewpage.action?pageId=123456",
            "edit": "/pages/resumedraft.action?draftId=123456",
            "tinyui": "/x/ABCD",
            "collection": "/rest/api/content",
            "base": "https://example.atlassian.net/wiki",
            "context": "/wiki",
            "self": "https://example.atlassian.net/wiki/rest/api/content/123456",
        },
        "operations": [
            {"operation": "read", "targetType": "page"},
            {"operation": "update", "targetType": "page"},
        ],
        "ancestors": [
            {
                "id": "111111",
                "title": "Parent Page",
                "type": "page",
                "_expandable": {"children": "/rest/api/content/111111/child"},
                "_links": {"webui": "/pages/viewpage.action?pageId=111111"},
            }
        ],
        "space": {
            "key": "TEST",
            "name": "Test Space",
            "type": "global",
            "_expandable": {
                "settings": "/rest/api/space/TEST/settings",
                "metadata": "/rest/api/space/TEST/metadata",
            },
            "_links": {
                "webui": "/spaces/TEST",
                "self": "https://example.atlassian.net/wiki/rest/api/space/TEST",
            },
        },
        "version": {
            "by": {
                "type": "known",
                "username": "testuser",
                "userKey": "testuser",
                "displayName": "Test User",
            },
            "when": "2024-01-01T12:00:00.000Z",
            "number": 1,
            "minorEdit": False,
        },
        "body": {"view": {"value": "<p>Test content</p>", "representation": "view"}},
        "metadata": {"labels": {"results": [], "start": 0, "limit": 200, "size": 0}},
    }

    print("=== ORIGINAL METADATA (with API internals) ===")
    print(json.dumps(test_metadata, indent=2))
    print(f"\nOriginal metadata size: {len(json.dumps(test_metadata))} characters")
    print(f"Contains _expandable: {'_expandable' in test_metadata}")
    print(f"Contains _links: {'_links' in test_metadata}")
    print(f"Contains operations: {'operations' in test_metadata}")

    # Test WITHOUT filtering (regular export)
    print("\n=== WITHOUT FILTERING (Regular Export) ===")
    unfiltered_frontmatter = enricher.compile_metadata_to_frontmatter(
        test_metadata, format="yaml", filter_for_openwebui=False
    )
    print(unfiltered_frontmatter)
    print(f"Unfiltered frontmatter size: {len(unfiltered_frontmatter)} characters")

    # Test WITH filtering (Open WebUI export)
    print("\n=== WITH FILTERING (Open WebUI Export) ===")
    filtered_frontmatter = enricher.compile_metadata_to_frontmatter(
        test_metadata, format="yaml", filter_for_openwebui=True
    )
    print(filtered_frontmatter)
    print(f"Filtered frontmatter size: {len(filtered_frontmatter)} characters")

    # Test enriching content
    print("\n=== TESTING CONTENT ENRICHMENT ===")
    test_content = "# Test Page\n\nThis is test content."

    # Without filtering
    unfiltered_enriched = enricher.enrich_page_content(
        test_content, test_metadata, format="yaml", filter_for_openwebui=False
    )

    # With filtering
    filtered_enriched = enricher.enrich_page_content(
        test_content, test_metadata, format="yaml", filter_for_openwebui=True
    )

    print("WITHOUT filtering - Content length:", len(unfiltered_enriched))
    print("WITH filtering - Content length:", len(filtered_enriched))

    # Show the difference
    print("\n=== COMPARISON ===")
    print(f"Size reduction: {len(unfiltered_frontmatter) - len(filtered_frontmatter)} characters")
    print(
        f"Percentage reduction: {((len(unfiltered_frontmatter) - len(filtered_frontmatter)) / len(unfiltered_frontmatter) * 100):.1f}%"
    )

    # Check what fields were removed
    import yaml

    unfiltered_data = yaml.safe_load(unfiltered_frontmatter)
    filtered_data = yaml.safe_load(filtered_frontmatter)

    unfiltered_fields = set()
    filtered_fields = set()

    def extract_fields(data, prefix=""):
        fields = set()
        if isinstance(data, dict):
            for key, value in data.items():
                field_name = f"{prefix}.{key}" if prefix else key
                fields.add(field_name)
                fields.update(extract_fields(value, field_name))
        return fields

    unfiltered_fields = extract_fields(unfiltered_data)
    filtered_fields = extract_fields(filtered_data)

    removed_fields = unfiltered_fields - filtered_fields
    print(f"\nRemoved fields: {sorted(removed_fields)}")
    print(f"Kept fields: {sorted(filtered_fields)}")


if __name__ == "__main__":
    test_metadata_filtering()
