# Phase 2: Open-WebUI API Client

## Overview
Implement the Open-WebUI API client with comprehensive support for knowledge base and file operations.

## Task 2.1: Create Open-WebUI API Client

### Objective
Implement a robust API client for Open-WebUI with support for knowledge bases, file operations, and proper error handling.

### Files to Create
- `confluence_markdown_exporter/clients/open_webui_client.py`
- `confluence_markdown_exporter/clients/__init__.py` (update)

### Requirements
- Bearer token authentication
- Knowledge base operations (create, get, list)
- File operations (search, create, update, delete)
- File registration to knowledge base
- Batch operations support
- Comprehensive error handling
- Progress reporting
- Proper logging

### Reference Implementation

```python
# confluence_markdown_exporter/clients/open_webui_client.py

import requests
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)

@dataclass
class OpenWebUIFile:
    """Represents a file in Open-WebUI"""
    id: str
    filename: str
    created_at: str
    updated_at: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenWebUIFile':
        return cls(
            id=data['id'],
            filename=data['filename'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            size=data.get('size'),
            content_type=data.get('content_type')
        )

@dataclass
class OpenWebUIKnowledge:
    """Represents a knowledge base in Open-WebUI"""
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenWebUIKnowledge':
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )

class OpenWebUIClientError(Exception):
    """Exception raised for Open-WebUI API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class OpenWebUIClient:
    """Client for interacting with Open-WebUI API"""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """Initialize the Open-WebUI client
        
        Args:
            base_url: Base URL of the Open-WebUI instance
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"Initialized Open-WebUI client for {self.base_url}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = urljoin(self.base_url, endpoint)
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            response_data = None
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    response_data = e.response.json()
                except:
                    response_data = {'error': e.response.text}
            
            raise OpenWebUIClientError(
                f"API request failed: {str(e)}", 
                status_code=status_code,
                response_data=response_data
            )
    
    def test_connection(self) -> bool:
        """Test connection to Open-WebUI API"""
        try:
            response = self._make_request('GET', '/api/v1/knowledge/')
            logger.info("Connection test successful")
            return True
        except OpenWebUIClientError as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    # Knowledge Base Operations
    
    def list_knowledge_bases(self) -> List[OpenWebUIKnowledge]:
        """List all knowledge bases"""
        try:
            response = self._make_request('GET', '/api/v1/knowledge/')
            knowledge_bases = []
            
            for kb_data in response.json():
                knowledge_bases.append(OpenWebUIKnowledge.from_dict(kb_data))
            
            logger.info(f"Found {len(knowledge_bases)} knowledge bases")
            return knowledge_bases
        except OpenWebUIClientError as e:
            logger.error(f"Failed to list knowledge bases: {e}")
            raise
    
    def get_knowledge_base(self, knowledge_id: str) -> Optional[OpenWebUIKnowledge]:
        """Get knowledge base by ID"""
        try:
            response = self._make_request('GET', f'/api/v1/knowledge/{knowledge_id}')
            return OpenWebUIKnowledge.from_dict(response.json())
        except OpenWebUIClientError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Failed to get knowledge base {knowledge_id}: {e}")
            raise
    
    def find_knowledge_base_by_name(self, name: str) -> Optional[OpenWebUIKnowledge]:
        """Find knowledge base by name"""
        try:
            knowledge_bases = self.list_knowledge_bases()
            for kb in knowledge_bases:
                if kb.name == name:
                    return kb
            return None
        except OpenWebUIClientError as e:
            logger.error(f"Failed to find knowledge base '{name}': {e}")
            raise
    
    def create_knowledge_base(self, name: str, description: str = "") -> OpenWebUIKnowledge:
        """Create a new knowledge base"""
        try:
            data = {
                'name': name,
                'description': description
            }
            response = self._make_request('POST', '/api/v1/knowledge/create', json=data)
            
            knowledge_base = OpenWebUIKnowledge.from_dict(response.json())
            logger.info(f"Created knowledge base: {name} (ID: {knowledge_base.id})")
            return knowledge_base
        except OpenWebUIClientError as e:
            logger.error(f"Failed to create knowledge base '{name}': {e}")
            raise
    
    def create_or_get_knowledge_base(self, name: str, description: str = "") -> OpenWebUIKnowledge:
        """Create knowledge base if it doesn't exist, otherwise return existing one"""
        try:
            # Try to find existing knowledge base
            existing_kb = self.find_knowledge_base_by_name(name)
            if existing_kb:
                logger.info(f"Found existing knowledge base: {name}")
                return existing_kb
            
            # Create new knowledge base
            return self.create_knowledge_base(name, description)
        except OpenWebUIClientError as e:
            logger.error(f"Failed to create or get knowledge base '{name}': {e}")
            raise
    
    # File Operations
    
    def search_files(self, filename: str = "*") -> List[OpenWebUIFile]:
        """Search for files by filename pattern"""
        try:
            params = {'filename': filename}
            response = self._make_request('GET', '/api/v1/files/search', params=params)
            
            files = []
            for file_data in response.json():
                files.append(OpenWebUIFile.from_dict(file_data))
            
            logger.info(f"Found {len(files)} files matching '{filename}'")
            return files
        except OpenWebUIClientError as e:
            logger.error(f"Failed to search files: {e}")
            raise
    
    def find_file_by_name(self, filename: str) -> Optional[OpenWebUIFile]:
        """Find file by exact filename"""
        try:
            files = self.search_files(filename)
            for file in files:
                if file.filename == filename:
                    return file
            return None
        except OpenWebUIClientError as e:
            logger.error(f"Failed to find file '{filename}': {e}")
            raise
    
    def upload_file(self, filename: str, content: Union[str, bytes], content_type: str = 'text/markdown') -> OpenWebUIFile:
        """Upload a file to Open-WebUI"""
        try:
            # Prepare file data
            files = {
                'file': (filename, content, content_type)
            }
            
            # Remove content-type header for file upload
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.post(
                f"{self.base_url}/api/v1/files/",
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            file_obj = OpenWebUIFile.from_dict(response.json())
            logger.info(f"Uploaded file: {filename} (ID: {file_obj.id})")
            return file_obj
        except requests.RequestException as e:
            logger.error(f"Failed to upload file '{filename}': {e}")
            raise OpenWebUIClientError(f"Failed to upload file: {str(e)}")
    
    def update_file_content(self, file_id: str, content: Union[str, bytes]) -> bool:
        """Update file content by ID"""
        try:
            data = {'content': content}
            response = self._make_request('POST', f'/api/v1/files/{file_id}/data/content/update', json=data)
            logger.info(f"Updated file content: {file_id}")
            return True
        except OpenWebUIClientError as e:
            logger.error(f"Failed to update file content {file_id}: {e}")
            raise
    
    def create_or_update_file(self, filename: str, content: Union[str, bytes], content_type: str = 'text/markdown') -> OpenWebUIFile:
        """Create file if it doesn't exist, otherwise update existing one"""
        try:
            # Check if file exists
            existing_file = self.find_file_by_name(filename)
            
            if existing_file:
                # Update existing file
                self.update_file_content(existing_file.id, content)
                logger.info(f"Updated existing file: {filename}")
                return existing_file
            else:
                # Create new file
                return self.upload_file(filename, content, content_type)
        except OpenWebUIClientError as e:
            logger.error(f"Failed to create or update file '{filename}': {e}")
            raise
    
    # Knowledge Base File Operations
    
    def add_file_to_knowledge(self, knowledge_id: str, file_id: str) -> bool:
        """Add a file to a knowledge base"""
        try:
            data = {'file_id': file_id}
            response = self._make_request('POST', f'/api/v1/knowledge/{knowledge_id}/file/add', json=data)
            logger.info(f"Added file {file_id} to knowledge base {knowledge_id}")
            return True
        except OpenWebUIClientError as e:
            logger.error(f"Failed to add file {file_id} to knowledge base {knowledge_id}: {e}")
            raise
    
    def batch_add_files_to_knowledge(self, knowledge_id: str, file_ids: List[str]) -> bool:
        """Add multiple files to a knowledge base in batch"""
        try:
            data = [{'file_id': file_id} for file_id in file_ids]
            response = self._make_request('POST', f'/api/v1/knowledge/{knowledge_id}/files/batch/add', json=data)
            logger.info(f"Added {len(file_ids)} files to knowledge base {knowledge_id} in batch")
            return True
        except OpenWebUIClientError as e:
            logger.error(f"Failed to batch add files to knowledge base {knowledge_id}: {e}")
            raise
    
    def get_knowledge_files(self, knowledge_id: str) -> List[OpenWebUIFile]:
        """Get all files in a knowledge base"""
        try:
            response = self._make_request('GET', f'/api/v1/knowledge/{knowledge_id}')
            knowledge_data = response.json()
            
            files = []
            if 'files' in knowledge_data:
                for file_data in knowledge_data['files']:
                    files.append(OpenWebUIFile.from_dict(file_data))
            
            logger.info(f"Found {len(files)} files in knowledge base {knowledge_id}")
            return files
        except OpenWebUIClientError as e:
            logger.error(f"Failed to get files for knowledge base {knowledge_id}: {e}")
            raise
    
    # Utility Methods
    
    def get_file_content_type(self, filename: str) -> str:
        """Determine content type based on file extension"""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        content_types = {
            'md': 'text/markdown',
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'json': 'application/json',
            'xml': 'application/xml',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'py': 'text/plain',
            'java': 'text/plain',
            'cpp': 'text/plain',
            'c': 'text/plain'
        }
        
        return content_types.get(extension, 'text/plain')
    
    def cleanup_filename(self, filename: str) -> str:
        """Clean up filename for Open-WebUI compatibility"""
        import re
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple consecutive underscores
        filename = re.sub(r'_+', '_', filename)
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        return filename
```

