import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from questionary import Choice

from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.config_interactive import _open_webui_config_menu


class TestOpenWebUIConfig(unittest.TestCase):
    def test_open_webui_config_menu_url(self):
        """Test updating the Open-WebUI URL."""
        settings = get_settings().model_dump()
        config_dict = settings["auth"]["open_webui"].copy()

        with (
            patch("questionary.select") as mock_select,
            patch(
                "confluence_markdown_exporter.utils.config_interactive._prompt_for_new_value"
            ) as mock_prompt,
            patch(
                "confluence_markdown_exporter.utils.config_interactive.questionary.print"
            ) as mock_print,
            patch(
                "confluence_markdown_exporter.utils.config_interactive.set_setting"
            ) as mock_set_setting,
        ):
            # Mock the select function to return "url" and then "__back__"
            mock_select.return_value = MagicMock()
            mock_select.return_value.ask.side_effect = ["url", "__back__"]

            # Mock the prompt function to return a test URL
            mock_prompt.return_value = "https://openwebui.example.com/"

            # Call the function with a mock model
            mock_model = MagicMock()
            _open_webui_config_menu(config_dict, mock_model, "auth.open_webui")

            # Check if the prompt was called for the URL
            mock_prompt.assert_called()

            # Check if set_setting was called with the correct parameters
            mock_set_setting.assert_called_with(
                "auth.open_webui.url", "https://openwebui.example.com/"
            )

            # Check if the print function was called with the success message
            mock_print.assert_called_with(
                "auth.open_webui.url updated to https://openwebui.example.com/."
            )

    def test_open_webui_config_menu_api_key(self):
        """Test updating the Open-WebUI API key."""
        settings = get_settings().model_dump()
        config_dict = settings["auth"]["open_webui"].copy()

        with (
            patch("questionary.select") as mock_select,
            patch(
                "confluence_markdown_exporter.utils.config_interactive._prompt_for_new_value"
            ) as mock_prompt,
            patch(
                "confluence_markdown_exporter.utils.config_interactive.questionary.print"
            ) as mock_print,
            patch(
                "confluence_markdown_exporter.utils.config_interactive.set_setting"
            ) as mock_set_setting,
        ):
            # Mock the select function to return "api_key" and then "__back__"
            mock_select.return_value = MagicMock()
            mock_select.return_value.ask.side_effect = ["api_key", "__back__"]

            # Mock the prompt function to return a test API key
            mock_prompt.return_value = "test-api-key"

            # Call the function with a mock model
            mock_model = MagicMock()
            _open_webui_config_menu(config_dict, mock_model, "auth.open_webui")

            # Check if the prompt was called for the API key
            mock_prompt.assert_called()

            # Check if set_setting was called with the correct parameters
            mock_set_setting.assert_called_with("auth.open_webui.api_key", "test-api-key")

            # Check if the print function was called with the success message
            mock_print.assert_called_with("auth.open_webui.api_key updated.")


if __name__ == "__main__":
    unittest.main()
