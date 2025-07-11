"""Open-WebUI API client implementation."""

import logging
import os
import re
import time
from collections.abc import Callable
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import requests
from pydantic import AnyHttpUrl
from pydantic import SecretStr
from requests.adapters import HTTPAdapter
from requests.adapters import Retry

from confluence_markdown_exporter.utils.app_data_store import OpenWebUIAuthConfig
from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.config_interactive import main_config_menu_loop

# Configure logging with structured logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger(__name__)
# Create a separate logger for sensitive information
sensitive_logger = logging.getLogger(f"{__name__}.sensitive")
sensitive_logger.setLevel(logging.DEBUG)

# Regular expression for redacting sensitive information
SENSITIVE_INFO_PATTERN = re.compile(r"(?i)\b(api_key|authorization|secret|token|password)\b")


# Context manager for structured logging
class LoggingContext:
    """Context manager for adding structured context to logs."""

    def __init__(self, logger, context_dict):
        self.logger = logger
        self.context_dict = context_dict
        self.original_extra = getattr(self.logger, "_logExtra", {})

    def __enter__(self):
        # Store the context in the logger
        self.logger._logExtra = self.context_dict
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore the original extra
        self.logger._logExtra = self.original_extra

    @staticmethod
    def log_with_context(logger, context_dict, message, level="info"):
        """Log a message with the given context."""
        with LoggingContext(logger, context_dict):
            if level == "info":
                logger.info(message)
            elif level == "debug":
                logger.debug(message)
            elif level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
            elif level == "critical":
                logger.critical(message)


DEBUG: bool = bool(os.getenv("DEBUG"))


def redact_sensitive_info(text: str | bytes) -> str:
    """Pass through sensitive information without redaction."""
    if not text:
        return str(text)
    # Convert bytes to str if needed
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    # Return the original text without redaction
    return str(text)


def response_hook(
    response: requests.Response, *args: object, **kwargs: object
) -> requests.Response:
    """Log response headers when requests fail."""
    if not response.ok:
        print(f"Request to {response.url} failed with status {response.status_code}")
        # Use original headers without redaction
        headers = {k: v for k, v in dict(response.headers).items()}
        print(f"Response headers: {headers}")
    return response


class APIKeyError(Exception):
    """Custom exception for API key-related errors."""

    def __init__(self, message: str):
        super().__init__(message)
        # Log API key errors with sensitive information
        sensitive_logger.error(f"API Key Error: {message}")
        # Log the original error message without redaction
        logger.error(f"API Key Error: {message}")