### Testing Requirements

```python
# tests/test_open_webui_client.py

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from confluence_markdown_exporter.clients.open_webui_client import (
    OpenWebUIClient, 
    OpenWebUIClientError,
    OpenWebUIKnowledge,
    OpenWebUIFile
)

class TestOpenWebUIClient:
    @pytest.fixture
    def client(self):
        return OpenWebUIClient("https://test.com", "test-api-key")
    
    @pytest.fixture
    def mock_response(self):
        response = Mock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        return response
    
    def test_client_initialization(self, client):
        assert client.base_url == "https://test.com"
        assert client.api_key == "test-api-key"
        assert client.timeout == 30
        assert "Bearer test-api-key" in client.session.headers['Authorization']
    
    @patch('requests.Session.request')
    def test_connection_test_success(self, mock_request, client, mock_response):
        mock_request.return_value = mock_response
        mock_response.json.return_value = []
        
        result = client.test_connection()
        assert result == True
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_connection_test_failure(self, mock_request, client):
        mock_request.side_effect = requests.RequestException("Connection failed")
        
        result = client.test_connection()
        assert result == False
    
    @patch('requests.Session.request')
    def test_list_knowledge_bases(self, mock_request, client, mock_response):
        mock_response.json.return_value = [
            {
                'id': 'kb1',
                'name': 'Test KB',
                'description': 'Test Description',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_request.return_value = mock_response
        
        knowledge_bases = client.list_knowledge_bases()
        assert len(knowledge_bases) == 1
        assert knowledge_bases[0].name == 'Test KB'
    
    @patch('requests.Session.request')
    def test_create_knowledge_base(self, mock_request, client, mock_response):
        mock_response.json.return_value = {
            'id': 'kb1',
            'name': 'New KB',
            'description': 'New Description',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        kb = client.create_knowledge_base('New KB', 'New Description')
        assert kb.name == 'New KB'
        assert kb.description == 'New Description'
    
    @patch('requests.Session.request')
    def test_find_knowledge_base_by_name(self, mock_request, client, mock_response):
        mock_response.json.return_value = [
            {
                'id': 'kb1',
                'name': 'Test KB',
                'description': 'Test Description',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_request.return_value = mock_response
        
        kb = client.find_knowledge_base_by_name('Test KB')
        assert kb is not None
        assert kb.name == 'Test KB'
        
        kb_not_found = client.find_knowledge_base_by_name('Non-existent KB')
        assert kb_not_found is None
    
    @patch('requests.post')
    def test_upload_file(self, mock_post, client, mock_response):
        mock_response.json.return_value = {
            'id': 'file1',
            'filename': 'test.md',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_post.return_value = mock_response
        
        file_obj = client.upload_file('test.md', 'content', 'text/markdown')
        assert file_obj.filename == 'test.md'
        assert file_obj.id == 'file1'
    
    @patch('requests.Session.request')
    def test_update_file_content(self, mock_request, client, mock_response):
        mock_request.return_value = mock_response
        
        result = client.update_file_content('file1', 'new content')
        assert result == True
    
    @patch('requests.Session.request')
    def test_search_files(self, mock_request, client, mock_response):
        mock_response.json.return_value = [
            {
                'id': 'file1',
                'filename': 'test.md',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_request.return_value = mock_response
        
        files = client.search_files('*.md')
        assert len(files) == 1
        assert files[0].filename == 'test.md'
    
    def test_get_file_content_type(self, client):
        assert client.get_file_content_type('test.md') == 'text/markdown'
        assert client.get_file_content_type('test.txt') == 'text/plain'
        assert client.get_file_content_type('test.pdf') == 'application/pdf'
        assert client.get_file_content_type('test.unknown') == 'text/plain'
    
    def test_cleanup_filename(self, client):
        assert client.cleanup_filename('test<>file.md') == 'test__file.md'
        assert client.cleanup_filename('test/file\\name.md') == 'test_file_name.md'
        assert client.cleanup_filename('___test___file___.md') == 'test___file.md'
    
    @patch('requests.Session.request')
    def test_batch_add_files_to_knowledge(self, mock_request, client, mock_response):
        mock_request.return_value = mock_response
        
        result = client.batch_add_files_to_knowledge('kb1', ['file1', 'file2'])
        assert result == True
        
        # Verify the request was made with correct data
        args, kwargs = mock_request.call_args
        assert kwargs['json'] == [{'file_id': 'file1'}, {'file_id': 'file2'}]
    
    @patch('requests.Session.request')
    def test_error_handling(self, mock_request, client):
        # Setup mock to raise an exception
        mock_request.side_effect = requests.RequestException("API Error")
        
        with pytest.raises(OpenWebUIClientError) as exc_info:
            client.list_knowledge_bases()
        
        assert "API request failed" in str(exc_info.value)
```

