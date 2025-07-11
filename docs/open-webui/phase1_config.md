# Phase 1: Configuration Extension

## Overview
Extend the existing configuration system to support Open-WebUI authentication and export settings.

## Task 1.1: Extend Configuration Schema

### Objective
Add Open-WebUI configuration fields to the existing configuration schema.

### Files to Modify
- `confluence_markdown_exporter/config/config_schema.py`
- `config/app_data.json.example`

### Requirements
- Add Open-WebUI authentication fields
- Add Open-WebUI export control fields
- Maintain backward compatibility
- Add proper validation

### Reference Implementation

#### Configuration Schema Extension
```python
# confluence_markdown_exporter/config/config_schema.py

from typing import Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class OpenWebUIAuthConfig:
    """Configuration for Open-WebUI authentication"""
    url: str = ""
    api_key: str = ""
    
    def validate(self) -> bool:
        """Validate Open-WebUI configuration"""
        if not self.url or not self.api_key:
            return False
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(self.url))

@dataclass
class OpenWebUIExportConfig:
    """Configuration for Open-WebUI export settings"""
    export_to_open_webui: bool = False
    attachment_extensions: str = "md,txt,pdf"
    batch_add: bool = True
    
    def get_extension_list(self) -> list:
        """Parse comma-separated extensions into list"""
        if not self.attachment_extensions:
            return []
        return [ext.strip().lower() for ext in self.attachment_extensions.split(',')]

# Add to existing AuthConfig class
@dataclass
class AuthConfig:
    confluence: ConfluenceAuthConfig = None
    jira: JiraAuthConfig = None
    open_webui: OpenWebUIAuthConfig = None  # New field
    
    def __post_init__(self):
        if self.confluence is None:
            self.confluence = ConfluenceAuthConfig()
        if self.jira is None:
            self.jira = JiraAuthConfig()
        if self.open_webui is None:
            self.open_webui = OpenWebUIAuthConfig()

# Add to existing ExportConfig class
@dataclass
class ExportConfig:
    output_path: str = "./"
    page_href: str = "relative"
    page_path: str = "{space_name}/{homepage_title}/{ancestor_titles}/{page_title}.md"
    attachment_href: str = "relative"
    attachment_path: str = "{space_name}/attachments/{attachment_file_id}{attachment_extension}"
    page_breadcrumbs: bool = True
    include_document_title: bool = True
    export_to_open_webui: bool = False  # New field
    open_webui_attachment_extensions: str = "md,txt,pdf"  # New field
    open_webui_batch_add: bool = True  # New field
    
    def get_open_webui_extensions(self) -> list:
        """Parse Open-WebUI attachment extensions"""
        if not self.open_webui_attachment_extensions:
            return []
        return [ext.strip().lower() for ext in self.open_webui_attachment_extensions.split(',')]

# Validation functions
def validate_open_webui_config(config: Dict[str, Any]) -> list:
    """Validate Open-WebUI specific configuration"""
    errors = []
    
    auth_config = config.get('auth', {}).get('open_webui', {})
    if auth_config.get('url') and not auth_config.get('api_key'):
        errors.append("Open-WebUI API key is required when URL is provided")
    
    export_config = config.get('export', {})
    if export_config.get('export_to_open_webui'):
        if not auth_config.get('url') or not auth_config.get('api_key'):
            errors.append("Open-WebUI URL and API key are required when export is enabled")
    
    return errors
```

#### Updated Configuration Example
```json
{
  "auth": {
    "confluence": {
      "url": "",
      "username": "",
      "api_token": "",
      "pat": ""
    },
    "jira": {
      "url": "",
      "username": "",
      "api_token": "",
      "pat": ""
    },
    "open_webui": {
      "url": "",
      "api_key": ""
    }
  },
  "export": {
    "output_path": "./",
    "page_href": "relative",
    "page_path": "{space_name}/{homepage_title}/{ancestor_titles}/{page_title}.md",
    "attachment_href": "relative",
    "attachment_path": "{space_name}/attachments/{attachment_file_id}{attachment_extension}",
    "page_breadcrumbs": true,
    "include_document_title": true,
    "export_to_open_webui": false,
    "open_webui_attachment_extensions": "md,txt,pdf",
    "open_webui_batch_add": true
  },
  "retry_config": {
    "backoff_and_retry": true,
    "backoff_factor": 2,
    "max_backoff_seconds": 60,
    "max_backoff_retries": 5,
    "retry_status_codes": [413, 429, 502, 503, 504]
  }
}
```

