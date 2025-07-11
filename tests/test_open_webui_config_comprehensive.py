import json
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from questionary import Choice

from confluence_markdown_exporter.utils.app_data_store import AnyHttpUrl
from confluence_markdown_exporter.utils.app_data_store import AuthConfig
from confluence_markdown_exporter.utils.app_data_store import ConfigModel
from confluence_markdown_exporter.utils.app_data_store import ExportConfig
from confluence_markdown_exporter.utils.app_data_store import OpenWebUIAuthConfig
from confluence_markdown_exporter.utils.app_data_store import SecretStr
from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.app_data_store import reset_to_defaults
from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.config_interactive import _get_main_menu_choices
from confluence_markdown_exporter.utils.config_interactive import _get_open_webui_menu_choices
from confluence_markdown_exporter.utils.config_interactive import _main_config_menu
from confluence_markdown_exporter.utils.config_interactive import _open_webui_config_menu


class TestOpenWebUIConfigComprehensive(unittest.TestCase):
    def test_interactive_menu_navigation(self):
        """Test that Open-WebUI settings are accessible through Export Settings and Authentication."""
        settings = get_settings().model_dump()
        choices = _get_main_menu_choices(settings)

        # Verify that the duplicate "Open-WebUI Settings" option is no longer in main menu
        open_webui_choice = next(
            (c for c in choices if "Open-WebUI Settings" in str(c.title)), None
        )
        self.assertIsNone(
            open_webui_choice,
            "Duplicate Open-WebUI Settings option should not be in main config menu",
        )

        # Verify Export Settings menu exists (contains Open-WebUI export options)
        export_choice = next((c for c in choices if "Export Settings" in str(c.title)), None)
        self.assertIsNotNone(export_choice, "Export Settings option not found in main config menu")

        # Verify Authentication menu exists (contains Open-WebUI URL and API key)
        auth_choice = next((c for c in choices if "Authentication" in str(c.title)), None)
        self.assertIsNotNone(auth_choice, "Authentication option not found in main config menu")

        # Test that Open-WebUI submenu choices are still available for direct access
        submenu_choices = _get_open_webui_menu_choices()
        export_choice = next(
            (c for c in submenu_choices if "Export to Open-WebUI" in str(c.title)), None
        )
        self.assertIsNotNone(export_choice, "Export option not found in Open-WebUI menu")

    def test_set_url_and_api_key_independently(self):
        """Test setting URL and API key independently."""
        # Test setting only URL
        set_setting("auth.open_webui.url", "https://openwebui.test.com")
        settings = get_settings()
        # Normalize URL for comparison (remove trailing slash)
        url_str = str(settings.auth.open_webui.url).rstrip("/")
        self.assertEqual(url_str, "https://openwebui.test.com")
        # Now we can directly compare the API key value since redaction is removed
        self.assertIsInstance(settings.auth.open_webui.api_key, SecretStr)
        self.assertEqual(str(settings.auth.open_webui.api_key), "")

        # Reset
        reset_to_defaults("auth.open_webui.url")

        # Test setting only API key
        set_setting("auth.open_webui.api_key", SecretStr("test-key-123"))
        settings = get_settings()
        # Now we can directly compare the API key value since redaction is removed
        self.assertEqual(settings.auth.open_webui.api_key.get_secret_value(), "test-key-123")
        self.assertEqual(settings.auth.open_webui.url, "")

        # Clean up
        reset_to_defaults("auth.open_webui")

    def test_validation_logic(self):
        """Test validation logic for Open-WebUI configuration."""
        # First reset everything to ensure clean state
        reset_to_defaults()

        # Set both URL and API key
        set_setting("auth.open_webui.url", "https://openwebui.test.com")
        set_setting("auth.open_webui.api_key", SecretStr("test-key-123"))

        # Now enable export_to_open_webui (should work)
        set_setting("export.export_to_open_webui", True)

        settings = get_settings()
        # Normalize URL for comparison
        url_str = str(settings.auth.open_webui.url).rstrip("/")
        self.assertEqual(url_str, "https://openwebui.test.com")
        # We can't directly compare the API key value because it's redacted
        self.assertIsNotNone(settings.auth.open_webui.api_key)
        self.assertTrue(settings.export.export_to_open_webui)

        # Reset
        reset_to_defaults()

        # Test with export_to_open_webui enabled but missing URL
        # First set URL and API key
        set_setting("auth.open_webui.url", "https://openwebui.test.com")
        set_setting("auth.open_webui.api_key", SecretStr("test-key-123"))

        # Then reset URL to test validation
        reset_to_defaults("auth.open_webui.url")

        # This should raise an error when we try to validate
        with self.assertRaises(ValueError):
            # This should raise an error because URL is missing
            ConfigModel(
                export=ExportConfig(export_to_open_webui=True),
                auth=get_settings().auth,
            )

        # Reset
        reset_to_defaults()

        # Test with export_to_open_webui enabled but missing API key
        # First set URL and API key
        set_setting("auth.open_webui.url", "https://openwebui.test.com")
        set_setting("auth.open_webui.api_key", SecretStr("test-key-123"))

        # Then reset API key to test validation
        reset_to_defaults("auth.open_webui.api_key")

        # This should raise an error when we try to validate
        with self.assertRaises(ValueError):
            # This should raise an error because API key is missing
            ConfigModel(
                export=ExportConfig(export_to_open_webui=True),
                auth=AuthConfig(
                    open_webui=OpenWebUIAuthConfig(
                        url=AnyHttpUrl("https://openwebui.test.com"), api_key=SecretStr("")
                    )
                ),
            )

        # Clean up
        reset_to_defaults()

    def test_config_persistence(self):
        """Test that configuration is saved and loaded correctly."""
        # Set values
        set_setting("auth.open_webui.url", "https://openwebui.test.com")
        set_setting("auth.open_webui.api_key", SecretStr("test-key-123"))
        set_setting("export.export_to_open_webui", True)

        # Reload settings
        settings = get_settings()
        # Normalize URL for comparison
        url_str = str(settings.auth.open_webui.url).rstrip("/")
        self.assertEqual(url_str, "https://openwebui.test.com")
        # We can't directly compare the API key value because it's redacted
        self.assertIsNotNone(settings.auth.open_webui.api_key)
        self.assertTrue(settings.export.export_to_open_webui)

        # Reset to defaults
        reset_to_defaults()
        settings = get_settings()
        self.assertEqual(settings.auth.open_webui.url, "")
        # Now we can directly compare the API key value since redaction is removed
        self.assertIsInstance(settings.auth.open_webui.api_key, SecretStr)
        self.assertEqual(str(settings.auth.open_webui.api_key), "")
        self.assertFalse(settings.export.export_to_open_webui)

    def test_example_config_file(self):
        """Test that example configuration file includes Open-WebUI settings."""
        example_path = Path("config/app_data.json.example")
        self.assertTrue(example_path.exists(), "Example config file does not exist")

        # Read the file content
        with open(example_path, "r") as f:
            content = f.read()

        # Remove comments (lines starting with //)
        content = re.sub(r"//.*?\n", "", content)

        try:
            # Try to parse the content
            example_content = json.loads(content)
            self.assertIn("open_webui", example_content["auth"], "Open-WebUI not in auth section")
            self.assertIn(
                "url", example_content["auth"]["open_webui"], "URL not in Open-WebUI config"
            )
            self.assertIn(
                "api_key", example_content["auth"]["open_webui"], "API key not in Open-WebUI config"
            )
            self.assertIn(
                "export_to_open_webui",
                example_content["export"],
                "Export flag not in export section",
            )
        except json.JSONDecodeError as e:
            self.fail(f"Example config file has JSON syntax error after removing comments: {e}")


if __name__ == "__main__":
    unittest.main()