## Task 2.2: Add API Response Models

### Objective
Create comprehensive data models for Open-WebUI API responses to ensure type safety and easy data manipulation.

### Files to Create
- `confluence_markdown_exporter/models/open_webui_models.py`
- `confluence_markdown_exporter/models/__init__.py` (update)

### Requirements
- Data models for all API responses
- Proper serialization/deserialization
- Validation methods
- Type hints throughout

### Reference Implementation

```python
# confluence_markdown_exporter/models/open_webui_models.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

@dataclass
class BaseModel:
    """Base model with common functionality"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    def to_json(self) -> str:
        """Convert model to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model from dictionary"""
        # Filter out keys that don't match the dataclass fields
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

@dataclass
class OpenWebUIFile(BaseModel):
    """Represents a file in Open-WebUI"""
    id: str
    filename: str
    created_at: str
    updated_at: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    user_id: Optional[str] = None
    hash: Optional[str] = None
    
    def get_extension(self) -> str:
        """Get file extension"""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
    
    def is_text_file(self) -> bool:
        """Check if file is a text file"""
        text_extensions = {'md', 'txt', 'json', 'xml', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c'}
        return self.get_extension() in text_extensions
    
    def get_created_datetime(self) -> Optional[datetime]:
        """Get created datetime as datetime object"""
        try:
            return datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def get_updated_datetime(self) -> Optional[datetime]:
        """Get updated datetime as datetime object"""
        try:
            return datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

@dataclass
class OpenWebUIKnowledge(BaseModel):
    """Represents a knowledge base in Open-WebUI"""
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    user_id: Optional[str] = None
    files: List[OpenWebUIFile] = field(default_factory=list)
    
    def get_created_datetime(self) -> Optional[datetime]:
        """Get created datetime as datetime object"""
        try:
            return datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def get_updated_datetime(self) -> Optional[datetime]:
        """Get updated datetime as datetime object"""
        try:
            return datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def get_file_count(self) -> int:
        """Get number of files in knowledge base"""
        return len(self.files)
    
    def find_file_by_name(self, filename: str) -> Optional[OpenWebUIFile]:
        """Find file by filename"""
        for file in self.files:
            if file.filename == filename:
                return file
        return None
    
    def get_files_by_extension(self, extension: str) -> List[OpenWebUIFile]:
        """Get files by extension"""
        return [file for file in self.files if file.get_extension() == extension.lower()]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenWebUIKnowledge':
        """Create knowledge base from dictionary"""
        files = []
        if 'files' in data:
            files = [OpenWebUIFile.from_dict(file_data) for file_data in data['files']]
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            user_id=data.get('user_id'),
            files=files
        )

@dataclass
class OpenWebUIFileUploadResponse(BaseModel):
    """Response from file upload operation"""
    file: OpenWebUIFile
    success: bool = True
    message: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenWebUIFileUploadResponse':
        """Create upload response from dictionary"""
        return cls(
            file=OpenWebUIFile.from_dict(data),
            success=True,
            message="File uploaded successfully"
        )

@dataclass
class OpenWebUIKnowledgeCreateResponse(BaseModel):
    """Response from knowledge base creation"""
    knowledge: OpenWebUIKnowledge
    success: bool = True
    message: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenWebUIKnowledgeCreateResponse':
        """Create knowledge creation response from dictionary"""
        return cls(
            knowledge=OpenWebUIKnowledge.from_dict(data),
            success=True,
            message="Knowledge base created successfully"
        )

@dataclass
class OpenWebUIBatchOperation(BaseModel):
    """Represents a batch operation result"""
    total_files: int
    successful_files: int
    failed_files: int
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.successful_files / self.total_files) * 100
    
    def is_complete_success(self) -> bool:
        """Check if all files were processed successfully"""
        return self.failed_files == 0
    
    def add_error(self, error: str):
        """Add error to the batch operation"""
        self.errors.append(error)
        self.failed_files += 1

@dataclass
class OpenWebUIExportSummary(BaseModel):
    """Summary of export operation"""
    knowledge_base_name: str
    knowledge_base_id: str
    total_pages: int
    total_attachments: int
    successful_pages: int
    successful_attachments: int
    failed_pages: int
    failed_attachments: int
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def total_files(self) -> int:
        """Total number of files processed"""
        return self.total_pages + self.total_attachments
    
    @property
    def total_successful(self) -> int:
        """Total number of successful uploads"""
        return self.successful_pages + self.successful_attachments
    
    @property
    def total_failed(self) -> int:
        """Total number of failed uploads"""
        return self.failed_pages + self.failed_attachments
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_files == 0:
            return 0.0
        return (self.total_successful / self.total_files) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def add_page_success(self):
        """Record successful page upload"""
        self.successful_pages += 1
    
    def add_page_failure(self, error: str):
        """Record failed page upload"""
        self.failed_pages += 1
        self.errors.append(f"Page upload failed: {error}")
    
    def add_attachment_success(self):
        """Record successful attachment upload"""
        self.successful_attachments += 1
    
    def add_attachment_failure(self, error: str):
        """Record failed attachment upload"""
        self.failed_attachments += 1
        self.errors.append(f"Attachment upload failed: {error}")
    
    def get_summary_text(self) -> str:
        """Get formatted summary text"""
        summary = [
            f"=== Export Summary ===",
            f"Knowledge Base: {self.knowledge_base_name} ({self.knowledge_base_id})",
            f"Total Files: {self.total_files}",
            f"  - Pages: {self.total_pages}",
            f"  - Attachments: {self.total_attachments}",
            f"Successful: {self.total_successful} ({self.success_rate:.1f}%)",
            f"  - Pages: {self.successful_pages}",
            f"  - Attachments: {self.successful_attachments}",
            f"Failed: {self.total_failed}",
            f"  - Pages: {self.failed_pages}",
            f"  - Attachments: {self.failed_attachments}"
        ]
        
        if self.duration:
            summary.append(f"Duration: {self.duration:.2f} seconds")
        
        if self.errors:
            summary.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[-5:]:  # Show last 5 errors
                summary.append(f"  - {error}")
            if len(self.errors) > 5:
                summary.append(f"  ... and {len(self.errors) - 5} more errors")
        
        return "\n".join(summary)

# Model registry for easy access
MODEL_REGISTRY = {
    'file': OpenWebUIFile,
    'knowledge': OpenWebUIKnowledge,
    'file_upload_response': OpenWebUIFileUploadResponse,
    'knowledge_create_response': OpenWebUIKnowledgeCreateResponse,
    'batch_operation': OpenWebUIBatchOperation,
    'export_summary': OpenWebUIExportSummary
}

def get_model(model_name: str) -> Optional[type]:
    """Get model class by name"""
    return MODEL_REGISTRY.get(model_name)
```

