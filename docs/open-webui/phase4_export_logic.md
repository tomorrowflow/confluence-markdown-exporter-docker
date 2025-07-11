# Phase 4: File Processing and Export Logic

## Overview
Implement the main export logic for Open-WebUI, including file filtering, processing, and upload management with proper progress reporting.

## Task 4.1: Create Attachment Filter

### Objective
Create a component to filter attachments based on file extensions as specified in the configuration.

### Files to Create
- `confluence_markdown_exporter/processors/attachment_filter.py`
- `confluence_markdown_exporter/processors/__init__.py` (update)

### Requirements
- Parse comma-separated extension configuration
- Case-insensitive matching
- Support for wildcard patterns
- Validation of extension lists
- Logging of filter decisions

### Reference Implementation

```python
# confluence_markdown_exporter/processors/attachment_filter.py

import logging
import re
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """Result of attachment filtering"""
    should_process: bool
    reason: str
    matched_extension: Optional[str] = None

class AttachmentFilter:
    """Filters attachments based on file extensions and other criteria"""
    
    def __init__(self, allowed_extensions: str = "md,txt,pdf", max_file_size_mb: int = 10):
        """Initialize the attachment filter
        
        Args:
            allowed_extensions: Comma-separated list of allowed extensions
            max_file_size_mb: Maximum file size in MB (0 for no limit)
        """
        self.allowed_extensions = self._parse_extensions(allowed_extensions)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb > 0 else 0
        
        logger.info(f"Initialized attachment filter with extensions: {self.allowed_extensions}")
        if self.max_file_size_bytes > 0:
            logger.info(f"Maximum file size: {max_file_size_mb}MB")
    
    def _parse_extensions(self, extensions_str: str) -> Set[str]:
        """Parse comma-separated extensions string
        
        Args:
            extensions_str: Comma-separated extension list
            
        Returns:
            Set of lowercase extensions
        """
        if not extensions_str:
            return set()
        
        extensions = set()
        for ext in extensions_str.split(','):
            ext = ext.strip().lower()
            if ext:
                # Remove leading dot if present
                ext = ext.lstrip('.')
                extensions.add(ext)
        
        return extensions
    
    def should_process_attachment(self, filename: str, file_size: Optional[int] = None) -> FilterResult:
        """Check if an attachment should be processed
        
        Args:
            filename: The attachment filename
            file_size: File size in bytes (optional)
            
        Returns:
            FilterResult indicating whether to process the file
        """
        try:
            # Check if we have any allowed extensions
            if not self.allowed_extensions:
                return FilterResult(
                    should_process=False,
                    reason="No allowed extensions configured"
                )
            
            # Get file extension
            file_extension = self._get_file_extension(filename)
            
            # Check if extension is allowed
            if file_extension not in self.allowed_extensions:
                return FilterResult(
                    should_process=False,
                    reason=f"Extension '{file_extension}' not in allowed list: {sorted(self.allowed_extensions)}"
                )
            
            # Check file size if provided and limit is set
            if file_size is not None and self.max_file_size_bytes > 0:
                if file_size > self.max_file_size_bytes:
                    max_mb = self.max_file_size_bytes / (1024 * 1024)
                    actual_mb = file_size / (1024 * 1024)
                    return FilterResult(
                        should_process=False,
                        reason=f"File size {actual_mb:.2f}MB exceeds limit of {max_mb:.2f}MB"
                    )
            
            return FilterResult(
                should_process=True,
                reason="File passes all filters",
                matched_extension=file_extension
            )
            
        except Exception as e:
            logger.error(f"Error filtering attachment '{filename}': {e}")
            return FilterResult(
                should_process=False,
                reason=f"Error during filtering: {str(e)}"
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename
        
        Args:
            filename: The filename
            
        Returns:
            Lowercase file extension without dot
        """
        if not filename or '.' not in filename:
            return ''
        
        return filename.split('.')[-1].lower()
    
    def filter_attachments(self, attachments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Filter a list of attachments
        
        Args:
            attachments: List of attachment dictionaries
            
        Returns:
            Dictionary with 'allowed' and 'filtered' lists
        """
        allowed = []
        filtered = []
        
        for attachment in attachments:
            filename = attachment.get('filename', attachment.get('title', ''))
            file_size = attachment.get('size', attachment.get('extensions', {}).get('fileSize'))
            
            result = self.should_process_attachment(filename, file_size)
            
            if result.should_process:
                allowed.append(attachment)
                logger.debug(f"Allowed attachment: {filename}")
            else:
                filtered.append(attachment)
                logger.debug(f"Filtered attachment: {filename} - {result.reason}")
        
        logger.info(f"Filtered attachments: {len(allowed)} allowed, {len(filtered)} filtered")
        
        return {
            'allowed': allowed,
            'filtered': filtered
        }
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of filter configuration
        
        Returns:
            Dictionary with filter settings
        """
        return {
            'allowed_extensions': sorted(self.allowed_extensions),
            'max_file_size_mb': self.max_file_size_bytes / (1024 * 1024) if self.max_file_size_bytes > 0 else 0,
            'total_extensions': len(self.allowed_extensions)
        }
    
    def validate_extensions(self, extensions_str: str) -> List[str]:
        """Validate extensions string and return any issues
        
        Args:
            extensions_str: Comma-separated extension list
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not extensions_str or not extensions_str.strip():
            errors.append("Extensions string cannot be empty")
            return errors
        
        extensions = self._parse_extensions(extensions_str)
        
        if not extensions:
            errors.append("No valid extensions found after parsing")
            return errors
        
        # Check for common issues
        for ext in extensions:
            if len(ext) > 10:
                errors.append(f"Extension '{ext}' is unusually long")
            if not re.match(r'^[a-z0-9]+$', ext):
                errors.append(f"Extension '{ext}' contains invalid characters")
        
        return errors
    
    def update_extensions(self, extensions_str: str) -> bool:
        """Update allowed extensions
        
        Args:
            extensions_str: New comma-separated extension list
            
        Returns:
            True if update was successful
        """
        try:
            # Validate first
            errors = self.validate_extensions(extensions_str)
            if errors:
                logger.error(f"Invalid extensions: {', '.join(errors)}")
                return False
            
            # Update
            old_extensions = self.allowed_extensions.copy()
            self.allowed_extensions = self._parse_extensions(extensions_str)
            
            logger.info(f"Updated extensions from {sorted(old_extensions)} to {sorted(self.allowed_extensions)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update extensions: {e}")
            return False
    
    def is_text_file(self, filename: str) -> bool:
        """Check if file is likely a text file based on extension
        
        Args:
            filename: The filename
            
        Returns:
            True if file is likely text-based
        """
        text_extensions = {
            'md', 'txt', 'json', 'xml', 'html', 'htm', 'css', 'js', 'ts',
            'py', 'java', 'cpp', 'c', 'h', 'cs', 'php', 'rb', 'go', 'rs',
            'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'log', 'csv',
            'tsv', 'sql', 'sh', 'bash', 'ps1', 'bat', 'cmd'
        }
        
        extension = self._get_file_extension(filename)
        return extension in text_extensions
    
    def get_content_type(self, filename: str) -> str:
        """Get appropriate content type for file
        
        Args:
            filename: The filename
            
        Returns:
            MIME content type
        """
        extension = self._get_file_extension(filename)
        
        content_types = {
            'md': 'text/markdown',
            'txt': 'text/plain',
            'json': 'application/json',
            'xml': 'application/xml',
            'html': 'text/html',
            'htm': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'ts': 'application/typescript',
            'py': 'text/x-python',
            'java': 'text/x-java-source',
            'cpp': 'text/x-c++src',
            'c': 'text/x-csrc',
            'h': 'text/x-chdr',
            'cs': 'text/x-csharp',
            'php': 'application/x-php',
            'rb': 'application/x-ruby',
            'go': 'text/x-go',
            'rs': 'text/x-rust',
            'yaml': 'application/x-yaml',
            'yml': 'application/x-yaml',
            'toml': 'application/toml',
            'ini': 'text/plain',
            'cfg': 'text/plain',
            'conf': 'text/plain',
            'log': 'text/plain',
            'csv': 'text/csv',
            'tsv': 'text/tab-separated-values',
            'sql': 'application/sql',
            'sh': 'application/x-sh',
            'bash': 'application/x-sh',
            'ps1': 'application/x-powershell',
            'bat': 'application/x-bat',
            'cmd': 'application/x-bat',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        return content_types.get(extension, 'application/octet-stream')
```

