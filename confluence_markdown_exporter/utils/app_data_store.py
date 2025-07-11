"""Handles storage and retrieval of application data (auth and settings) for the exporter."""

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field
from pydantic import SecretStr
from pydantic import ValidationError
from pydantic import validator
from typer import get_app_dir


def get_app_config_path() -> Path:
    """Determine the path to the app config file, creating parent directories if needed."""
    config_env = os.environ.get("CME_CONFIG_PATH")
    if config_env:
        path = Path(config_env)
    else:
        app_name = "confluence-markdown-exporter"
        config_dir = Path(get_app_dir(app_name))
        path = config_dir / "app_data.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


APP_CONFIG_PATH = get_app_config_path()


class RetryConfig(BaseModel):
    """Configuration for network retry behavior."""

    backoff_and_retry: bool = Field(
        default=True,
        title="Enable Retry",
        description="Enable or disable automatic retry with exponential backoff on network errors.",
    )
    backoff_factor: int = Field(
        default=2,
        title="Backoff Factor",
        description=(
            "Multiplier for exponential backoff between retries. "
            "For example, 2 means each retry waits twice as long as the previous."
        ),
    )
    max_backoff_seconds: int = Field(
        default=60,
        title="Max Backoff Seconds",
        description="Maximum number of seconds to wait between retries.",
    )
    max_backoff_retries: int = Field(
        default=5,
        title="Max Retries",
        description="Maximum number of retry attempts before giving up.",
    )
    retry_status_codes: list[int] = Field(
        default_factory=lambda: [413, 429, 502, 503, 504],
        title="Retry Status Codes",
        description="HTTP status codes that should trigger a retry.",
    )


class ApiDetails(BaseModel):
    """API authentication details."""

    url: AnyHttpUrl | Literal[""] = Field(
        "", title="Instance URL", description="Base URL of the Confluence or Jira instance."
    )
    username: str = Field(
        "", title="Username (email)", description="Username or email for API authentication."
    )
    api_token: SecretStr = Field(
        SecretStr(""),
        title="API Token",
        description=(
            "API token for authentication (if required). "
            "Create an Atlassian API token at "
            "https://id.atlassian.com/manage-profile/security/api-tokens. "
            "See Atlassian documentation for details."
        ),
    )
    pat: SecretStr = Field(
        SecretStr(""),
        title="Personal Access Token (PAT)",
        description=(
            "Personal Access Token for authentication. "
            "Set this if you use a PAT instead of username+API token. "
            "See your Atlassian instance documentation for how to create a PAT."
        ),
    )


class OpenWebUIAuthConfig(BaseModel):
    """Configuration for Open-WebUI authentication"""

    url: AnyHttpUrl | Literal[""] = Field(
        "", title="Open-WebUI URL", description="Base URL of the Open-WebUI instance."
    )
    api_key: SecretStr = Field(
        SecretStr(""),
        title="Open-WebUI API Key",
        description="API key for Open-WebUI authentication.",
    )

    @validator("api_key")
    def api_key_must_not_be_empty(cls, v, values):
        """Validate that the API key is not empty when export_to_open_webui is enabled."""
        # Get export_to_open_webui from parent model if available
        export_enabled = values.get("export_to_open_webui", False)
        if export_enabled and v.get_secret_value() == "":
            raise ValueError("API key must not be empty when export_to_open_webui is enabled")
        return v


class AuthConfig(BaseModel):
    """Authentication configuration for Confluence and Jira."""

    confluence: ApiDetails = Field(
        default_factory=lambda: ApiDetails(
            url="", username="", api_token=SecretStr(""), pat=SecretStr("")
        ),
        title="Confluence Account",
        description="Authentication for Confluence.",
    )
    jira: ApiDetails = Field(
        default_factory=lambda: ApiDetails(
            url="", username="", api_token=SecretStr(""), pat=SecretStr("")
        ),
        title="Jira Account",
        description="Authentication for Jira.",
    )
    open_webui: OpenWebUIAuthConfig = Field(
        default_factory=lambda: OpenWebUIAuthConfig(url="", api_key=SecretStr("")),
        title="Open-WebUI Account",
        description="Authentication for Open-WebUI.",
    )