### Testing Requirements

```python
# tests/test_open_webui_models.py

import pytest
from datetime import datetime
from confluence_markdown_exporter.models.open_webui_models import (
    OpenWebUIFile,
    OpenWebUIKnowledge,
    OpenWebUIExportSummary,
    OpenWebUIBatchOperation
)

class TestOpenWebUIModels:
    def test_file_model_creation(self):
        file_data = {
            'id': 'file1',
            'filename': 'test.md',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'size': 1024,
            'content_type': 'text/markdown'
        }
        
        file_obj = OpenWebUIFile.from_dict(file_data)
        assert file_obj.id == 'file1'
        assert file_obj.filename == 'test.md'
        assert file_obj.size == 1024
    
    def test_file_extension_methods(self):
        file_obj = OpenWebUIFile(
            id='file1',
            filename='test.md',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z'
        )
        
        assert file_obj.get_extension() == 'md'
        assert file_obj.is_text_file() == True
    
    def test_knowledge_base_model(self):
        kb_data = {
            'id': 'kb1',
            'name': 'Test KB',
            'description': 'Test Description',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'files': [
                {
                    'id': 'file1',
                    'filename': 'test.md',
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                }
            ]
        }
        
        kb = OpenWebUIKnowledge.from_dict(kb_data)
        assert kb.name == 'Test KB'
        assert kb.get_file_count() == 1
        assert kb.find_file_by_name('test.md') is not None
    
    def test_export_summary_calculations(self):
        summary = OpenWebUIExportSummary(
            knowledge_base_name='Test KB',
            knowledge_base_id='kb1',
            total_pages=10,
            total_attachments=5,
            successful_pages=8,
            successful_attachments=4,
            failed_pages=2,
            failed_attachments=1
        )
        
        assert summary.total_files == 15
        assert summary.total_successful == 12
        assert summary.total_failed == 3
        assert summary.success_rate == 80.0
    
    def test_batch_operation_tracking(self):
        batch_op = OpenWebUIBatchOperation(
            total_files=5,
            successful_files=3,
            failed_files=2
        )
        
        assert batch_op.success_rate == 60.0
        assert batch_op.is_complete_success() == False
        
        batch_op.add_error("File too large")
        assert len(batch_op.errors) == 1
        assert batch_op.failed_files == 3
    
    def test_datetime_conversion(self):
        file_obj = OpenWebUIFile(
            id='file1',
            filename='test.md',
            created_at='2024-01-01T10:30:00Z',
            updated_at='2024-01-01T10:30:00Z'
        )
        
        created_dt = file_obj.get_created_datetime()
        assert created_dt is not None
        assert created_dt.year == 2024
        assert created_dt.month == 1
        assert created_dt.day == 1
    
    def test_model_serialization(self):
        file_obj = OpenWebUIFile(
            id='file1',
            filename='test.md',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z'
        )
        
        file_dict = file_obj.to_dict()
        assert 'id' in file_dict
        assert 'filename' in file_dict
        
        json_str = file_obj.to_json()
        assert 'file1' in json_str
        assert 'test.md' in json_str
```

## Deliverables

1. **Open-WebUI API Client** (`open_webui_client.py`)
   - Complete API client with all required operations
   - Comprehensive error handling
   - Progress reporting and logging
   - Batch operation support

2. **API Response Models** (`open_webui_models.py`)
   - Type-safe data models for all API responses
   - Utility methods for common operations
   - Serialization/deserialization support

3. **Test Suite**
   - Unit tests for all client methods
   - Mock-based testing for API interactions
   - Model validation and serialization tests
   - Error handling and edge case testing

## Success Criteria

- [ ] API client successfully connects to Open-WebUI
- [ ] All knowledge base operations work correctly
- [ ] File upload, search, and update operations function properly
- [ ] Batch operations handle multiple files efficiently
- [ ] Error handling provides meaningful feedback
- [ ] Progress reporting works as specified
- [ ] All models serialize/deserialize correctly
- [ ] Test coverage exceeds 90%
- [ ] Client handles connection failures gracefully
- [ ] File content type detection works for all supported formats