### Testing Requirements

```python
# tests/test_attachment_filter.py

import pytest
from confluence_markdown_exporter.processors.attachment_filter import AttachmentFilter, FilterResult

class TestAttachmentFilter:
    @pytest.fixture
    def filter_default(self):
        return AttachmentFilter("md,txt,pdf")
    
    @pytest.fixture
    def filter_custom(self):
        return AttachmentFilter("docx,xlsx,pptx", max_file_size_mb=5)
    
    def test_extension_parsing(self, filter_default):
        assert 'md' in filter_default.allowed_extensions
        assert 'txt' in filter_default.allowed_extensions
        assert 'pdf' in filter_default.allowed_extensions
        assert len(filter_default.allowed_extensions) == 3
    
    def test_extension_parsing_with_dots(self):
        filter_obj = AttachmentFilter(".md,.txt,.pdf")
        assert 'md' in filter_obj.allowed_extensions
        assert 'txt' in filter_obj.allowed_extensions
        assert 'pdf' in filter_obj.allowed_extensions
    
    def test_extension_parsing_with_spaces(self):
        filter_obj = AttachmentFilter("md , txt , pdf ")
        assert 'md' in filter_obj.allowed_extensions
        assert 'txt' in filter_obj.allowed_extensions
        assert 'pdf' in filter_obj.allowed_extensions
    
    def test_should_process_allowed_extension(self, filter_default):
        result = filter_default.should_process_attachment("test.md")
        assert result.should_process == True
        assert result.matched_extension == "md"
    
    def test_should_process_disallowed_extension(self, filter_default):
        result = filter_default.should_process_attachment("test.jpg")
        assert result.should_process == False
        assert "jpg" in result.reason
    
    def test_should_process_no_extension(self, filter_default):
        result = filter_default.should_process_attachment("testfile")
        assert result.should_process == False
        assert "not in allowed list" in result.reason
    
    def test_file_size_limit(self, filter_custom):
        # 5MB limit
        result = filter_custom.should_process_attachment("test.docx", file_size=6*1024*1024)
        assert result.should_process == False
        assert "exceeds limit" in result.reason
    
    def test_file_size_within_limit(self, filter_custom):
        # 5MB limit
        result = filter_custom.should_process_attachment("test.docx", file_size=3*1024*1024)
        assert result.should_process == True
    
    def test_filter_attachments_list(self, filter_default):
        attachments = [
            {"filename": "doc1.md", "size": 1024},
            {"filename": "doc2.txt", "size": 2048},
            {"filename": "image.jpg", "size": 1024},
            {"filename": "presentation.pptx", "size": 1024}
        ]
        
        result = filter_default.filter_attachments(attachments)
        
        assert len(result['allowed']) == 2
        assert len(result['filtered']) == 2
        assert result['allowed'][0]['filename'] == 'doc1.md'
        assert result['allowed'][1]['filename'] == 'doc2.txt'
    
    def test_get_file_extension(self, filter_default):
        assert filter_default._get_file_extension("test.md") == "md"
        assert filter_default._get_file_extension("test.PDF") == "pdf"
        assert filter_default._get_file_extension("test") == ""
        assert filter_default._get_file_extension("test.tar.gz") == "gz"
    
    def test_is_text_file(self, filter_default):
        assert filter_default.is_text_file("test.md") == True
        assert filter_default.is_text_file("test.txt") == True
        assert filter_default.is_text_file("test.py") == True
        assert filter_default.is_text_file("test.pdf") == False
        assert filter_default.is_text_file("test.jpg") == False
    
    def test_get_content_type(self, filter_default):
        assert filter_default.get_content_type("test.md") == "text/markdown"
        assert filter_default.get_content_type("test.txt") == "text/plain"
        assert filter_default.get_content_type("test.pdf") == "application/pdf"
        assert filter_default.get_content_type("test.unknown") == "application/octet-stream"
    
    def test_validate_extensions(self, filter_default):
        errors = filter_default.validate_extensions("md,txt,pdf")
        assert len(errors) == 0
        
        errors = filter_default.validate_extensions("")
        assert len(errors) > 0
        assert "cannot be empty" in errors[0]
        
        errors = filter_default.validate_extensions("md,txt,verylongextension")
        assert len(errors) > 0
        assert "unusually long" in errors[0]
    
    def test_update_extensions(self, filter_default):
        assert filter_default.update_extensions("docx,xlsx,pptx") == True
        assert 'docx' in filter_default.allowed_extensions
        assert 'md' not in filter_default.allowed_extensions
        
        assert filter_default.update_extensions("") == False
    
    def test_get_filter_summary(self, filter_default):
        summary = filter_default.get_filter_summary()
        assert 'allowed_extensions' in summary
        assert 'max_file_size_mb' in summary
        assert 'total_extensions' in summary
        assert summary['total_extensions'] == 3
```