class ExportConfig(BaseModel):
    """Export settings for markdown and attachments."""

    output_path: Path = Field(
        default=Path("."),
        title="Output Path",
        description=("Directory where exported pages and attachments will be saved."),
        examples=[
            "`.`: Output will be saved relative to the current working directory.",
            (
                "`./confluence_export`: Output will be saved in a folder `confluence_export` "
                "relative to the current working directory."
            ),
            "`/path/to/export`: Output will be saved in the specified absolute path.",
        ],
    )
    page_href: Literal["absolute", "relative"] = Field(
        default="relative",
        title="Page Href Style",
        description=(
            "How to generate page href paths. Options: absolute, relative.\n"
            "  - `relative` links are relative to the page"
            "  - `absolute` links start from the configured output path"
        ),
    )
    page_path: str = Field(
        default="{space_name}/{homepage_title}/{ancestor_titles}/{page_title}.md",
        title="Page Path Template",
        description=(
            "Template for exported page file paths.\n"
            "Available variables:\n"
            "  - {space_key}: The key of the Confluence space.\n"
            "  - {space_name}: The name of the Confluence space.\n"
            "  - {homepage_id}: The ID of the homepage of the Confluence space.\n"
            "  - {homepage_title}: The title of the homepage of the Confluence space.\n"
            "  - {ancestor_ids}: A slash-separated list of ancestor page IDs.\n"
            "  - {ancestor_titles}: A slash-separated list of ancestor page titles.\n"
            "  - {page_id}: The unique ID of the Confluence page.\n"
            "  - {page_title}: The title of the Confluence page."
        ),
        examples=["{space_name}/{page_title}.md"],
    )
    attachment_href: Literal["absolute", "relative"] = Field(
        default="relative",
        title="Attachment Href Style",
        description=(
            "How to generate attachment href paths. Options: absolute, relative.\n"
            "  - `relative` links are relative to the page"
            "  - `absolute` links start from the configured output path"
        ),
    )
    attachment_path: str = Field(
        default="{space_name}/attachments/{attachment_file_id}{attachment_extension}",
        title="Attachment Path Template",
        description=(
            "Template for exported attachment file paths.\n"
            "Available variables:\n"
            "  - {space_key}: The key of the Confluence space.\n"
            "  - {space_name}: The name of the Confluence space.\n"
            "  - {homepage_id}: The ID of the homepage of the Confluence space.\n"
            "  - {homepage_title}: The title of the homepage of the Confluence space.\n"
            "  - {ancestor_ids}: A slash-separated list of ancestor page IDs.\n"
            "  - {ancestor_titles}: A slash-separated list of ancestor page titles.\n"
            "  - {attachment_id}: The unique ID of the attachment.\n"
            "  - {attachment_title}: The title of the attachment.\n"
            "  - {attachment_file_id}: The file ID of the attachment.\n"
            "  - {attachment_extension}: The file extension of the attachment, "
            "including the leading dot."
        ),
        examples=["{space_name}/attachments/{attachment_file_id}{attachment_extension}"],
    )
    page_breadcrumbs: bool = Field(
        default=True,
        title="Page Breadcrumbs",
        description="Whether to include breadcrumb links at the top of the page.",
    )
    include_document_title: bool = Field(
        default=True,
        title="Include Document Title",
        description=(
            "Whether to include the document title in the exported markdown file. "
            "If enabled, the title will be added as a top-level heading."
        ),
    )
    export_to_open_webui: bool = Field(
        default=False,
        title="Export to Open-WebUI",
        description="Whether to export pages to Open-WebUI knowledge base.",
    )
    open_webui_attachment_extensions: str = Field(
        default="md,txt,pdf",
        title="Open-WebUI Attachment Extensions",
        description=(
            "Comma-separated list of file extensions to include when exporting "
            "attachments to Open-WebUI. Example: 'md,txt,pdf'"
        ),
    )
    open_webui_batch_add: bool = Field(
        default=True,
        title="Open-WebUI Batch Add",
        description=(
            "Whether to use batch processing when adding files to Open-WebUI. "
            "Batch processing is more efficient but may use more memory."
        ),
    )


class ConfigModel(BaseModel):
    """Top-level application configuration model."""

    export: ExportConfig = Field(default_factory=ExportConfig, title="Export Settings")
    retry_config: RetryConfig = Field(default_factory=RetryConfig, title="Retry/Network Settings")
    auth: AuthConfig = Field(default_factory=AuthConfig, title="Authentication")

    @validator("auth")
    def check_open_webui_credentials(cls, v, values):
        """Ensure both URL and API key are set when export_to_open_webui is enabled."""
        # Get export config from values
        export_config = values.get("export", None)
        if export_config is not None and getattr(export_config, "export_to_open_webui", False):
            open_webui = v.open_webui
            if not open_webui.url:
                raise ValueError("URL must be set when export_to_open_webui is enabled")
            if not open_webui.api_key.get_secret_value():
                raise ValueError("API key must be set when export_to_open_webui is enabled")
        return v


