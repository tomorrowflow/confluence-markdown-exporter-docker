#!/usr/bin/env python3
"""Test script to verify that API keys are preserved when saving configuration."""

import json
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from confluence_markdown_exporter.utils.app_data_store import get_app_config_path
from confluence_markdown_exporter.utils.app_data_store import load_app_data
from confluence_markdown_exporter.utils.app_data_store import set_setting


def test_api_key_preservation():
    """Test that API keys are preserved when saving configuration."""
    print("Testing API key preservation...")

    # Get the current configuration
    current_config = load_app_data()

    # Make a copy of the current API keys for comparison
    original_confluence_api_token = (
        current_config.get("auth", {}).get("confluence", {}).get("api_token")
    )
    original_confluence_pat = current_config.get("auth", {}).get("confluence", {}).get("pat")
    original_jira_api_token = current_config.get("auth", {}).get("jira", {}).get("api_token")
    original_jira_pat = current_config.get("auth", {}).get("jira", {}).get("pat")
    original_open_webui_api_key = (
        current_config.get("auth", {}).get("open_webui", {}).get("api_key")
    )

    print(f"Original Confluence API Token: {original_confluence_api_token}")
    print(f"Original Confluence PAT: {original_confluence_pat}")
    print(f"Original Jira API Token: {original_jira_api_token}")
    print(f"Original Jira PAT: {original_jira_pat}")
    print(f"Original Open-WebUI API Key: {original_open_webui_api_key}")

    # Update a non-API-key setting
    print("\nUpdating a non-API-key setting (export.output_path)...")
    set_setting("export.output_path", "/tmp/test_export")

    # Reload the configuration
    updated_config = load_app_data()

    # Check if API keys were preserved
    new_confluence_api_token = updated_config.get("auth", {}).get("confluence", {}).get("api_token")
    new_confluence_pat = updated_config.get("auth", {}).get("confluence", {}).get("pat")
    new_jira_api_token = updated_config.get("auth", {}).get("jira", {}).get("api_token")
    new_jira_pat = updated_config.get("auth", {}).get("jira", {}).get("pat")
    new_open_webui_api_key = updated_config.get("auth", {}).get("open_webui", {}).get("api_key")

    print(f"New Confluence API Token: {new_confluence_api_token}")
    print(f"New Confluence PAT: {new_confluence_pat}")
    print(f"New Jira API Token: {new_jira_api_token}")
    print(f"New Jira PAT: {new_jira_pat}")
    print(f"New Open-WebUI API Key: {new_open_webui_api_key}")

    # Verify that API keys were preserved
    api_keys_preserved = (
        original_confluence_api_token == new_confluence_api_token
        and original_confluence_pat == new_confluence_pat
        and original_jira_api_token == new_jira_api_token
        and original_jira_pat == new_jira_pat
        and original_open_webui_api_key == new_open_webui_api_key
    )

    if api_keys_preserved:
        print("\nSUCCESS: All API keys were preserved!")
    else:
        print("\nFAILURE: Some API keys were overwritten!")

    # Reset the setting to its original value
    print("\nResetting export.output_path to its original value...")
    original_output_path = current_config.get("export", {}).get("output_path")
    set_setting("export.output_path", original_output_path)

    print("Test completed.")


if __name__ == "__main__":
    test_api_key_preservation()