## Task 4.2: Create Open-WebUI Exporter

### Objective
Implement the main export logic for Open-WebUI with comprehensive file handling, progress reporting, and error management.

### Files to Create
- `confluence_markdown_exporter/exporters/open_webui_exporter.py`
- `confluence_markdown_exporter/exporters/__init__.py` (update)

### Requirements
- Knowledge base creation with specified naming and description
- File conflict resolution (replace content)
- Progress reporting with detailed logging
- Error handling with continuation
- Support for both batch and individual uploads
- Metadata enrichment integration
- Proper file type handling

### Reference Implementation

```python
# confluence_markdown_exporter/exporters/open_webui_exporter.py

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from ..clients.open_webui_client import OpenWebUIClient, OpenWebUIClientError
from ..clients.confluence_client import ConfluenceClient
from ..processors.attachment_filter import AttachmentFilter
from ..processors.metadata_enricher import MetadataEnricher
from ..models.open_webui_models import OpenWebUIExportSummary, OpenWebUIKnowledge, OpenWebUIFile

logger = logging.getLogger(__name__)

class OpenWebUIExporter:
    """Exports Confluence content to Open-WebUI knowledge base"""
    
    def __init__(self, 
                 open_webui_client: OpenWebUIClient,
                 confluence_client: ConfluenceClient,
                 attachment_filter: AttachmentFilter,
                 metadata_enricher: MetadataEnricher,
                 use_batch_upload: bool = True):
        """Initialize the Open-WebUI exporter
        
        Args:
            open_webui_client: Client for Open-WebUI API
            confluence_client: Client for Confluence API
            attachment_filter: Filter for attachments
            metadata_enricher: Enricher for metadata
            use_batch_upload: Whether to use batch upload for better performance
        """
        self.open_webui_client = open_webui_client
        self.confluence_client = confluence_client
        self.attachment_filter = attachment_filter
        self.metadata_enricher = metadata_enricher
        self.use_batch_upload = use_batch_upload
        
        logger.info("Initialized Open-WebUI exporter")
    
    def export_space(self, space_key: str, output_path: str, 
                    pages: List[Dict[str, Any]], 
                    attachments: List[Dict[str, Any]]) -> OpenWebUIExportSummary:
        """Export a complete Confluence space to Open-WebUI
        
        Args:
            space_key: The Confluence space key
            output_path: Local output path for files
            pages: List of page dictionaries
            attachments: List of attachment dictionaries
            
        Returns:
            Export summary with results
        """
        start_time = datetime.now()
        
        # Get space details
        space_details = self.confluence_client.get_space_details(space_key)
        if not space_details:
            logger.error(f"Could not retrieve space details for {space_key}")
            return self._create_failed_summary(space_key, "Could not retrieve space details")
        
        space_name = space_details.get('name', space_key)
        space_url = self.confluence_client.build_space_url(space_key)
        
        # Initialize summary
        summary = OpenWebUIExportSummary(
            knowledge_base_name=space_name,
            knowledge_base_id="",
            total_pages=len(pages),
            total_attachments=len(attachments),
            successful_pages=0,
            successful_attachments=0,
            failed_pages=0,
            failed_attachments=0,
            start_time=start_time
        )
        
        try:
            # Create or get knowledge base
            knowledge_base = self._create_or_get_knowledge_base(space_name, space_url)
            if not knowledge_base:
                logger.error(f"Failed to create knowledge base for space {space_key}")
                summary.add_page_failure("Failed to create knowledge base")
                return summary
            
            summary.knowledge_base_id = knowledge_base.id
            logger.info(f"Using knowledge base: {knowledge_base.name} (ID: {knowledge_base.id})")
            
            # Filter attachments
            filtered_attachments = self.attachment_filter.filter_attachments(attachments)
            allowed_attachments = filtered_attachments['allowed']
            
            logger.info(f"Processing {len(pages)} pages and {len(allowed_attachments)} attachments")
            
            # Export pages
            uploaded_file_ids = []
            for i, page in enumerate(pages):
                try:
                    file_id = self._export_page(page, output_path, space_key, i + 1, len(pages))
                    if file_id:
                        uploaded_file_ids.append(file_id)
                        summary.add_page_success()
                    else:
                        summary.add_page_failure(f"Failed to export page {page.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error exporting page {page.get('title', 'Unknown')}: {e}")
                    summary.add_page_failure(str(e))
            
            # Export attachments
            for i, attachment in enumerate(allowed_attachments):
                try:
                    file_id = self._export_attachment(attachment, output_path, space_key, i + 1, len(allowed_attachments))
                    if file_id:
                        uploaded_file_ids.append(file_id)
                        summary.add_attachment_success()
                    else:
                        summary.add_attachment_failure(f"Failed to export attachment {attachment.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error exporting attachment {attachment.get('title', 'Unknown')}: {e}")
                    summary.add_attachment_failure(str(e))
            
            # Register files with knowledge base
            if uploaded_file_ids:
                self._register_files_with_knowledge_base(knowledge_base.id, uploaded_file_ids)
            
            summary.end_time = datetime.now()
            
            logger.info(f"Export completed: {summary.total_successful}/{summary.total_files} files successful")
            logger.info(summary.get_summary_text())
            
            return summary
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            summary.add_page_failure(f"Export failed: {str(e)}")
            summary.end_time = datetime.now()
            return summary
    
    def _create_or_get_knowledge_base(self, space_name: str, space_url: str) -> Optional[OpenWebUIKnowledge]:
        """Create or get knowledge base for the space
        
        Args:
            space_name: Name of the Confluence space
            space_url: URL of the Confluence space
            
        Returns:
            Knowledge base object or None if failed
        """
        try:
            description = f"Automated Confluence Export of {space_url}"
            knowledge_base = self.open_webui_client.create_or_get_knowledge_base(space_name, description)
            return knowledge_base
        except OpenWebUIClientError as e:
            logger.error(f"Failed to create/get knowledge base: {e}")
            return None
    
    def _export_page(self, page: Dict[str, Any], output_path: str, space_key: str, 
                    current: int, total: int) -> Optional[str]:
        """Export a single page to Open-WebUI
        
        Args:
            page: Page dictionary
            output_path: Local output path
            space_key: Confluence space key
            current: Current page number
            total: Total pages
            
        Returns:
            File ID if successful, None otherwise
        """
        page_id = page.get('id')
        page_title = page.get('title', 'Unknown')
        
        try:
            logger.info(f"Exporting page {current}/{total}: {page_title}")
            
            # Get complete page metadata
            page_metadata = self.confluence_client.get_complete_page_metadata(page_id)
            
            # Read page content from local file
            page_content = self._read_page_content(output_path, page, space_key)
            if not page_content:
                logger.error(f"Could not read content for page {page_title}")
                return None
            
            # Enrich content with metadata
            enriched_content = self.metadata_enricher.enrich_page_content(page_content, page_metadata)
            
            # Generate filename
            filename = self._generate_safe_filename(page_title, '.md')
            
            # Upload to Open-WebUI
            file_obj = self.open_webui_client.create_or_update_file(
                filename, 
                enriched_content, 
                'text/markdown'
            )
            
            logger.info(f"Uploading '{filename}' to knowledge base '{self.knowledge_base_name}'... Success")
            return file_obj.id
            
        except Exception as e:
            logger.error(f"Uploading '{page_title}' to knowledge base '{self.knowledge_base_name}'... Failed: {str(e)}")
            return None
    
    def _export_attachment(self, attachment: Dict[str, Any], output_path: str, space_key: str,
                         current: int, total: int) -> Optional[str]:
        """Export a single attachment to Open-WebUI
        
        Args:
            attachment: Attachment dictionary
            output_path: Local output path
            space_key: Confluence space key
            current: Current attachment number
            total: Total attachments
            
        Returns:
            File ID if successful, None otherwise
        """
        attachment_id = attachment.get('id')
        attachment_title = attachment.get('title', 'Unknown')
        
        try:
            logger.info(f"Exporting attachment {current}/{total}: {attachment_title}")
            
            # Get complete attachment metadata
            attachment_metadata = self.confluence_client.get_complete_attachment_metadata(attachment_id)
            
            # Read attachment content from local file
            attachment_content = self._read_attachment_content(output_path, attachment, space_key)
            if attachment_content is None:
                logger.error(f"Could not read content for attachment {attachment_title}")
                return None
            
            # Determine if this is a text file that can be enriched
            is_text = self.attachment_filter.is_text_file(attachment_title)
            
            if is_text and isinstance(attachment_content, str):
                # Enrich text content with metadata
                enriched_content = self.metadata_enricher.enrich_attachment_content(
                    attachment_content, 
                    attachment_metadata
                )
            else:
                # Binary content - use as-is
                enriched_content = attachment_content
            
            # Generate safe filename
            filename = self._generate_safe_filename(attachment_title)
            
            # Get content type
            content_type = self.attachment_filter.get_content_type(attachment_title)
            
            # Upload to Open-WebUI
            file_obj = self.open_webui_client.create_or_update_file(
                filename, 
                enriched_content, 
                content_type
            )
            
            logger.info(f"Uploading '{filename}' to knowledge base '{self.knowledge_base_name}'... Success")
            return file_obj.id
            
        except Exception as e:
            logger.error(f"Uploading '{attachment_title}' to knowledge base '{self.knowledge_base_name}'... Failed: {str(e)}")
            return None
    
    def _read_page_content(self, output_path: str, page: Dict[str, Any], space_key: str) -> Optional[str]:
        """Read page content from local file
        
        Args:
            output_path: Local output path
            page: Page dictionary
            space_key: Confluence space key
            
        Returns:
            Page content as string or None if failed
        """
        try:
            # Construct file path based on export configuration
            page_title = page.get('title', '')
            safe_title = self._generate_safe_filename(page_title, '.md')
            
            # Try different possible paths
            possible_paths = [
                Path(output_path) / space_key / safe_title,
                Path(output_path) / space_key / page_title / f"{page_title}.md",
                Path(output_path) / safe_title
            ]
            
            for file_path in possible_paths:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            logger.error(f"Could not find page file for {page_title}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading page content: {e}")
            return None
    
    def _read_attachment_content(self, output_path: str, attachment: Dict[str, Any], space_key: str) -> Optional[bytes]:
        """Read attachment content from local file
        
        Args:
            output_path: Local output path
            attachment: Attachment dictionary
            space_key: Confluence space key
            
        Returns:
            Attachment content as bytes or None if failed
        """
        try:
            # Construct file path based on export configuration
            attachment_title = attachment.get('title', '')
            
            # Try different possible paths
            possible_paths = [
                Path(output_path) / space_key / "attachments" / attachment_title,
                Path(output_path) / "attachments" / attachment_title,
                Path(output_path) / attachment_title
            ]
            
            for file_path in possible_paths:
                if file_path.exists():
                    mode = 'r' if self.attachment_filter.is_text_file(attachment_title) else 'rb'
                    encoding = 'utf-8' if mode == 'r' else None
                    
                    with open(file_path, mode, encoding=encoding) as f:
                        return f.read()
            
            logger.error(f"Could not find attachment file for {attachment_title}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading attachment content: {e}")
            return None
    
    def _register_files_with_knowledge_base(self, knowledge_base_id: str, file_ids: List[str]):
        """Register files with knowledge base
        
        Args:
            knowledge_base_id: ID of the knowledge base
            file_ids: List of file IDs to register
        """
        try:
            if self.use_batch_upload and len(file_ids) > 1:
                # Use batch upload for better performance
                logger.info(f"Registering {len(file_ids)} files with knowledge base using batch upload")
                self.open_webui_client.batch_add_files_to_knowledge(knowledge_base_id, file_ids)
            else:
                # Register files individually
                logger.info(f"Registering {len(file_ids)} files with knowledge base individually")
                for file_id in file_ids:
                    self.open_webui_client.add_file_to_knowledge(knowledge_base_id, file_id)
            
            logger.info(f"Successfully registered {len(file_ids)} files with knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to register files with knowledge base: {e}")
    
    def _generate_safe_filename(self, title: str, extension: str = '') -> str:
        """Generate a safe filename for Open-WebUI
        
        Args:
            title: Original title
            extension: File extension to add
            
        Returns:
            Safe filename
        """
        # Clean up the title
        safe_title = self.open_webui_client.cleanup_filename(title)
        
        # Add extension if not present
        if extension and not safe_title.endswith(extension):
            safe_title += extension
        
        return safe_title
    
    def _create_failed_summary(self, space_key: str, error_message: str) -> OpenWebUIExportSummary:
        """Create a summary for failed export
        
        Args:
            space_key: The space key
            error_message: Error message
            
        Returns:
            Export summary with failure
        """
        summary = OpenWebUIExportSummary(
            knowledge_base_name=space_key,
            knowledge_base_id="",
            total_pages=0,
            total_attachments=0,
            successful_pages=0,
            successful_attachments=0,
            failed_pages=1,
            failed_attachments=0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        summary.add_page_failure(error_message)
        return summary
    
    def test_connection(self) -> bool:
        """Test connection to Open-WebUI
        
        Returns:
            True if connection is successful
        """
        try:
            return self.open_webui_client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get export statistics and configuration
        
        Returns:
            Dictionary with export statistics
        """
        return {
            'attachment_filter': self.attachment_filter.get_filter_summary(),
            'batch_upload_enabled': self.use_batch_upload,
            'metadata_enrichment_enabled': True
        }
```