### Testing Requirements
```python
# tests/test_config_schema.py

import pytest
from confluence_markdown_exporter.config.config_schema import (
    OpenWebUIAuthConfig, 
    validate_open_webui_config
)

class TestOpenWebUIConfig:
    def test_valid_url_validation(self):
        config = OpenWebUIAuthConfig(
            url="https://openwebui.example.com",
            api_key="test-key"
        )
        assert config.validate() == True
    
    def test_invalid_url_validation(self):
        config = OpenWebUIAuthConfig(
            url="not-a-url",
            api_key="test-key"
        )
        assert config.validate() == False
    
    def test_missing_api_key_validation(self):
        config = OpenWebUIAuthConfig(
            url="https://openwebui.example.com",
            api_key=""
        )
        assert config.validate() == False
    
    def test_extension_list_parsing(self):
        config = ExportConfig()
        config.open_webui_attachment_extensions = "md, txt, pdf, docx"
        extensions = config.get_open_webui_extensions()
        assert extensions == ["md", "txt", "pdf", "docx"]
    
    def test_config_validation(self):
        config = {
            "auth": {
                "open_webui": {
                    "url": "https://test.com",
                    "api_key": ""
                }
            },
            "export": {
                "export_to_open_webui": True
            }
        }
        errors = validate_open_webui_config(config)
        assert len(errors) > 0
        assert "API key is required" in errors[0]
```

## Task 1.2: Update Configuration Menu

### Objective
Extend the interactive configuration menu to include Open-WebUI settings.

### Files to Modify
- `confluence_markdown_exporter/config/config_manager.py`

### Requirements
- Add Open-WebUI authentication section
- Add Open-WebUI export settings
- Maintain existing menu structure
- Add proper validation and error handling

### Reference Implementation

```python
# confluence_markdown_exporter/config/config_manager.py

from typing import Dict, Any, Optional
from .config_schema import validate_open_webui_config
import requests

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
    
    def show_auth_menu(self):
        """Display authentication configuration menu"""
        while True:
            print("\n=== Authentication Configuration ===")
            print("1. Confluence")
            print("2. Jira")
            print("3. Open-WebUI")  # New option
            print("4. Back to main menu")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                self.configure_confluence_auth()
            elif choice == "2":
                self.configure_jira_auth()
            elif choice == "3":
                self.configure_open_webui_auth()  # New method
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")
    
    def configure_open_webui_auth(self):
        """Configure Open-WebUI authentication"""
        print("\n=== Open-WebUI Authentication ===")
        current_config = self.config.get('auth', {}).get('open_webui', {})
        
        print(f"Current URL: {current_config.get('url', 'Not set')}")
        print(f"Current API Key: {'***' if current_config.get('api_key') else 'Not set'}")
        
        print("\nEnter new values (press Enter to keep current):")
        
        # URL configuration
        url = input("Open-WebUI URL: ").strip()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            if self.validate_open_webui_url(url):
                self.set_config_value('auth.open_webui.url', url)
                print("✓ URL updated successfully")
            else:
                print("✗ Invalid URL format")
                return
        
        # API Key configuration
        api_key = input("API Key: ").strip()
        if api_key:
            self.set_config_value('auth.open_webui.api_key', api_key)
            print("✓ API Key updated successfully")
        
        # Test connection if both values are set
        if self.config.get('auth', {}).get('open_webui', {}).get('url') and \
           self.config.get('auth', {}).get('open_webui', {}).get('api_key'):
            if self.test_open_webui_connection():
                print("✓ Connection test successful")
            else:
                print("✗ Connection test failed - please check your credentials")
    
    def show_export_menu(self):
        """Display export configuration menu"""
        while True:
            print("\n=== Export Configuration ===")
            print("1. Output Settings")
            print("2. Path Templates")
            print("3. Open-WebUI Export")  # New option
            print("4. Back to main menu")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                self.configure_output_settings()
            elif choice == "2":
                self.configure_path_templates()
            elif choice == "3":
                self.configure_open_webui_export()  # New method
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")
    
    def configure_open_webui_export(self):
        """Configure Open-WebUI export settings"""
        print("\n=== Open-WebUI Export Settings ===")
        current_config = self.config.get('export', {})
        
        print(f"Export to Open-WebUI: {current_config.get('export_to_open_webui', False)}")
        print(f"Attachment Extensions: {current_config.get('open_webui_attachment_extensions', 'md,txt,pdf')}")
        print(f"Batch Add: {current_config.get('open_webui_batch_add', True)}")
        
        # Export toggle
        enable_export = input("\nEnable export to Open-WebUI? (y/n): ").strip().lower()
        if enable_export in ['y', 'yes', 'true', '1']:
            self.set_config_value('export.export_to_open_webui', True)
            print("✓ Open-WebUI export enabled")
            
            # Attachment extensions
            extensions = input("Attachment extensions (comma-separated, e.g., md,txt,pdf): ").strip()
            if extensions:
                self.set_config_value('export.open_webui_attachment_extensions', extensions)
                print("✓ Attachment extensions updated")
            
            # Batch add setting
            batch_add = input("Use batch add for better performance? (y/n): ").strip().lower()
            if batch_add in ['y', 'yes', 'true', '1']:
                self.set_config_value('export.open_webui_batch_add', True)
            else:
                self.set_config_value('export.open_webui_batch_add', False)
            print("✓ Batch add setting updated")
            
        elif enable_export in ['n', 'no', 'false', '0']:
            self.set_config_value('export.export_to_open_webui', False)
            print("✓ Open-WebUI export disabled")
    
    def validate_open_webui_url(self, url: str) -> bool:
        """Validate Open-WebUI URL format"""
        try:
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            return bool(url_pattern.match(url))
        except Exception:
            return False
    
    def test_open_webui_connection(self) -> bool:
        """Test connection to Open-WebUI"""
        try:
            url = self.config.get('auth', {}).get('open_webui', {}).get('url')
            api_key = self.config.get('auth', {}).get('open_webui', {}).get('api_key')
            
            if not url or not api_key:
                return False
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Test with knowledge endpoint
            response = requests.get(f"{url}/api/v1/knowledge/", headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test error: {e}")
            return False
    
    def validate_current_config(self) -> bool:
        """Validate current configuration including Open-WebUI"""
        errors = []
        
        # Existing validation...
        
        # Open-WebUI validation
        open_webui_errors = validate_open_webui_config(self.config)
        errors.extend(open_webui_errors)
        
        if errors:
            print("\n=== Configuration Errors ===")
            for error in errors:
                print(f"✗ {error}")
            return False
        
        return True
```

