#!/usr/bin/env python3
"""Test to verify which export path is being used and why there's no metadata."""

import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_export_path():
    """Test which export path is being used."""
    # Check if we can import the main module
    try:
        from confluence_markdown_exporter.main import main
        from confluence_markdown_exporter.utils.app_data_store import get_settings

        # Get current settings
        settings = get_settings()

        print("=== CURRENT EXPORT CONFIGURATION ===")
        print(f"Export to Open WebUI: {settings.export.export_to_open_webui}")
        print(f"Open WebUI URL: {settings.auth.open_webui.url}")
        print(
            f"Open WebUI API Key configured: {'Yes' if settings.auth.open_webui.api_key.get_secret_value() else 'No'}"
        )

        # Check if the exported files exist and their content
        export_file = Path("exports/My first space/My first space/Searchable Title #2.md")
        if export_file.exists():
            content = export_file.read_text()
            print("\n=== EXPORTED FILE ANALYSIS ===")
            print(f"File size: {len(content)} characters")
            print(f"Has YAML frontmatter: {'---' in content[:100]}")
            print(f"Has JSON frontmatter: {'```json' in content[:100]}")
            print(f"Starts with title: {content.strip().startswith('#')}")

            # Show first 200 characters
            print("\nFirst 200 characters:")
            print(repr(content[:200]))

        return True

    except Exception as e:
        print(f"Error testing export path: {e}")
        return False


if __name__ == "__main__":
    test_export_path()