### Testing Requirements

```python
# tests/test_open_webui_exporter.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.models.open_webui_models import OpenWebUIKnowledge, OpenWebUIFile

class TestOpenWebUIExporter:
    @pytest.fixture
    def mock_clients(self):
        open_webui_client = Mock()
        confluence_client = Mock()
        attachment_filter = Mock()
        metadata_enricher = Mock()
        
        return {
            'open_webui_client': open_webui_client,
            'confluence_client': confluence_client,
            'attachment_filter': attachment_filter,
            'metadata_enricher': metadata_enricher
        }
    
    @pytest.fixture
    def exporter(self, mock_clients):
        return OpenWebUIExporter(
            mock_clients['open_webui_client'],
            mock_clients['confluence_client'],
            mock_clients['attachment_filter'],
            mock_clients['metadata_enricher']
        )
    
    def test_exporter_initialization(self, exporter):
        assert exporter.use_batch_upload == True
        assert exporter.open_webui_client is not None
        assert exporter.confluence_client is not None
    
    def test_create_or_get_knowledge_base(self, exporter, mock_clients):
        # Setup mock
        knowledge_base = OpenWebUIKnowledge(
            id='kb1',
            name='Test Space',
            description='Test Description',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z'
        )
        mock_clients['open_webui_client'].create_or_get_knowledge_base.return_value = knowledge_base
        
        result = exporter._create_or_get_knowledge_base('Test Space', 'https://test.com/spaces/TEST')
        
        assert result.name == 'Test Space'
        mock_clients['open_webui_client'].create_or_get_knowledge_base.assert_called_once_with(
            'Test Space',
            'Automated Confluence Export of https://test.com/spaces/TEST'
        )
    
    def test_generate_safe_filename(self, exporter, mock_clients):
        mock_clients['open_webui_client'].cleanup_filename.return_value = 'test_file'
        
        result = exporter._generate_safe_filename('Test File', '.md')
        assert result == 'test_file.md'
        
        mock_clients['open_webui_client'].cleanup_filename.assert_called_once_with('Test File')
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_read_page_content(self, mock_open, mock_exists, exporter):
        # Setup mocks
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "Page content"
        
        page = {'title': 'Test Page'}
        result = exporter._read_page_content('/output', page, 'TEST')
        
        assert result == "Page content"
        mock_open.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_read_attachment_content(self, mock_open, mock_exists, exporter, mock_clients):
        # Setup mocks
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "Attachment content"
        mock_clients['attachment_filter'].is_text_file.return_value = True
        
        attachment = {'title': 'test.txt'}
        result = exporter._read_attachment_content('/output', attachment, 'TEST')
        
        assert result == "Attachment content"
        mock_open.assert_called_once()
    
    def test_export_page(self, exporter, mock_clients):
        # Setup mocks
        mock_clients['confluence_client'].get_complete_page_metadata.return_value = {
            'page_title': 'Test Page',
            'space_key': 'TEST'
        }
        mock_clients['metadata_enricher'].enrich_page_content.return_value = "Enriched content"
        
        file_obj = OpenWebUIFile(
            id='file1',
            filename='test.md',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z'
        )
        mock_clients['open_webui_client'].create_or_update_file.return_value = file_obj
        
        # Mock file reading
        with patch.object(exporter, '_read_page_content', return_value="Page content"):
            with patch.object(exporter, '_generate_safe_filename', return_value="test.md"):
                exporter.knowledge_base_name = "Test KB"
                result = exporter._export_page({'id': '123', 'title': 'Test Page'}, '/output', 'TEST', 1, 1)
        
        assert result == 'file1'
        mock_clients['open_webui_client'].create_or_update_file.assert_called_once()
    
    def test_register_files_with_knowledge_base_batch(self, exporter, mock_clients):
        exporter.use_batch_upload = True
        file_ids = ['file1', 'file2', 'file3']
        
        exporter._register_files_with_knowledge_base('kb1', file_ids)
        
        mock_clients['open_webui_client'].batch_add_files_to_knowledge.assert_called_once_with('kb1', file_ids)
    
    def test_register_files_with_knowledge_base_individual(self, exporter, mock_clients):
        exporter.use_batch_upload = False
        file_ids = ['file1', 'file2']
        
        exporter._register_files_with_knowledge_base('kb1', file_ids)
        
        assert mock_clients['open_webui_client'].add_file_to_knowledge.call_count == 2
    
    def test_test_connection(self, exporter, mock_clients):
        mock_clients['open_webui_client'].test_connection.return_value = True
        
        result = exporter.test_connection()
        assert result == True
        
        mock_clients['open_webui_client'].test_connection.assert_called_once()
    
    def test_get_export_statistics(self, exporter, mock_clients):
        mock_clients['attachment_filter'].get_filter_summary.return_value = {
            'allowed_extensions': ['md', 'txt'],
            'max_file_size_mb': 10
        }
        
        stats = exporter.get_export_statistics()
        
        assert 'attachment_filter' in stats
        assert 'batch_upload_enabled' in stats
        assert 'metadata_enrichment_enabled' in stats
        assert stats['batch_upload_enabled'] == True
        assert stats['metadata_enrichment_enabled'] == True
```

