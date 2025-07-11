#!/usr/bin/env python3
"""Verification script to test that API token redaction removal is working correctly.
This script directly tests the _convert_paths_to_str() function and configuration persistence.
"""

import json
import tempfile
from pathlib import Path

from pydantic import AnyHttpUrl
from pydantic import SecretStr

from confluence_markdown_exporter.utils.app_data_store import APP_CONFIG_PATH
from confluence_markdown_exporter.utils.app_data_store import AuthConfig
from confluence_markdown_exporter.utils.app_data_store import ConfigModel
from confluence_markdown_exporter.utils.app_data_store import ExportConfig
from confluence_markdown_exporter.utils.app_data_store import OpenWebUIAuthConfig

# Import the functions we need to test
from confluence_markdown_exporter.utils.app_data_store import _convert_paths_to_str
from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.app_data_store import load_app_data
from confluence_markdown_exporter.utils.app_data_store import reset_to_defaults
from confluence_markdown_exporter.utils.app_data_store import save_app_data
from confluence_markdown_exporter.utils.app_data_store import set_setting


def test_convert_paths_to_str_with_secret():
    """Test that _convert_paths_to_str returns actual SecretStr values instead of [REDACTED]."""
    print("🔍 Testing _convert_paths_to_str() function...")

    # Test with a simple SecretStr
    test_api_key = SecretStr("sk-test-api-key-12345")
    result = _convert_paths_to_str(test_api_key)

    print(f"   Input SecretStr: {test_api_key}")
    print(f"   Converted result: {result}")
    print(f"   Type of result: {type(result)}")

    # Verify the result is the actual secret value, not "[REDACTED]"
    assert result == "sk-test-api-key-12345", f"Expected 'sk-test-api-key-12345', got '{result}'"
    assert result != "[REDACTED]", "Function is still returning [REDACTED]!"

    print("   ✅ _convert_paths_to_str() correctly returns actual secret value")
    return True


def test_convert_paths_to_str_with_nested_structure():
    """Test that _convert_paths_to_str works with nested dictionaries containing SecretStr."""
    print("\n🔍 Testing _convert_paths_to_str() with nested structure...")

    # Create a nested structure similar to our config
    test_data = {
        "auth": {
            "open_webui": {
                "url": "https://test.example.com",
                "api_key": SecretStr("sk-nested-test-key-67890"),
            },
            "confluence": {
                "api_token": SecretStr("confluence-token-abc123"),
                "pat": SecretStr("pat-token-def456"),
            },
        }
    }

    result = _convert_paths_to_str(test_data)

    print(f"   Input structure: {test_data}")
    print(f"   Converted result: {result}")

    # Verify all SecretStr values are converted to actual values
    assert isinstance(result, dict)
    assert result["auth"]["open_webui"]["api_key"] == "sk-nested-test-key-67890"
    assert result["auth"]["confluence"]["api_token"] == "confluence-token-abc123"
    assert result["auth"]["confluence"]["pat"] == "pat-token-def456"

    # Verify no [REDACTED] strings exist
    result_str = json.dumps(result)
    assert "[REDACTED]" not in result_str, "Found [REDACTED] in converted structure!"

    print("   ✅ Nested structure conversion works correctly")
    return True


def test_config_save_and_load_preserves_api_keys():
    """Test that saving and loading configuration preserves actual API key values."""
    print("\n🔍 Testing configuration save/load preserves API keys...")

    # Create a backup of current config path
    original_config_path = APP_CONFIG_PATH

    # Use a temporary file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        # Temporarily override the config path
        import confluence_markdown_exporter.utils.app_data_store as ads

        ads.APP_CONFIG_PATH = temp_path

        # Reset to defaults first
        reset_to_defaults()

        # Set test values
        test_api_key = "sk-save-load-test-key-xyz789"
        set_setting("auth.open_webui.url", "https://saveload.test.com")
        set_setting("auth.open_webui.api_key", SecretStr(test_api_key))
        set_setting("export.export_to_open_webui", True)

        print(f"   Set API key: {test_api_key}")

        # Load the settings back
        settings = get_settings()
        loaded_api_key = settings.auth.open_webui.api_key.get_secret_value()

        print(f"   Loaded API key: {loaded_api_key}")

        # Verify the API key was preserved
        assert loaded_api_key == test_api_key, f"Expected '{test_api_key}', got '{loaded_api_key}'"

        # Also check the raw file content
        with open(temp_path, "r") as f:
            file_content = f.read()

        print(f"   Raw file content: {file_content}")

        # Verify the actual API key is in the file (not [REDACTED])
        assert test_api_key in file_content, f"API key '{test_api_key}' not found in saved file"
        assert "[REDACTED]" not in file_content, "Found [REDACTED] in saved file!"

        print("   ✅ Configuration save/load preserves API keys correctly")
        return True

    finally:
        # Restore original config path
        ads.APP_CONFIG_PATH = original_config_path
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


def test_no_redacted_strings_in_config_operations():
    """Test that no [REDACTED] strings are generated during config operations."""
    print("\n🔍 Testing that no [REDACTED] strings are generated...")

    # Create a config with API keys
    config = ConfigModel(
        auth=AuthConfig(
            open_webui=OpenWebUIAuthConfig(
                url=AnyHttpUrl("https://noredacted.test.com"),
                api_key=SecretStr("sk-no-redacted-test-key-123"),
            )
        ),
        export=ExportConfig(export_to_open_webui=True),
    )

    # Convert to dict (this uses _convert_paths_to_str internally)
    config_dict = config.model_dump()
    converted_dict = _convert_paths_to_str(config_dict)

    # Convert to JSON string
    json_str = json.dumps(converted_dict, indent=2)

    print(f"   Generated JSON: {json_str}")

    # Verify no [REDACTED] strings exist anywhere
    assert "[REDACTED]" not in json_str, "Found [REDACTED] in generated JSON!"

    # Verify the actual API key is present
    assert "sk-no-redacted-test-key-123" in json_str, "API key not found in JSON!"

    print("   ✅ No [REDACTED] strings generated in config operations")
    return True


def main():
    """Run all verification tests."""
    print("🚀 Starting API Token Redaction Removal Verification\n")

    tests = [
        test_convert_paths_to_str_with_secret,
        test_convert_paths_to_str_with_nested_structure,
        test_config_save_and_load_preserves_api_keys,
        test_no_redacted_strings_in_config_operations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            failed += 1

    print("\n📊 Verification Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")

    if failed == 0:
        print(
            "\n🎉 All verification tests passed! API token redaction removal is working correctly."
        )
        print("   • SecretStr values are no longer redacted")
        print("   • Configuration saving and loading preserves actual API key values")
        print("   • No [REDACTED] strings are generated")
        print("   • The usability issue has been resolved")
        return True
    print(f"\n⚠️  {failed} verification test(s) failed. Please check the implementation.")
    return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