def _convert_paths_to_str(obj: object) -> object:
    """Recursively convert Path, SecretStr, and AnyHttpUrl objects to str."""
    if isinstance(obj, dict):
        return {k: _convert_paths_to_str(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_paths_to_str(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, SecretStr):
        # Return the actual secret value instead of redacting
        return obj.get_secret_value()
    if isinstance(obj, AnyHttpUrl):
        return str(obj)
    return obj


def load_app_data() -> dict[str, dict]:
    """Load application data from the config file, returning a validated dict."""
    data = json.loads(APP_CONFIG_PATH.read_text()) if APP_CONFIG_PATH.exists() else {}
    try:
        return ConfigModel(**data).model_dump()
    except ValidationError:
        return ConfigModel().model_dump()


def save_app_data(data: dict[str, dict]) -> None:
    """Save application data to the config file after conversion and validation."""
    data_obj = _convert_paths_to_str(data)
    if not isinstance(data_obj, dict):
        msg = "Data must be a dict after conversion"
        raise TypeError(msg)
    APP_CONFIG_PATH.write_text(json.dumps(data_obj, indent=2))


def get_settings() -> ConfigModel:
    """Get the current application settings as a ConfigModel instance."""
    data = load_app_data()
    return ConfigModel(
        export=ExportConfig(**data.get("export", {})),
        retry_config=RetryConfig(**data.get("retry_config", {})),
        auth=AuthConfig(**data.get("auth", {})),
    )


def _set_by_path(obj: dict, path: str, value: object) -> None:
    """Set a value in a nested dict using dot notation path."""
    keys = path.split(".")
    current = obj
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value


def set_setting(path: str, value: object) -> None:
    """Set a setting by dot-path and save to config file without overwriting API keys."""
    # Load current configuration
    data = load_app_data()

    # Make a copy of auth section to preserve API keys
    auth_copy = data.get("auth", {}).copy() if "auth" in data else {}

    # Update the setting
    _set_by_path(data, path, value)

    try:
        # Validate the updated configuration
        settings = ConfigModel.model_validate(data)
        settings_dict = settings.model_dump()

        # Preserve API keys in auth section
        if "auth" in settings_dict:
            # Only preserve API keys if they weren't explicitly changed
            if path.split(".")[0] != "auth" or (
                len(path.split(".")) > 1
                and path.split(".")[1] not in ["api_token", "pat", "api_key"]
            ):
                # Preserve Confluence API keys
                if "confluence" in auth_copy and "confluence" in settings_dict["auth"]:
                    if "api_token" in auth_copy.get("confluence", {}):
                        settings_dict["auth"]["confluence"]["api_token"] = auth_copy["confluence"][
                            "api_token"
                        ]
                    if "pat" in auth_copy.get("confluence", {}):
                        settings_dict["auth"]["confluence"]["pat"] = auth_copy["confluence"]["pat"]

                # Preserve Jira API keys
                if "jira" in auth_copy and "jira" in settings_dict["auth"]:
                    if "api_token" in auth_copy.get("jira", {}):
                        settings_dict["auth"]["jira"]["api_token"] = auth_copy["jira"]["api_token"]
                    if "pat" in auth_copy.get("jira", {}):
                        settings_dict["auth"]["jira"]["pat"] = auth_copy["jira"]["pat"]

                # Preserve Open-WebUI API key
                if "open_webui" in auth_copy and "open_webui" in settings_dict["auth"]:
                    if "api_key" in auth_copy.get("open_webui", {}):
                        settings_dict["auth"]["open_webui"]["api_key"] = auth_copy["open_webui"][
                            "api_key"
                        ]

        # Save the updated configuration
        save_app_data(settings_dict)
    except ValidationError as e:
        raise ValueError(str(e)) from e


def get_default_value_by_path(path: str | None = None) -> object:
    """Get the default value for a given config path, or the whole config if path is None."""
    model = ConfigModel()
    if not path:
        return model.model_dump()
    keys = path.split(".")
    current = model
    for k in keys:
        if hasattr(current, k):
            current = getattr(current, k)
        elif isinstance(current, dict) and k in current:
            current = current[k]
        else:
            msg = f"Invalid config path: {path}"
            raise KeyError(msg)
    if isinstance(current, BaseModel):
        return current.model_dump()
    return current


def reset_to_defaults(path: str | None = None) -> None:
    """Reset the whole config, a section, or a single option to its default value.

    If path is None, reset the entire config. Otherwise, reset the specified path.
    """
    if path is None:
        save_app_data(ConfigModel().model_dump())
        return
    data = load_app_data()
    default_value = get_default_value_by_path(path)
    _set_by_path(data, path, default_value)
    save_app_data(data)