## Task 4.3: Extend Main Export Controller

### Objective
Integrate Open-WebUI export into the main export workflow while maintaining backward compatibility.

### Files to Modify
- `confluence_markdown_exporter/main.py`

### Requirements
- Add conditional Open-WebUI export after markdown generation
- Process both pages and filtered attachments
- Maintain existing CLI interface
- Add proper error handling and logging
- Support configuration-driven export

### Reference Implementation

```python
# confluence_markdown_exporter/main.py
# (Integration with existing main.py)

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .clients.open_webui_client import OpenWebUIClient
from .processors.attachment_filter import AttachmentFilter
from .processors.metadata_enricher import MetadataEnricher
from .exporters.open_webui_exporter import OpenWebUIExporter
from .config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ConfluenceMarkdownExporter:
    """Main exporter class with Open-WebUI integration"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Initialize clients
        self.confluence_client = self._initialize_confluence_client()
        self.open_webui_client = None
        self.open_webui_exporter = None
        
        # Initialize if Open-WebUI export is enabled
        if self.config.get('export', {}).get('export_to_open_webui', False):
            self._initialize_open_webui_components()
    
    def _initialize_open_webui_components(self):
        """Initialize Open-WebUI related components"""
        try:
            # Get configuration
            open_webui_config = self.config.get('auth', {}).get('open_webui', {})
            export_config = self.config.get('export', {})
            
            # Validate configuration
            if not open_webui_config.get('url') or not open_webui_config.get('api_key'):
                logger.error("Open-WebUI URL and API key are required for export")
                return
            
            # Initialize Open-WebUI client
            self.open_webui_client = OpenWebUIClient(
                base_url=open_webui_config['url'],
                api_key=open_webui_config['api_key']
            )
            
            # Test connection
            if not self.open_webui_client.test_connection():
                logger.error("Failed to connect to Open-WebUI")
                return
            
            # Initialize attachment filter
            attachment_extensions = export_config.get('open_webui_attachment_extensions', 'md,txt,pdf')
            attachment_filter = AttachmentFilter(attachment_extensions)
            
            # Initialize metadata enricher
            metadata_enricher = MetadataEnricher()
            
            # Initialize exporter
            use_batch_upload = export_config.get('open_webui_batch_add', True)
            self.open_webui_exporter = OpenWebUIExporter(
                self.open_webui_client,
                self.confluence_client,
                attachment_filter,
                metadata_enricher,
                use_batch_upload
            )
            
            logger.info("Open-WebUI components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Open-WebUI components: {e}")
            self.open_webui_client = None
            self.open_webui_exporter = None
    
    def export_space(self, space_key: str, output_path: str) -> bool:
        """Export a Confluence space with optional Open-WebUI integration
        
        Args:
            space_key: The Confluence space key
            output_path: Local output path
            
        Returns:
            True if export was successful
        """
        try:
            logger.info(f"Starting export of space {space_key}")
            
            # Perform standard markdown export
            success = self._export_space_to_markdown(space_key, output_path)
            if not success:
                logger.error("Markdown export failed")
                return False
            
            # If Open-WebUI export is enabled, perform additional export
            if self.open_webui_exporter:
                logger.info("Starting Open-WebUI export")
                success = self._export_space_to_open_webui(space_key, output_path)
                if not success:
                    logger.error("Open-WebUI export failed, but markdown export succeeded")
                    # Don't return False here - markdown export was successful
            
            logger.info(f"Export of space {space_key} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def _export_space_to_markdown(self, space_key: str, output_path: str) -> bool:
        """Export space to markdown (existing functionality)"""
        # This would be the existing markdown export logic
        # For now, we'll assume it exists and works
        logger.info(f"Exporting space {space_key} to markdown at {output_path}")
        
        # Placeholder - actual implementation would use existing export logic
        return True
    
    def _export_space_to_open_webui(self, space_key: str, output_path: str) -> bool:
        """Export space to Open-WebUI knowledge base
        
        Args:
            space_key: The Confluence space key
            output_path: Local output path where markdown files are stored
            
        Returns:
            True if export was successful
        """
        try:
            # Get space pages and attachments
            pages = self._get_space_pages(space_key)
            attachments = self._get_space_attachments(space_key)
            
            if not pages:
                logger.warning(f"No pages found for space {space_key}")
                return True  # Not an error, just empty space
            
            # Perform export
            summary = self.open_webui_exporter.export_space(
                space_key, 
                output_path, 
                pages, 
                attachments
            )
            
            # Log summary
            logger.info(f"Open-WebUI export summary: {summary.total_successful}/{summary.total_files} files uploaded")
            
            if summary.total_failed > 0:
                logger.warning(f"Some files failed to upload: {summary.total_failed}")
                for error in summary.errors[-5:]:  # Show last 5 errors
                    logger.warning(f"  - {error}")
            
            return summary.total_successful > 0 or summary.total_files == 0
            
        except Exception as e:
            logger.error(f"Open-WebUI export failed: {e}")
            return False
    
    def _get_space_pages(self, space_key: str) -> List[Dict[str, Any]]:
        """Get all pages in a space
        
        Args:
            space_key: The Confluence space key
            
        Returns:
            List of page dictionaries
        """
        try:
            # This would use the existing Confluence client to get pages
            # For now, we'll return a placeholder
            logger.info(f"Getting pages for space {space_key}")
            
            # Placeholder - actual implementation would use existing logic
            return []
            
        except Exception as e:
            logger.error(f"Failed to get pages for space {space_key}: {e}")
            return []
    
    def _get_space_attachments(self, space_key: str) -> List[Dict[str, Any]]:
        """Get all attachments in a space
        
        Args:
            space_key: The Confluence space key
            
        Returns:
            List of attachment dictionaries
        """
        try:
            # This would use the existing Confluence client to get attachments
            # For now, we'll return a placeholder
            logger.info(f"Getting attachments for space {space_key}")
            
            # Placeholder - actual implementation would use existing logic
            return []
            
        except Exception as e:
            logger.error(f"Failed to get attachments for space {space_key}: {e}")
            return []
    
    def export_page(self, page_id: str, output_path: str) -> bool:
        """Export a single page with optional Open-WebUI integration
        
        Args:
            page_id: The Confluence page ID
            output_path: Local output path
            
        Returns:
            True if export was successful
        """
        try:
            logger.info(f"Starting export of page {page_id}")
            
            # Perform standard markdown export
            success = self._export_page_to_markdown(page_id, output_path)
            if not success:
                logger.error("Markdown export failed")
                return False
            
            # If Open-WebUI export is enabled, perform additional export
            if self.open_webui_exporter:
                logger.info("Starting Open-WebUI export")
                success = self._export_page_to_open_webui(page_id, output_path)
                if not success:
                    logger.error("Open-WebUI export failed, but markdown export succeeded")
            
            logger.info(f"Export of page {page_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def _export_page_to_markdown(self, page_id: str, output_path: str) -> bool:
        """Export page to markdown (existing functionality)"""
        # This would be the existing markdown export logic
        logger.info(f"Exporting page {page_id} to markdown at {output_path}")
        
        # Placeholder - actual implementation would use existing export logic
        return True
    
    def _export_page_to_open_webui(self, page_id: str, output_path: str) -> bool:
        """Export page to Open-WebUI knowledge base
        
        Args:
            page_id: The Confluence page ID
            output_path: Local output path where markdown files are stored
            
        Returns:
            True if export was successful
        """
        try:
            # Get page details
            page_data = self.confluence_client.get_page_by_id(page_id)
            if not page_data:
                logger.error(f"Could not retrieve page {page_id}")
                return False
            
            # Get space key
            space_key = page_data.get('space', {}).get('key', '')
            if not space_key:
                logger.error(f"Could not determine space for page {page_id}")
                return False
            
            # Get page attachments
            attachments = self._get_page_attachments(page_id)
            
            # Export using the space exporter (reuse logic)
            summary = self.open_webui_exporter.export_space(
                space_key,
                output_path,
                [page_data],
                attachments
            )
            
            logger.info(f"Open-WebUI export summary: {summary.total_successful}/{summary.total_files} files uploaded")
            
            return summary.total_successful > 0 or summary.total_files == 0
            
        except Exception as e:
            logger.error(f"Open-WebUI export failed: {e}")
            return False
    
    def _get_page_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all attachments for a page
        
        Args:
            page_id: The Confluence page ID
            
        Returns:
            List of attachment dictionaries
        """
        try:
            # This would use the existing Confluence client to get attachments
            logger.info(f"Getting attachments for page {page_id}")
            
            # Placeholder - actual implementation would use existing logic
            return []
            
        except Exception as e:
            logger.error(f"Failed to get attachments for page {page_id}: {e}")
            return []
    
    def test_open_webui_connection(self) -> bool:
        """Test connection to Open-WebUI
        
        Returns:
            True if connection is successful
        """
        if not self.open_webui_exporter:
            logger.error("Open-WebUI exporter is not initialized")
            return False
        
        return self.open_webui_exporter.test_connection()
    
    def get_export_status(self) -> Dict[str, Any]:
        """Get status of export configuration
        
        Returns:
            Dictionary with export status
        """
        status = {
            'markdown_export': True,
            'open_webui_export': False,
            'open_webui_configured': False,
            'open_webui_connected': False
        }
        
        if self.config.get('export', {}).get('export_to_open_webui', False):
            status['open_webui_export'] = True
            
            if self.open_webui_client:
                status['open_webui_configured'] = True
                status['open_webui_connected'] = self.open_webui_client.test_connection()
        
        return status


# CLI Integration
def main():
    """Main CLI entry point with Open-WebUI integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export Confluence content to Markdown and Open-WebUI')
    parser.add_argument('command', choices=['page', 'space', 'config', 'test-connection'], 
                       help='Command to execute')
    parser.add_argument('--space-key', help='Confluence space key')
    parser.add_argument('--page-id', help='Confluence page ID')
    parser.add_argument('--output', help='Output path')
    
    args = parser.parse_args()
    
    # Initialize configuration
    config_manager = ConfigManager()
    exporter = ConfluenceMarkdownExporter(config_manager)
    
    if args.command == 'config':
        # Run configuration interface
        config_manager.run_interactive_config()
        return
    
    elif args.command == 'test-connection':
        # Test Open-WebUI connection
        if exporter.test_open_webui_connection():
            print("✓ Open-WebUI connection successful")
        else:
            print("✗ Open-WebUI connection failed")
        return
    
    elif args.command == 'space':
        if not args.space_key or not args.output:
            print("Error: --space-key and --output are required for space export")
            return
        
        success = exporter.export_space(args.space_key, args.output)
        if success:
            print("✓ Space export completed successfully")
        else:
            print("✗ Space export failed")
    
    elif args.command == 'page':
        if not args.page_id or not args.output:
            print("Error: --page-id and --output are required for page export")
            return
        
        success = exporter.export_page(args.page_id, args.output)
        if success:
            print("✓ Page export completed successfully")
        else:
            print("✗ Page export failed")


if __name__ == '__main__':
    main()
```