class OpenWebUIClient:
    """Client for interacting with the Open-WebUI API."""

    def __init__(self, url: str, api_key: str, retry_config: dict[str, Any] = {}):
        """Initialize the Open-WebUI API client."""
        # Validate URL format
        if not url:
            raise ValueError("URL must not be empty")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("URL must start with 'http://' or 'https://'")

        # Validate API key format
        if not api_key:
            raise APIKeyError("API key must not be empty")
        if not api_key.startswith("sk-"):
            raise APIKeyError("API key must start with 'sk-'")

        self.url = url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )

        # Setup retry configuration
        self.retry_config = retry_config
        self._setup_retry(self.session, retry_config)

        # Test connection to validate credentials
        self._validate_connection()

        if DEBUG:
            self.session.hooks["response"] = [response_hook]

    def _setup_retry(self, session: requests.Session, config: dict[str, Any]):
        """Setup retry configuration for the requests session."""
        if not config:
            return

        retry = Retry(
            total=config.get("max_retries", 3),
            read=config.get("max_retries", 3),
            connect=config.get("max_retries", 3),
            backoff_factor=config.get("backoff_factor", 0.3),
            status_forcelist=config.get("status_forcelist", [500, 502, 503, 504]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

    @classmethod
    def from_auth_config(
        cls, auth_config: OpenWebUIAuthConfig, retry_config: dict[str, Any] | None = None
    ) -> "OpenWebUIClient":
        """Create an OpenWebUIClient instance from authentication configuration."""
        try:
            return cls(
                url=str(auth_config.url),
                api_key=auth_config.api_key.get_secret_value(),
                retry_config=retry_config or {},
            )
        except ValueError as e:
            # Re-raise with a more specific error message if it's about API key format
            if "API key" in str(e):
                raise APIKeyError(f"Invalid API key: {e}")
            raise

    def _validate_connection(self) -> None:
        """Validate API connection by making a test request."""
        try:
            response = self._make_request("GET", "/health")
            if response.status_code != 200:
                raise APIKeyError(f"API connection failed with status {response.status_code}")
            status_data = response.json()
            if not status_data.get("status"):
                raise APIKeyError(
                    f"API returned error status: {status_data.get('message', 'Unknown error')}"
                )
            logger.info("API connection validated successfully")
        except Exception as e:
            raise APIKeyError(f"Failed to validate API connection: {e}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with proper error handling and structured logging."""
        # Special handling for health endpoint
        if endpoint == "/health":
            url = f"{self.url}{endpoint}"
        # Don't add trailing slash for endpoints that already have specific paths
        elif endpoint.endswith(("/create", "/update", "/delete", "/add", "/reindex")):
            url = f"{self.url}/api/v1{endpoint}"
        else:
            url = f"{self.url}/api/v1{endpoint}/"

        # Handle multipart file uploads by temporarily removing Content-Type header
        session_headers = dict(self.session.headers)
        if "files" in kwargs:
            # Remove Content-Type header for multipart uploads - requests will set it automatically
            session_headers.pop("Content-Type", None)
            # Create a temporary session with modified headers
            temp_session = requests.Session()
            temp_session.headers.update(session_headers)
            # Setup retry configuration for temp session
            self._setup_retry(temp_session, self.retry_config)
            session_to_use = temp_session
        else:
            session_to_use = self.session

        # Create context for this request
        request_context = {
            "request_method": method,
            "request_url": url,
            "request_headers": dict(session_to_use.headers),
            "request_data": str(kwargs.get("json", kwargs.get("data", kwargs.get("files")))),
        }

        # Log request details with context
        LoggingContext.log_with_context(
            logger, request_context, f"Making {method} request to {request_context['request_url']}"
        )
        LoggingContext.log_with_context(
            logger, request_context, f"Request headers: {request_context['request_headers']}"
        )
        LoggingContext.log_with_context(
            logger, request_context, f"Request data: {request_context['request_data']}"
        )

        # Log full request details with sensitive information to sensitive logger
        if DEBUG:
            sensitive_context = {
                "request_method": method,
                "request_url": url,
                "request_headers": dict(self.session.headers),
                "request_data": kwargs.get("json", kwargs.get("data")),
            }
            sensitive_logger.debug(f"Making {method} request to {url}")
            sensitive_logger.debug(f"Request headers: {dict(self.session.headers)}")
            sensitive_logger.debug(f"Request data: {kwargs.get('json', kwargs.get('data'))}")

        try:
            response = session_to_use.request(method, url, **kwargs)

            # Update context with response information
            response_context = request_context.copy()
            response_context.update(
                {
                    "response_status": str(response.status_code),
                    "response_headers": dict(response.headers),
                }
            )

            # Log response status with context
            LoggingContext.log_with_context(
                logger, response_context, f"Response status: {response.status_code}"
            )

            # Add detailed URL logging
            LoggingContext.log_with_context(logger, response_context, f"Full request URL: {url}")

            # Log redacted response headers with context
            LoggingContext.log_with_context(
                logger,
                response_context,
                f"Response headers: {response_context['response_headers']}",
            )

            # Log Content-Type header for debugging
            content_type = response.headers.get("Content-Type", "No Content-Type header")
            LoggingContext.log_with_context(
                logger, response_context, f"Content-Type: {content_type}"
            )

            # Log redacted response content
            response_content = response.text
            response_context["response_content"] = response_content[:500]
            LoggingContext.log_with_context(
                logger,
                response_context,
                f"Response content (first 500 chars): {response_content[:500]}",
            )

            # Log full response details with sensitive information to sensitive logger
            if DEBUG:
                sensitive_response_context = (
                    sensitive_context.copy() if "sensitive_context" in locals() else {}
                )
                sensitive_response_context.update(
                    {
                        "response_status": response.status_code,
                        "response_headers": dict(response.headers),
                        "response_content": response_content[:500],
                    }
                )
                sensitive_logger.debug(f"Response headers: {dict(response.headers)}")
                sensitive_logger.debug(
                    f"Response content (first 500 chars): {response_content[:500]}"
                )

            # Check for API key related errors
            if response.status_code == 401:  # Unauthorized
                error_info = response.json()
                error_msg = error_info.get("error", "Unauthorized access")
                if "api_key" in error_msg.lower() or "authorization" in error_msg.lower():
                    # Check for expiration
                    if "expired" in error_msg.lower():
                        raise APIKeyError(f"API key has expired: {error_msg}")
                    # Log the original error message without redaction
                    LoggingContext.log_with_context(
                        logger,
                        response_context,
                        f"API key authentication failed: {error_msg}",
                        level="error",
                    )
                    sensitive_logger.error(f"API key authentication failed: {error_msg}")
                    raise APIKeyError(f"API key authentication failed: {error_msg}")
                response.raise_for_status()

            return response
        except requests.RequestException as e:
            error_context = {"error_message": str(e), "error_type": type(e).__name__}

            error_msg = f"Open-WebUI API request failed: {e}"
            LoggingContext.log_with_context(logger, error_context, error_msg, level="error")

            if hasattr(e, "response") and e.response:
                error_context["response_status"] = str(e.response.status_code)

                # Log the original error content without redaction
                error_content = e.response.text
                error_context["error_response_content"] = error_content

                LoggingContext.log_with_context(
                    logger,
                    error_context,
                    f"Error response status: {e.response.status_code}",
                    level="error",
                )
                LoggingContext.log_with_context(
                    logger,
                    error_context,
                    f"Error response content: {error_content}",
                    level="error",
                )

                # Log full error content to sensitive logger
                if DEBUG:
                    sensitive_error_context = {
                        "error_message": str(e),
                        "error_type": type(e).__name__,
                        "response_status": e.response.status_code,
                        "error_response_content": error_content,
                    }
                    sensitive_logger.error(f"Error response content: {error_content}")

                # Check for API key related errors in response
                try:
                    error_info = e.response.json()
                    if (error_info.get("error") or "").lower().find(
                        "api_key"
                    ) >= 0 or error_info.get("message", "").lower().find("api_key") >= 0:
                        # Log the original error without redaction
                        error_msg = str(error_info.get("error", "Unknown API key error"))
                        error_context["api_key_error"] = error_msg
                        LoggingContext.log_with_context(
                            logger,
                            error_context,
                            f"API key error detected: {error_msg}",
                            level="error",
                        )
                        sensitive_logger.error(f"API key error detected: {error_msg}")
                        raise APIKeyError(f"API key error detected: {error_msg}")
                except ValueError:
                    # Not JSON, continue with general error
                    pass

            raise

    def get_knowledge(self) -> dict[str, Any]:
        """Get knowledge items from Open-WebUI."""
        response = self._make_request("GET", "/knowledge")
        return response.json()

    def get_knowledge_by_id(self, knowledge_id: str) -> dict[str, Any]:
        """Get a specific knowledge item by ID."""
        response = self._make_request("GET", f"/knowledge/{knowledge_id}")
        return response.json()

    def create_knowledge(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new knowledge item."""
        response = self._make_request("POST", "/knowledge/create", json=data)
        return response.json()

    def update_knowledge(self, knowledge_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing knowledge item."""
        response = self._make_request("POST", f"/knowledge/{knowledge_id}/update", json=data)
        return response.json()

    def delete_knowledge(self, knowledge_id: str) -> dict[str, Any]:
        """Delete a knowledge item."""
        response = self._make_request("DELETE", f"/knowledge/{knowledge_id}/delete")
        return response.json()

    def reindex_knowledge_files(self) -> bool:
        """Reindex knowledge files."""
        response = self._make_request("POST", "/knowledge/reindex")
        return response.json()

    def list_files(self) -> dict[str, Any]:
        """List all files in Open-WebUI."""
        response = self._make_request("GET", "/files")
        return response.json()

    def get_file_by_id(self, file_id: str) -> dict[str, Any]:
        """Get a specific file by ID."""
        response = self._make_request("GET", f"/files/{file_id}")
        return response.json()

    def upload_file(
        self, filename: str, content: str, content_type: str = "text/markdown"
    ) -> str | None:
        """Upload a file to Open-WebUI and return the file_id.

        Args:
            filename: Name of the file
            content: File content as string
            content_type: MIME type of the content

        Returns:
            file_id if successful, None if failed
        """
        try:
            from io import BytesIO

            # Handle both string and bytes content
            if isinstance(content, bytes):
                file_obj = BytesIO(content)
            else:
                file_obj = BytesIO(content.encode("utf-8"))

            # Prepare multipart form data
            files = {"file": (filename, file_obj, content_type)}

            # Make request without json parameter to avoid Content-Type override
            response = self._make_request("POST", "/files", files=files)

            if response and response.status_code == 200:
                result = response.json()
                return result.get("id")  # Return the file_id
            logger.error(f"Failed to upload file: {response.json() if response else 'No response'}")
            return None

        except Exception as e:
            logger.error(f"Error uploading file {filename}: {e!s}")
            return None

    def add_file_to_knowledge(self, knowledge_id: str, file_data: dict[str, Any]) -> dict[str, Any]:
        """Add a file to a knowledge item."""
        # If file_data doesn't have file_id, upload the file first
        if "file_id" not in file_data:
            # Upload the file first to get a file_id
            filename = file_data.get("filename", "")
            content = file_data.get("content", "")
            content_type = file_data.get("content_type", "text/markdown")

            file_id = self.upload_file(filename, content, content_type)
            if not file_id:
                raise ValueError(f"Failed to upload file: {filename}")

            # Create the payload with the file_id
            knowledge_payload = {
                "file_id": file_id,
                "filename": filename,
            }
        else:
            knowledge_payload = file_data

        try:
            response = self._make_request(
                "POST", f"/knowledge/{knowledge_id}/file/add", json=knowledge_payload
            )
            return response.json()
        except requests.RequestException as e:
            # Check if this is a duplicate content error
            if hasattr(e, "response") and e.response and e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("detail", "").lower()
                    if "duplicate content detected" in error_message:
                        # Return a special response indicating duplicate content
                        return {
                            "duplicate_content": True,
                            "message": "Duplicate content detected",
                            "filename": knowledge_payload.get("filename", "unknown"),
                        }
                except (ValueError, KeyError):
                    # Not JSON or missing expected fields, re-raise original exception
                    pass
            # Re-raise the original exception for other errors
            raise

    def is_duplicate_content_error(self, response_data: dict[str, Any]) -> bool:
        """Check if a response indicates duplicate content was detected.

        Args:
            response_data: Response data from add_file_to_knowledge

        Returns:
            True if the response indicates duplicate content, False otherwise
        """
        return response_data.get("duplicate_content", False) is True

    def update_file_from_knowledge(
        self, knowledge_id: str, file_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a file in a knowledge item."""
        response = self._make_request(
            "POST", f"/knowledge/{knowledge_id}/file/update", json=file_data
        )
        return response.json()

    def delete_all_files(self) -> dict[str, Any]:
        """Delete all files."""
        response = self._make_request("DELETE", "/files/all")
        return response.json()

    def get_space_details(self, space_key: str) -> dict[str, Any]:
        """Retrieve detailed information about a Confluence space.

        Args:
            space_key: The key of the space to retrieve details for.

        Returns:
            A dictionary containing space details including metadata.
        """
        response = self._make_request("GET", f"/confluence/spaces/{space_key}")
        return response.json()

    def get_ancestors(self, space_key: str, page_id: int) -> list[dict[str, Any]]:
        """Retrieve the ancestor hierarchy for a Confluence page.

        Args:
            space_key: The key of the space containing the page.
            page_id: The ID of the page to retrieve ancestors for.

        Returns:
            A list of dictionaries containing ancestor page details.
        """
        # First get the page to verify it exists in the space
        response = self._make_request("GET", f"/confluence/spaces/{space_key}/pages/{page_id}")
        if response.status_code != 200:
            # If the page doesn't exist in the space, return an empty list
            return []

        # Use the existing get_page_ancestors method to get the ancestors
        return self.get_page_ancestors(page_id)

    def get_page_ancestors(self, page_id: int) -> list[dict[str, Any]]:
        """Retrieve the ancestor hierarchy for a Confluence page.

        Args:
            page_id: The ID of the page to retrieve ancestors for.

        Returns:
            A list of dictionaries containing ancestor page details.
        """
        response = self._make_request("GET", f"/confluence/pages/{page_id}/ancestors")
        return response.json()

    def get_attachment_details(self, attachment_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a Confluence attachment.

        Args:
            attachment_id: The ID of the attachment to retrieve details for.

        Returns:
            A dictionary containing attachment details including metadata.
        """
        response = self._make_request("GET", f"/confluence/attachments/{attachment_id}")
        return response.json()

    def compile_metadata(self, page_id: int) -> dict[str, Any]:
        """Compile complete metadata for a Confluence page, including space details,
        ancestor hierarchy, and attachment details.

        Args:
            page_id: The ID of the page to compile metadata for.

        Returns:
            A dictionary containing comprehensive metadata for the page.
        """
        # Get page details
        page_response = self._make_request("GET", f"/confluence/pages/{page_id}")
        page_data = page_response.json()

        # Get space details
        space_key = page_data.get("space", {}).get("key")
        if space_key:
            space_details = self.get_space_details(space_key)
            page_data["space_details"] = space_details
        else:
            page_data["space_details"] = {}

        # Get page ancestors
        ancestors = self.get_page_ancestors(page_id)
        page_data["ancestors"] = ancestors

        # Get attachment details
        attachments = page_data.get("attachments", [])
        for attachment in attachments:
            attachment_id = attachment.get("id")
            if attachment_id:
                attachment_details = self.get_attachment_details(attachment_id)
                attachment.update(attachment_details)

        return page_data

    def test_connection(self) -> bool:
        """Test connection to Open-WebUI.

        This method tests the connection by attempting to retrieve basic metadata
        from the API. It returns True if the connection is successful, False otherwise.

        The method handles both JSON and HTML responses gracefully.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            # Try to get basic metadata to test the connection
            logger.debug("DEBUG: Starting connection test - making request to /health")
            response = self._make_request("GET", "/health")
            logger.debug(f"DEBUG: Health check response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Connection test failed with status {response.status_code}")
                return False

            # Check if the response is HTML
            content_type = response.headers.get("Content-Type", "")
            logger.debug(f"DEBUG: Health check response content-type: {content_type}")

            if "text/html" in content_type:
                logger.warning(
                    "Received HTML response from /health endpoint. "
                    "Connection considered successful for export purposes."
                )
                return True

            # Process JSON response
            try:
                status_data = response.json()
                logger.debug(f"DEBUG: Health check response JSON: {status_data}")
                logger.debug(
                    f"DEBUG: Status field value: {status_data.get('status')} (type: {type(status_data.get('status'))})"
                )

                # Check for both boolean true and string "ok" to handle API variations
                status_value = status_data.get("status")
                if status_value not in [True, "ok", "true"]:
                    error_message = status_data.get("message", "Unknown error")
                    logger.error(
                        f"Connection test failed: status='{status_value}', message='{error_message}'"
                    )
                    logger.debug(f"DEBUG: Full status_data for failed connection: {status_data}")
                    return False
            except ValueError as json_error:
                logger.error(f"Failed to parse JSON response from /health endpoint: {json_error}")
                logger.debug(f"DEBUG: Raw response text: {response.text[:500]}")
                return False

            logger.info("Connection test passed successfully")
            return True
        except Exception as e:
            logger.error(f"Connection test failed with exception: {e}")
            logger.debug(f"DEBUG: Exception type: {type(e).__name__}")
            logger.debug(f"DEBUG: Exception details: {e!s}")
            import traceback

            logger.debug(f"DEBUG: Full traceback: {traceback.format_exc()}")
            return False

    def get_attachments(self, space_key: str, page_id: int) -> list[dict[str, Any]]:
        """Retrieve attachments for a Confluence page.

        Args:
            space_key: The key of the space containing the page.
            page_id: The ID of the page to retrieve attachments for.

        Returns:
            A list of dictionaries containing attachment details.
        """
        # First get the page to verify it exists in the space
        response = self._make_request("GET", f"/confluence/spaces/{space_key}/pages/{page_id}")
        if response.status_code != 200:
            # If the page doesn't exist in the space, return an empty list
            return []

        # Get attachments for the page
        response = self._make_request("GET", f"/confluence/pages/{page_id}/attachments")
        return response.json()


def get_open_webui_client() -> OpenWebUIClient:
    """Get an authenticated Open-WebUI API client using current settings."""
    settings = get_settings()
    auth = settings.auth
    retry_config = settings.retry_config.model_dump()

    while True:
        try:
            client = OpenWebUIClient.from_auth_config(auth.open_webui, retry_config)
            # Test connection by making a simple API call
            client.get_knowledge()
            return client
        except APIKeyError as e:
            # Log the original error without redaction
            logger.error(f"API key error: {e}")
            sensitive_logger.error(f"API key error: {e}")
            print(f"Error: {e}")
            main_config_menu_loop("auth.open_webui")
            settings = get_settings()
            auth = settings.auth
        except ValueError as e:
            error_msg = str(e)
            if "API key must not be empty" in error_msg:
                logger.error("API key is empty. Please set a valid API key in the configuration.")
                print("Error: API key is empty. Please set a valid API key in the configuration.")
            elif "API key must start with 'sk-'" in error_msg:
                logger.error("Invalid API key format. API key must start with 'sk-'.")
                print("Error: Invalid API key format. API key must start with 'sk-'.")
            elif "Invalid API key" in error_msg:
                # Log the original error without redaction
                logger.error(f"Invalid API key: {error_msg}")
                sensitive_logger.error(f"Invalid API key: {error_msg}")
                print(f"Error: {error_msg}")
            else:
                # Log the original error without redaction
                logger.error(f"Open-WebUI configuration error: {error_msg}")
                print(f"Open-WebUI configuration error: {error_msg}")
            main_config_menu_loop("auth.open_webui")
            settings = get_settings()
            auth = settings.auth
        except requests.RequestException as e:
            error_msg = f"Open-WebUI connection failed: {e}"
            logger.error(error_msg)
            print(error_msg)
            main_config_menu_loop("auth.open_webui")
            settings = get_settings()
            auth = settings.auth
