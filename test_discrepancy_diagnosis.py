#!/usr/bin/env python3
"""Diagnostic test to investigate the discrepancy between refined whitelist configuration
and user's observation of unwanted metadata fields.
"""

import logging
from pathlib import Path

from confluence_markdown_exporter.utils.metadata_enricher import CONFLUENCE_API_INTERNAL_FIELDS
from confluence_markdown_exporter.utils.metadata_enricher import (
    DEFAULT_OPENWEBUI_METADATA_WHITELIST,
)
from confluence_markdown_exporter.utils.metadata_enricher import MetadataEnricher

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_metadata_filtering():
    """Test the metadata filtering to understand the discrepancy."""
    print("=== DISCREPANCY DIAGNOSIS ===")
    print()

    # 1. Check current whitelist configuration
    print("1. Current DEFAULT_OPENWEBUI_METADATA_WHITELIST:")
    for field in sorted(DEFAULT_OPENWEBUI_METADATA_WHITELIST):
        print(f"   - {field}")
    print()

    # 2. Check if problematic fields are in whitelist
    problematic_fields = ["extensions", "macroRenderedOutput"]
    print("2. Checking if problematic fields are in whitelist:")
    for field in problematic_fields:
        in_whitelist = field in DEFAULT_OPENWEBUI_METADATA_WHITELIST
        print(f"   - {field}: {'YES' if in_whitelist else 'NO'}")
    print()

    # 3. Check if problematic fields are in internal fields blacklist
    print("3. Checking if problematic fields are in CONFLUENCE_API_INTERNAL_FIELDS:")
    for field in problematic_fields:
        in_blacklist = field in CONFLUENCE_API_INTERNAL_FIELDS
        print(f"   - {field}: {'YES' if in_blacklist else 'NO'}")
    print()

    # 4. Simulate the user's reported metadata
    print("4. Simulating user's reported metadata:")
    user_reported_metadata = {
        "extensions": {"position": 2534},
        "id": "131095",
        "macroRenderedOutput": {},
        "status": "current",
        "title": "Searchable Title #2",
        "type": "page",
    }

    print("   Original metadata:")
    for key, value in user_reported_metadata.items():
        print(f"     {key}: {value}")
    print()

    # 5. Test filtering with filter_for_openwebui=True
    print("5. Testing filtering with filter_for_openwebui=True:")

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

    enricher = MetadataEnricher(MockClient())

    # Test the filtering
    filtered_metadata = enricher._filter_metadata_for_openwebui(user_reported_metadata)

    print("   Filtered metadata:")
    for key, value in filtered_metadata.items():
        print(f"     {key}: {value}")
    print()

    # 6. Check what would be in the final frontmatter
    print("6. Testing complete frontmatter generation:")
    try:
        frontmatter = enricher.compile_metadata_to_frontmatter(
            user_reported_metadata, format="yaml", filter_for_openwebui=True
        )
        print("   Generated frontmatter:")
        print("   " + "\n   ".join(frontmatter.split("\n")))
    except Exception as e:
        print(f"   Error generating frontmatter: {e}")
    print()

    # 7. Check the actual exported file
    print("7. Checking actual exported file:")
    export_file = Path("exports/My first space/My first space/Searchable Title #2.md")
    if export_file.exists():
        with open(export_file, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"   File exists: {export_file}")
        print(f"   File size: {len(content)} characters")
        print("   First 500 characters:")
        print("   " + "\n   ".join(content[:500].split("\n")))

        # Check if it has YAML frontmatter
        if content.startswith("---"):
            print("   ✓ File has YAML frontmatter")
            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_content = parts[1]
                print("   Frontmatter content:")
                print("   " + "\n   ".join(frontmatter_content.split("\n")))
        else:
            print("   ✗ File has NO frontmatter")
    else:
        print(f"   File does not exist: {export_file}")
    print()

    # 8. Diagnosis summary
    print("8. DIAGNOSIS SUMMARY:")
    print("   Based on the analysis:")

    extensions_filtered = "extensions" not in filtered_metadata
    macro_filtered = "macroRenderedOutput" not in filtered_metadata

    if extensions_filtered and macro_filtered:
        print("   ✓ Filtering is working correctly - problematic fields are removed")
        print("   ✓ The whitelist does NOT contain 'extensions' or 'macroRenderedOutput'")

        if export_file.exists() and not content.startswith("---"):
            print("   ⚠️  ISSUE IDENTIFIED: The exported file has NO metadata at all!")
            print("   ⚠️  This suggests the file was exported WITHOUT OpenWebUI filtering")
            print("   ⚠️  OR the file was exported before the filtering was implemented")
        else:
            print("   ✓ The exported file appears to be correctly filtered")
    else:
        print("   ✗ Filtering is NOT working - problematic fields are still present")
        if not extensions_filtered:
            print("   ✗ 'extensions' field was not filtered out")
        if not macro_filtered:
            print("   ✗ 'macroRenderedOutput' field was not filtered out")


if __name__ == "__main__":
    test_metadata_filtering()