## Deliverables

1. **Attachment Filter** (`attachment_filter.py`)
   - Extension-based filtering with validation
   - File size limits and content type detection
   - Comprehensive filtering logic with detailed reporting

2. **Open-WebUI Exporter** (`open_webui_exporter.py`)
   - Complete export workflow for spaces and pages
   - Knowledge base management with proper naming
   - File upload with metadata enrichment
   - Progress reporting with detailed logging
   - Error handling with continuation logic

3. **Main Export Controller Integration** (`main.py`)
   - Integration with existing export workflow
   - Configuration-driven Open-WebUI export
   - CLI interface updates
   - Connection testing utilities

4. **Test Suite**
   - Unit tests for all components
   - Integration tests for export workflow
   - Mock-based testing for external dependencies
   - Error handling and edge case validation

## Success Criteria

- [ ] Attachment filter correctly processes file extensions
- [ ] Open-WebUI exporter creates knowledge bases with proper naming
- [ ] Files are uploaded with enriched metadata
- [ ] Progress reporting shows detailed status messages
- [ ] Error handling continues processing after failures
- [ ] Batch upload works when enabled
- [ ] Individual upload works as fallback
- [ ] Integration with main export maintains backward compatibility
- [ ] CLI interface supports new functionality
- [ ] Connection testing validates Open-WebUI access
- [ ] All tests pass with >90% coverage
- [ ] Export summary provides comprehensive statistics
