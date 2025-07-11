import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from questionary import Choice

from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.config_interactive import _get_main_menu_choices
from confluence_markdown_exporter.utils.config_interactive import _get_open_webui_menu_choices


class TestOpenWebUIConfig(unittest.TestCase):
    def test_main_config_menu_includes_authentication(self):
        """Test that the main config menu includes the Authentication option."""
        settings = get_settings().model_dump()
        # We don't need to actually run the menu, just verify the choices
        choices = _get_main_menu_choices(settings)

        # Check if the Authentication option is in the choices
        auth_choice = next((c for c in choices if "Authentication" in str(c.title)), None)
        self.assertIsNotNone(auth_choice, "Authentication option not found in main config menu")
        if auth_choice is not None:
            self.assertEqual(
                auth_choice.value,
                ("auth", True),
                "Authentication option has incorrect value",
            )

    def test_open_webui_config_menu(self):
        """Test the Open-WebUI configuration submenu."""
        settings = get_settings().model_dump()
        config_dict = settings["auth"]["open_webui"]

        # We don't need to actually run the menu, just verify the choices
        choices = _get_open_webui_menu_choices()

        # Check if the expected options are in the choices
        export_choice = next((c for c in choices if "Export to Open-WebUI" in str(c.title)), None)
        self.assertIsNotNone(
            export_choice, "Export to Open-WebUI option not found in Open-WebUI menu"
        )
        if export_choice is not None:
            self.assertEqual(
                export_choice.value,
                "export_to_open_webui",
                "Export to Open-WebUI option has incorrect value",
            )

        back_choice = next((c for c in choices if "Back" in str(c.title)), None)
        self.assertIsNotNone(back_choice, "Back option not found in Open-WebUI menu")
        if back_choice is not None:
            self.assertEqual(back_choice.value, "__back__", "Back option has incorrect value")


if __name__ == "__main__":
    unittest.main()
