#!/usr/bin/env python3
"""Simple test to verify export configuration and file content."""

import json
from pathlib import Path


def test_configuration_and_files():
    """Test current configuration and exported file content."""
    print("=== CONFIGURATION ANALYSIS ===")

    # Read config file
    config_file = Path("config/app_data.json")
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)

        export_config = config.get("export", {})
        print(f"Export to Open WebUI: {export_config.get('export_to_open_webui', False)}")
        print(f"Open WebUI URL configured: {'url' in config.get('auth', {}).get('open_webui', {})}")
        print(
            f"Open WebUI API key configured: {'api_key' in config.get('auth', {}).get('open_webui', {})}"
        )
    else:
        print("Config file not found")

    print("\n=== EXPORTED FILE ANALYSIS ===")

    # Check exported files
    export_files = [
        "exports/My first space/My first space/Searchable Title #2.md",
        "exports/My first space/My first space/My first space.md",
        "exports/My first space/My first space/This is the page of today 24.06.25.md",
    ]

    for file_path in export_files:
        file_obj = Path(file_path)
        if file_obj.exists():
            content = file_obj.read_text()
            print(f"\nFile: {file_obj.name}")
            print(f"  Size: {len(content)} characters")
            print(f"  Has YAML frontmatter: {'---' in content[:100]}")
            print(f"  Has JSON frontmatter: {'```json' in content[:100]}")
            print(f"  Starts with title: {content.strip().startswith('#')}")
            print(f"  First 100 chars: {content[:100]!r}")
        else:
            print(f"\nFile not found: {file_path}")


if __name__ == "__main__":
    test_configuration_and_files()