### Testing Requirements
```python
# tests/test_config_manager.py

import pytest
from unittest.mock import patch, MagicMock
from confluence_markdown_exporter.config.config_manager import ConfigManager

class TestConfigManagerOpenWebUI:
    def test_open_webui_url_validation(self):
        config_manager = ConfigManager("test_config.json")
        
        # Valid URLs
        assert config_manager.validate_open_webui_url("https://openwebui.example.com") == True
        assert config_manager.validate_open_webui_url("http://localhost:8080") == True
        assert config_manager.validate_open_webui_url("https://192.168.1.100:3000") == True
        
        # Invalid URLs
        assert config_manager.validate_open_webui_url("not-a-url") == False
        assert config_manager.validate_open_webui_url("") == False
    
    @patch('requests.get')
    def test_open_webui_connection_test(self, mock_get):
        config_manager = ConfigManager("test_config.json")
        config_manager.config = {
            'auth': {
                'open_webui': {
                    'url': 'https://test.com',
                    'api_key': 'test-key'
                }
            }
        }
        
        # Successful connection
        mock_get.return_value.status_code = 200
        assert config_manager.test_open_webui_connection() == True
        
        # Failed connection
        mock_get.return_value.status_code = 401
        assert config_manager.test_open_webui_connection() == False
    
    def test_config_validation_with_open_webui(self):
        config_manager = ConfigManager("test_config.json")
        config_manager.config = {
            'auth': {
                'open_webui': {
                    'url': 'https://test.com',
                    'api_key': ''
                }
            },
            'export': {
                'export_to_open_webui': True
            }
        }
        
        assert config_manager.validate_current_config() == False
```

## Deliverables

1. **Updated Configuration Schema** (`config_schema.py`)
   - New Open-WebUI authentication and export configuration classes
   - Validation methods for URLs and API keys
   - Extension parsing functionality

2. **Updated Configuration Menu** (`config_manager.py`)
   - New Open-WebUI authentication section
   - New Open-WebUI export settings section
   - Connection testing functionality
   - Enhanced validation

3. **Updated Configuration Example** (`app_data.json.example`)
   - Added Open-WebUI authentication fields
   - Added Open-WebUI export settings
   - Proper default values

4. **Test Suite**
   - Unit tests for configuration validation
   - Integration tests for menu navigation
   - Connection testing validation

## Success Criteria

- [ ] Configuration schema supports all Open-WebUI fields
- [ ] Interactive menu includes Open-WebUI options
- [ ] URL and API key validation works correctly
- [ ] Connection testing functions properly
- [ ] All tests pass
- [ ] Backward compatibility maintained
- [ ] Configuration validation includes Open-WebUI checks
