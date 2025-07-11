#!/usr/bin/env python3
"""Test script to specifically verify that 'extensions' and 'macroRenderedOutput' fields are filtered out."""

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


def test_extensions_and_macrorenderedoutput_filtering():
    """Test that 'extensions' and 'macroRenderedOutput' fields are specifically filtered out."""
    print("Testing filtering of 'extensions' and 'macroRenderedOutput' fields...")
    print(
        f"Current DEFAULT_OPENWEBUI_METADATA_WHITELIST: {sorted(DEFAULT_OPENWEBUI_METADATA_WHITELIST)}"
    )

    # Create enricher with mock client
    client = MockClient()
    enricher = MetadataEnricher(client)

    # Test metadata with the specific problematic fields mentioned in the task
    test_metadata = {
        # Essential fields that should be kept
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
        # Problematic fields that should be filtered out according to the task
        "extensions": {
            "position": 2534,
            "fileSize": 1234,
            "mediaType": "text/plain",
            "fileId": "att123456",
        },
        "macroRenderedOutput": {},
        # Other fields that should also be filtered out
        "_expandable": {"children": "/rest/api/content/123456/child"},
        "_links": {"webui": "/pages/viewpage.action?pageId=123456"},
        "body": {"storage": {"value": "<p>Content</p>"}},
        "operations": [{"operation": "read"}],
        "metadata": {"labels": {"results": []}},
    }

    print(f"\nOriginal metadata keys: {sorted(test_metadata.keys())}")

    # Check if the problematic fields are in the whitelist
    extensions_in_whitelist = "extensions" in DEFAULT_OPENWEBUI_METADATA_WHITELIST
    macro_in_whitelist = "macroRenderedOutput" in DEFAULT_OPENWEBUI_METADATA_WHITELIST

    print(f"\n'extensions' in whitelist: {extensions_in_whitelist}")
    print(f"'macroRenderedOutput' in whitelist: {macro_in_whitelist}")

    if extensions_in_whitelist or macro_in_whitelist:
        print("❌ PROBLEM: Unwanted fields are in the whitelist!")
        if extensions_in_whitelist:
            print("  - 'extensions' should be removed from whitelist")
        if macro_in_whitelist:
            print("  - 'macroRenderedOutput' should be removed from whitelist")
    else:
        print("✅ GOOD: Neither 'extensions' nor 'macroRenderedOutput' are in the whitelist")

    # Test filtering
    filtered_metadata = enricher._filter_metadata_for_openwebui(test_metadata)
    print(f"\nFiltered metadata keys: {sorted(filtered_metadata.keys())}")

    # Check if unwanted fields are present in filtered result
    extensions_in_filtered = "extensions" in filtered_metadata
    macro_in_filtered = "macroRenderedOutput" in filtered_metadata

    print(f"\n'extensions' in filtered result: {extensions_in_filtered}")
    print(f"'macroRenderedOutput' in filtered result: {macro_in_filtered}")

    if extensions_in_filtered or macro_in_filtered:
        print("❌ FILTERING FAILED: Unwanted fields are still present!")
        if extensions_in_filtered:
            print(f"  - 'extensions' value: {filtered_metadata['extensions']}")
        if macro_in_filtered:
            print(f"  - 'macroRenderedOutput' value: {filtered_metadata['macroRenderedOutput']}")
    else:
        print("✅ FILTERING SUCCESS: Both 'extensions' and 'macroRenderedOutput' were filtered out")

    # Test with frontmatter generation
    frontmatter = enricher.compile_metadata_to_frontmatter(
        test_metadata, format="json", filter_for_openwebui=True
    )

    parsed_frontmatter = json.loads(frontmatter)
    confluence_metadata = parsed_frontmatter.get("confluence_metadata", {})

    extensions_in_frontmatter = "extensions" in confluence_metadata
    macro_in_frontmatter = "macroRenderedOutput" in confluence_metadata

    print(f"\n'extensions' in frontmatter: {extensions_in_frontmatter}")
    print(f"'macroRenderedOutput' in frontmatter: {macro_in_frontmatter}")

    if extensions_in_frontmatter or macro_in_frontmatter:
        print("❌ FRONTMATTER PROBLEM: Unwanted fields in final output!")
    else:
        print("✅ FRONTMATTER SUCCESS: No unwanted fields in final output")

    # Show what fields were kept
    print(f"\nFinal filtered fields in frontmatter: {sorted(confluence_metadata.keys())}")

    # Verify all essential fields are present
    essential_fields = {
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
    missing_essential = essential_fields - set(confluence_metadata.keys())

    if missing_essential:
        print(f"⚠️  WARNING: Missing essential fields: {missing_essential}")
    else:
        print("✅ All essential fields are present")

    return not (
        extensions_in_filtered
        or macro_in_filtered
        or extensions_in_frontmatter
        or macro_in_frontmatter
    )


if __name__ == "__main__":
    success = test_extensions_and_macrorenderedoutput_filtering()
    if success:
        print("\n🎉 ALL TESTS PASSED: Filtering is working correctly!")
    else:
        print("\n💥 TESTS FAILED: Filtering needs to be fixed!")
