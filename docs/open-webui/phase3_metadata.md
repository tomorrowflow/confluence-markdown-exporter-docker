# Phase 3: Metadata Enrichment

## Overview
Extend the Confluence API client to fetch additional metadata and create a metadata enricher to add comprehensive Confluence metadata to exported files.

## Task 3.1: Extend Confluence API Client

### Objective
Add methods to the existing Confluence API client to retrieve additional metadata required for Open-WebUI export.

### Files to Modify
- `confluence_markdown_exporter/clients/confluence_client.py`

### Requirements
- Add methods to fetch space details
- Add methods to get page ancestors
- Add methods to get attachment details
- Utilize additional endpoints from Confluence API v2
- Maintain backward compatibility
- Add proper error handling and logging

### Reference Implementation

```python
# confluence_markdown_exporter/clients/confluence_client.py
# (Extension to existing ConfluenceClient class)

from typing import Dict, List, Optional, Any
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ConfluenceClient:
    """Extended Confluence client with metadata fetching capabilities"""
    
    # ... existing methods ...
    
    def get_space_details(self, space_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed space information including homepage
        
        Args:
            space_key: The space key
            
        Returns:
            Dictionary containing space details or None if not found
        """
        try:
            # Use v2 API for better space information
            endpoint = f"/api/v2/spaces/{space_key}"
            response = self._make_request('GET', endpoint)
            
            if response.status_code == 200:
                space_data = response.json()
                logger.info(f"Retrieved space details for {space_key}")
                return space_data
            else:
                logger.warning(f"Space {space_key} not found or access denied")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get space details for {space_key}: {e}")
            return None
    
    def get_space_homepage(self, space_key: str) -> Optional[Dict[str, Any]]:
        """Get space homepage information
        
        Args:
            space_key: The space key
            
        Returns:
            Dictionary containing homepage details or None if not found
        """
        try:
            # Get space details first
            space_data = self.get_space_details(space_key)
            if not space_data:
                return None
            
            # Extract homepage information
            homepage_id = space_data.get('homepageId')
            if homepage_id:
                return self.get_page_by_id(homepage_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get homepage for space {space_key}: {e}")
            return None
    
    def get_page_ancestors(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all ancestors of a page (parent pages)
        
        Args:
            page_id: The page ID
            
        Returns:
            List of ancestor page dictionaries, ordered from root to immediate parent
        """
        try:
            # Use v1 API with ancestors expansion
            endpoint = f"/api/v1/content/{page_id}"
            params = {
                'expand': 'ancestors'
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response.status_code == 200:
                page_data = response.json()
                ancestors = page_data.get('ancestors', [])
                logger.info(f"Retrieved {len(ancestors)} ancestors for page {page_id}")
                return ancestors
            else:
                logger.warning(f"Could not get ancestors for page {page_id}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get ancestors for page {page_id}: {e}")
            return []
    
    def get_page_by_id(self, page_id: str, expand: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get page by ID with optional expansion
        
        Args:
            page_id: The page ID
            expand: Comma-separated list of properties to expand
            
        Returns:
            Dictionary containing page data or None if not found
        """
        try:
            endpoint = f"/api/v1/content/{page_id}"
            params = {}
            if expand:
                params['expand'] = expand
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response.status_code == 200:
                page_data = response.json()
                logger.info(f"Retrieved page {page_id}")
                return page_data
            else:
                logger.warning(f"Page {page_id} not found or access denied")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get page {page_id}: {e}")
            return None
    
    def get_attachment_details(self, attachment_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed attachment information using v2 API
        
        Args:
            attachment_id: The attachment ID
            
        Returns:
            Dictionary containing attachment details or None if not found
        """
        try:
            # Use v2 API for better attachment information
            endpoint = f"/api/v2/attachments/{attachment_id}"
            params = {
                'include-version': 'true',
                'include-collaborators': 'true'
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response.status_code == 200:
                attachment_data = response.json()
                logger.info(f"Retrieved attachment details for {attachment_id}")
                return attachment_data
            else:
                logger.warning(f"Attachment {attachment_id} not found or access denied")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get attachment details for {attachment_id}: {e}")
            return None
    
    def get_attachment_parent_page(self, attachment_id: str) -> Optional[Dict[str, Any]]:
        """Get the parent page of an attachment
        
        Args:
            attachment_id: The attachment ID
            
        Returns:
            Dictionary containing parent page data or None if not found
        """
        try:
            # Get attachment details first
            attachment_data = self.get_attachment_details(attachment_id)
            if not attachment_data:
                return None
            
            # Extract parent page information
            # In v2 API, this might be in different locations
            parent_id = None
            
            # Try different possible locations for parent page ID
            if 'parentId' in attachment_data:
                parent_id = attachment_data['parentId']
            elif 'container' in attachment_data and 'id' in attachment_data['container']:
                parent_id = attachment_data['container']['id']
            
            if parent_id:
                return self.get_page_by_id(parent_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get parent page for attachment {attachment_id}: {e}")
            return None
    
    def get_page_author_details(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get author details from page data
        
        Args:
            page_data: Page data dictionary
            
        Returns:
            Dictionary containing author details or None if not found
        """
        try:
            # Try to get author from version history
            if 'version' in page_data and 'by' in page_data['version']:
                author_data = page_data['version']['by']
                return {
                    'username': author_data.get('username', ''),
                    'display_name': author_data.get('displayName', ''),
                    'email': author_data.get('email', ''),
                    'user_key': author_data.get('userKey', '')
                }
            
            # Try to get from history if available
            if 'history' in page_data and 'createdBy' in page_data['history']:
                author_data = page_data['history']['createdBy']
                return {
                    'username': author_data.get('username', ''),
                    'display_name': author_data.get('displayName', ''),
                    'email': author_data.get('email', ''),
                    'user_key': author_data.get('userKey', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract author details: {e}")
            return None
    
    def get_page_timestamps(self, page_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Get creation and update timestamps from page data
        
        Args:
            page_data: Page data dictionary
            
        Returns:
            Dictionary with 'created' and 'updated' timestamps
        """
        try:
            timestamps = {
                'created': None,
                'updated': None
            }
            
            # Try to get from version information
            if 'version' in page_data:
                version_data = page_data['version']
                if 'when' in version_data:
                    timestamps['updated'] = version_data['when']
            
            # Try to get from history
            if 'history' in page_data:
                history_data = page_data['history']
                if 'createdDate' in history_data:
                    timestamps['created'] = history_data['createdDate']
            
            # For created date, try alternative locations
            if not timestamps['created']:
                # Check if it's in the root of page data
                if 'createdDate' in page_data:
                    timestamps['created'] = page_data['createdDate']
                elif 'created' in page_data:
                    timestamps['created'] = page_data['created']
            
            return timestamps
            
        except Exception as e:
            logger.error(f"Failed to extract timestamps: {e}")
            return {'created': None, 'updated': None}
    
    def build_page_url(self, space_key: str, page_id: str) -> str:
        """Build full URL to a Confluence page
        
        Args:
            space_key: The space key
            page_id: The page ID
            
        Returns:
            Full URL to the page
        """
        base_url = self.base_url.rstrip('/wiki/rest/api')
        return f"{base_url}/wiki/spaces/{space_key}/pages/{page_id}"
    
    def build_attachment_url(self, attachment_id: str, filename: str) -> str:
        """Build full URL to a Confluence attachment
        
        Args:
            attachment_id: The attachment ID
            filename: The attachment filename
            
        Returns:
            Full URL to the attachment
        """
        base_url = self.base_url.rstrip('/wiki/rest/api')
        return f"{base_url}/wiki/download/attachments/{attachment_id}/{filename}"
    
    def build_space_url(self, space_key: str) -> str:
        """Build full URL to a Confluence space
        
        Args:
            space_key: The space key
            
        Returns:
            Full URL to the space
        """
        base_url = self.base_url.rstrip('/wiki/rest/api')
        return f"{base_url}/wiki/spaces/{space_key}"
    
    def get_complete_page_metadata(self, page_id: str) -> Dict[str, Any]:
        """Get complete metadata for a page including all related information
        
        Args:
            page_id: The page ID
            
        Returns:
            Dictionary containing all available metadata
        """
        try:
            # Get page with expanded information
            page_data = self.get_page_by_id(page_id, expand='version,history,space,ancestors')
            if not page_data:
                return {}
            
            # Extract space information
            space_data = page_data.get('space', {})
            space_key = space_data.get('key', '')
            space_name = space_data.get('name', '')
            
            # Get homepage information
            homepage_data = self.get_space_homepage(space_key) if space_key else None
            homepage_title = homepage_data.get('title', '') if homepage_data else ''
            
            # Get ancestors
            ancestors = self.get_page_ancestors(page_id)
            ancestor_titles = [ancestor.get('title', '') for ancestor in ancestors]
            
            # Get author details
            author_details = self.get_page_author_details(page_data)
            
            # Get timestamps
            timestamps = self.get_page_timestamps(page_data)
            
            # Build URLs
            page_url = self.build_page_url(space_key, page_id)
            space_url = self.build_space_url(space_key)
            
            # Compile complete metadata
            metadata = {
                'page_id': page_id,
                'page_title': page_data.get('title', ''),
                'page_url': page_url,
                'space_key': space_key,
                'space_name': space_name,
                'space_url': space_url,
                'homepage_title': homepage_title,
                'ancestor_titles': ancestor_titles,
                'author': author_details,
                'created': timestamps['created'],
                'updated': timestamps['updated'],
                'version': page_data.get('version', {}).get('number', 1)
            }
            
            logger.info(f"Retrieved complete metadata for page {page_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get complete metadata for page {page_id}: {e}")
            return {}
    
    def get_complete_attachment_metadata(self, attachment_id: str) -> Dict[str, Any]:
        """Get complete metadata for an attachment including parent page information
        
        Args:
            attachment_id: The attachment ID
            
        Returns:
            Dictionary containing all available metadata
        """
        try:
            # Get attachment details
            attachment_data = self.get_attachment_details(attachment_id)
            if not attachment_data:
                return {}
            
            # Get parent page information
            parent_page_data = self.get_attachment_parent_page(attachment_id)
            
            # Extract basic attachment information
            attachment_filename = attachment_data.get('filename', '')
            attachment_created = attachment_data.get('createdDate', '')
            attachment_updated = attachment_data.get('updatedDate', '')
            attachment_size = attachment_data.get('size', 0)
            attachment_media_type = attachment_data.get('mediaType', '')
            
            # Extract author information
            author_details = None
            if 'version' in attachment_data and 'by' in attachment_data['version']:
                author_data = attachment_data['version']['by']
                author_details = {
                    'username': author_data.get('username', ''),
                    'display_name': author_data.get('displayName', ''),
                    'email': author_data.get('email', ''),
                    'user_key': author_data.get('userKey', '')
                }
            
            # Get parent page metadata if available
            parent_metadata = {}
            if parent_page_data:
                parent_metadata = self.get_complete_page_metadata(parent_page_data['id'])
            
            # Build attachment URL
            attachment_url = self.build_attachment_url(attachment_id, attachment_filename)
            
            # Compile complete metadata
            metadata = {
                'attachment_id': attachment_id,
                'attachment_filename': attachment_filename,
                'attachment_url': attachment_url,
                'attachment_created': attachment_created,
                'attachment_updated': attachment_updated,
                'attachment_size': attachment_size,
                'attachment_media_type': attachment_media_type,
                'attachment_author': author_details,
                'parent_page': parent_metadata
            }
            
            logger.info(f"Retrieved complete metadata for attachment {attachment_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get complete metadata for attachment {attachment_id}: {e}")
            return {}
```

### Testing Requirements

```python
# tests/test_confluence_client_extended.py

import pytest
from unittest.mock import Mock, patch
from confluence_markdown_exporter.clients.confluence_client import ConfluenceClient

class TestConfluenceClientExtended:
    @pytest.fixture
    def client(self):
        return ConfluenceClient("https://test.atlassian.net", "test-token")
    
    @patch('requests.Session.request')
    def test_get_space_details(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'key': 'TEST',
            'name': 'Test Space',
            'homepageId': '123'
        }
        mock_request.return_value = mock_response
        
        result = client.get_space_details('TEST')
        assert result['key'] == 'TEST'
        assert result['name'] == 'Test Space'
        assert result['homepageId'] == '123'
    
    @patch('requests.Session.request')
    def test_get_page_ancestors(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ancestors': [
                {'id': '1', 'title': 'Root Page'},
                {'id': '2', 'title': 'Parent Page'}
            ]
        }
        mock_request.return_value = mock_response
        
        ancestors = client.get_page_ancestors('123')
        assert len(ancestors) == 2
        assert ancestors[0]['title'] == 'Root Page'
        assert ancestors[1]['title'] == 'Parent Page'
    
    @patch('requests.Session.request')
    def test_get_attachment_details(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'att123',
            'filename': 'test.pdf',
            'size': 1024,
            'mediaType': 'application/pdf'
        }
        mock_request.return_value = mock_response
        
        result = client.get_attachment_details('att123')
        assert result['filename'] == 'test.pdf'
        assert result['size'] == 1024
        assert result['mediaType'] == 'application/pdf'
    
    def test_build_page_url(self, client):
        client.base_url = "https://test.atlassian.net/wiki/rest/api"
        url = client.build_page_url('TEST', '123')
        assert url == "https://test.atlassian.net/wiki/spaces/TEST/pages/123"
    
    def test_build_attachment_url(self, client):
        client.base_url = "https://test.atlassian.net/wiki/rest/api"
        url = client.build_attachment_url('att123', 'test.pdf')
        assert url == "https://test.atlassian.net/wiki/download/attachments/att123/test.pdf"
    
    def test_get_page_timestamps(self, client):
        page_data = {
            'version': {
                'when': '2024-01-01T12:00:00.000Z'
            },
            'history': {
                'createdDate': '2024-01-01T10:00:00.000Z'
            }
        }
        
        timestamps = client.get_page_timestamps(page_data)
        assert timestamps['created'] == '2024-01-01T10:00:00.000Z'
        assert timestamps['updated'] == '2024-01-01T12:00:00.000Z'
    
    def test_get_page_author_details(self, client):
        page_data = {
            'version': {
                'by': {
                    'username': 'jsmith',
                    'displayName': 'John Smith',
                    'email': 'john.smith@example.com'
                }
            }
        }
        
        author = client.get_page_author_details(page_data)
        assert author['username'] == 'jsmith'
        assert author['display_name'] == 'John Smith'
        assert author['email'] == 'john.smith@example.com'
```

## Task 3.2: Create Metadata Enricher

### Objective
Create a component that enriches markdown files with comprehensive Confluence metadata in the frontmatter.

### Files to Create
- `confluence_markdown_exporter/processors/metadata_enricher.py`
- `confluence_markdown_exporter/processors/__init__.py` (update)

### Requirements
- Add frontmatter with Confluence metadata
- Support both page and attachment metadata
- Handle missing metadata gracefully
- Provide configurable metadata inclusion
- Format metadata appropriately for different use cases

### Reference Implementation

```python
# confluence_markdown_exporter/processors/metadata_enricher.py

import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class MetadataEnricher:
    """Enriches markdown files with Confluence metadata"""
    
    def __init__(self, include_fields: Optional[List[str]] = None):
        """Initialize the metadata enricher
        
        Args:
            include_fields: List of metadata fields to include. If None, include all.
        """
        self.include_fields = include_fields or [
            'space', 'author', 'created', 'updated', 'ancestors', 'page_name', 'url'
        ]
        
        self.default_page_fields = [
            'confluence_space',
            'confluence_space_name', 
            'confluence_homepage',
            'confluence_ancestors',
            'confluence_page_name',
            'confluence_page_id',
            'confluence_page_url',
            'confluence_space_url',
            'confluence_author',
            'confluence_created',
            'confluence_updated',
            'confluence_version'
        ]
        
        self.default_attachment_fields = [
            'confluence_space',
            'confluence_space_name',
            'confluence_homepage',
            'confluence_ancestors',
            'confluence_page_name',
            'confluence_attachment_name',
            'confluence_attachment_id',
            'confluence_attachment_url',
            'confluence_attachment_author',
            'confluence_attachment_created',
            'confluence_attachment_updated',
            'confluence_attachment_size',
            'confluence_attachment_media_type',
            'confluence_parent_page_id',
            'confluence_parent_page_url'
        ]
    
    def enrich_page_content(self, content: str, page_metadata: Dict[str, Any]) -> str:
        """Enrich page content with Confluence metadata
        
        Args:
            content: The markdown content
            page_metadata: Dictionary containing page metadata
            
        Returns:
            Enriched markdown content with frontmatter
        """
        try:
            # Extract existing frontmatter if present
            existing_frontmatter = self._extract_frontmatter(content)
            content_without_frontmatter = self._remove_frontmatter(content)
            
            # Generate page metadata
            page_metadata_dict = self._generate_page_metadata(page_metadata)
            
            # Merge with existing frontmatter
            combined_metadata = {**existing_frontmatter, **page_metadata_dict}
            
            # Create enriched content
            enriched_content = self._create_content_with_frontmatter(
                content_without_frontmatter, 
                combined_metadata
            )
            
            logger.info(f"Enriched page content with metadata: {page_metadata.get('page_title', 'Unknown')}")
            return enriched_content
            
        except Exception as e:
            logger.error(f"Failed to enrich page content: {e}")
            return content
    
    def enrich_attachment_content(self, content: str, attachment_metadata: Dict[str, Any]) -> str:
        """Enrich attachment content with Confluence metadata
        
        Args:
            content: The attachment content (for text files)
            attachment_metadata: Dictionary containing attachment metadata
            
        Returns:
            Enriched content with frontmatter
        """
        try:
            # Extract existing frontmatter if present
            existing_frontmatter = self._extract_frontmatter(content)
            content_without_frontmatter = self._remove_frontmatter(content)
            
            # Generate attachment metadata
            attachment_metadata_dict = self._generate_attachment_metadata(attachment_metadata)
            
            # Merge with existing frontmatter
            combined_metadata = {**existing_frontmatter, **attachment_metadata_dict}
            
            # Create enriched content
            enriched_content = self._create_content_with_frontmatter(
                content_without_frontmatter, 
                combined_metadata
            )
            
            logger.info(f"Enriched attachment content with metadata: {attachment_metadata.get('attachment_filename', 'Unknown')}")
            return enriched_content
            
        except Exception as e:
            logger.error(f"Failed to enrich attachment content: {e}")
            return content
    
    def _generate_page_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate page metadata dictionary for frontmatter
        
        Args:
            metadata: Raw metadata from Confluence API
            
        Returns:
            Dictionary with formatted metadata
        """
        formatted_metadata = {}
        
        # Space information
        if self._should_include_field('space'):
            formatted_metadata['confluence_space'] = metadata.get('space_key', '')
            formatted_metadata['confluence_space_name'] = metadata.get('space_name', '')
            formatted_metadata['confluence_space_url'] = metadata.get('space_url', '')
        
        # Homepage information
        if self._should_include_field('homepage'):
            formatted_metadata['confluence_homepage'] = metadata.get('homepage_title', '')
        
        # Page information
        if self._should_include_field('page_name'):
            formatted_metadata['confluence_page_name'] = metadata.get('page_title', '')
            formatted_metadata['confluence_page_id'] = metadata.get('page_id', '')
            formatted_metadata['confluence_page_url'] = metadata.get('page_url', '')
        
        # Ancestors
        if self._should_include_field('ancestors'):
            ancestors = metadata.get('ancestor_titles', [])
            formatted_metadata['confluence_ancestors'] = ancestors
        
        # Author information
        if self._should_include_field('author'):
            author_data = metadata.get('author', {})
            if author_data:
                formatted_metadata['confluence_author'] = author_data.get('display_name', author_data.get('username', ''))
                formatted_metadata['confluence_author_email'] = author_data.get('email', '')
                formatted_metadata['confluence_author_username'] = author_data.get('username', '')
        
        # Timestamps
        if self._should_include_field('created'):
            created_date = metadata.get('created')
            if created_date:
                formatted_metadata['confluence_created'] = self._format_timestamp(created_date)
        
        if self._should_include_field('updated'):
            updated_date = metadata.get('updated')
            if updated_date:
                formatted_metadata['confluence_updated'] = self._format_timestamp(updated_date)
        
        # Version
        if self._should_include_field('version'):
            formatted_metadata['confluence_version'] = metadata.get('version', 1)
        
        return formatted_metadata
    
    def _generate_attachment_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate attachment metadata dictionary for frontmatter
        
        Args:
            metadata: Raw metadata from Confluence API
            
        Returns:
            Dictionary with formatted metadata
        """
        formatted_metadata = {}
        
        # Parent page information
        parent_page = metadata.get('parent_page', {})
        if parent_page:
            # Include parent page space information
            formatted_metadata['confluence_space'] = parent_page.get('space_key', '')
            formatted_metadata['confluence_space_name'] = parent_page.get('space_name', '')
            formatted_metadata['confluence_space_url'] = parent_page.get('space_url', '')
            
            # Include parent page information
            formatted_metadata['confluence_page_name'] = parent_page.get('page_title', '')
            formatted_metadata['confluence_parent_page_id'] = parent_page.get('page_id', '')
            formatted_metadata['confluence_parent_page_url'] = parent_page.get('page_url', '')
            
            # Include homepage and ancestors from parent page
            formatted_metadata['confluence_homepage'] = parent_page.get('homepage_title', '')
            formatted_metadata['confluence_ancestors'] = parent_page.get('ancestor_titles', [])
        
        # Attachment specific information
        if self._should_include_field('attachment'):
            formatted_metadata['confluence_attachment_name'] = metadata.get('attachment_filename', '')
            formatted_metadata['confluence_attachment_id'] = metadata.get('attachment_id', '')
            formatted_metadata['confluence_attachment_url'] = metadata.get('attachment_url', '')
            formatted_metadata['confluence_attachment_size'] = metadata.get('attachment_size', 0)
            formatted_metadata['confluence_attachment_media_type'] = metadata.get('attachment_media_type', '')
        
        # Attachment author information
        if self._should_include_field('author'):
            author_data = metadata.get('attachment_author', {})
            if author_data:
                formatted_metadata['confluence_attachment_author'] = author_data.get('display_name', author_data.get('username', ''))
                formatted_metadata['confluence_attachment_author_email'] = author_data.get('email', '')
                formatted_metadata['confluence_attachment_author_username'] = author_data.get('username', '')
        
        # Attachment timestamps
        if self._should_include_field('created'):
            created_date = metadata.get('attachment_created')
            if created_date:
                formatted_metadata['confluence_attachment_created'] = self._format_timestamp(created_date)
        
        if self._should_include_field('updated'):
            updated_date = metadata.get('attachment_updated')
            if updated_date:
                formatted_metadata['confluence_attachment_updated'] = self._format_timestamp(updated_date)
        
        return formatted_metadata
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract existing frontmatter from content
        
        Args:
            content: The markdown content
            
        Returns:
            Dictionary containing existing frontmatter
        """
        try:
            # Check for YAML frontmatter
            if content.startswith('---\n'):
                # Find the end of frontmatter
                end_match = re.search(r'\n---\n', content[4:])
                if end_match:
                    yaml_content = content[4:end_match.start() + 4]
                    return yaml.safe_load(yaml_content) or {}
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to extract frontmatter: {e}")
            return {}
    
    def _remove_frontmatter(self, content: str) -> str:
        """Remove existing frontmatter from content
        
        Args:
            content: The markdown content
            
        Returns:
            Content without frontmatter
        """
        try:
            # Check for YAML frontmatter
            if content.startswith('---\n'):
                # Find the end of frontmatter
                end_match = re.search(r'\n---\n', content[4:])
                if end_match:
                    return content[end_match.end() + 4:]
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to remove frontmatter: {e}")
            return content
    
    def _create_content_with_frontmatter(self, content: str, metadata: Dict[str, Any]) -> str:
        """Create content with frontmatter
        
        Args:
            content: The content without frontmatter
            metadata: Dictionary containing metadata
            
        Returns:
            Content with frontmatter
        """
        try:
            # Remove empty values
            filtered_metadata = {k: v for k, v in metadata.items() if v is not None and v != ''}
            
            if not filtered_metadata:
                return content
            
            # Create YAML frontmatter
            yaml_content = yaml.dump(
                filtered_metadata,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
            
            # Combine frontmatter and content
            return f"---\n{yaml_content}---\n\n{content}"
            
        except Exception as e:
            logger.error(f"Failed to create content with frontmatter: {e}")
            return content
    
    def _should_include_field(self, field: str) -> bool:
        """Check if a field should be included in metadata
        
        Args:
            field: The field name to check
            
        Returns:
            True if field should be included
        """
        return field in self.include_fields
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for frontmatter
        
        Args:
            timestamp: The timestamp string
            
        Returns:
            Formatted timestamp
        """
        try:
            # Parse various timestamp formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%f%z',
                '%Y-%m-%dT%H:%M:%S%z'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # If no format matches, return as-is
            return timestamp
            
        except Exception as e:
            logger.error(f"Failed to format timestamp {timestamp}: {e}")
            return timestamp
    
    def create_metadata_summary(self, metadata: Dict[str, Any], content_type: str = 'page') -> Dict[str, Any]:
        """Create a summary of metadata for logging/debugging
        
        Args:
            metadata: The metadata dictionary
            content_type: Type of content ('page' or 'attachment')
            
        Returns:
            Summary dictionary
        """
        summary = {
            'content_type': content_type,
            'metadata_fields': len(metadata),
            'fields': list(metadata.keys())
        }
        
        if content_type == 'page':
            summary['page_title'] = metadata.get('page_title', 'Unknown')
            summary['space'] = metadata.get('space_key', 'Unknown')
        elif content_type == 'attachment':
            summary['attachment_name'] = metadata.get('attachment_filename', 'Unknown')
            summary['parent_page'] = metadata.get('parent_page', {}).get('page_title', 'Unknown')
        
        return summary
```

### Testing Requirements

```python
# tests/test_metadata_enricher.py

import pytest
from confluence_markdown_exporter.processors.metadata_enricher import MetadataEnricher

class TestMetadataEnricher:
    @pytest.fixture
    def enricher(self):
        return MetadataEnricher()
    
    @pytest.fixture
    def page_metadata(self):
        return {
            'page_id': '123',
            'page_title': 'Test Page',
            'page_url': 'https://test.com/pages/123',
            'space_key': 'TEST',
            'space_name': 'Test Space',
            'space_url': 'https://test.com/spaces/TEST',
            'homepage_title': 'Home',
            'ancestor_titles': ['Parent 1', 'Parent 2'],
            'author': {
                'username': 'jsmith',
                'display_name': 'John Smith',
                'email': 'john@example.com'
            },
            'created': '2024-01-01T10:00:00.000Z',
            'updated': '2024-01-01T12:00:00.000Z',
            'version': 1
        }
    
    @pytest.fixture
    def attachment_metadata(self):
        return {
            'attachment_id': 'att123',
            'attachment_filename': 'test.pdf',
            'attachment_url': 'https://test.com/attachments/att123',
            'attachment_size': 1024,
            'attachment_media_type': 'application/pdf',
            'attachment_author': {
                'username': 'jsmith',
                'display_name': 'John Smith',
                'email': 'john@example.com'
            },
            'attachment_created': '2024-01-01T10:00:00.000Z',
            'attachment_updated': '2024-01-01T12:00:00.000Z',
            'parent_page': {
                'page_id': '123',
                'page_title': 'Parent Page',
                'space_key': 'TEST',
                'space_name': 'Test Space'
            }
        }
    
    def test_enrich_page_content(self, enricher, page_metadata):
        content = "# Test Page\n\nThis is test content."
        
        enriched = enricher.enrich_page_content(content, page_metadata)
        
        assert enriched.startswith('---\n')
        assert 'confluence_page_name: Test Page' in enriched
        assert 'confluence_space: TEST' in enriched
        assert 'confluence_space_name: Test Space' in enriched
        assert 'confluence_author: John Smith' in enriched
        assert '# Test Page' in enriched
    
    def test_enrich_attachment_content(self, enricher, attachment_metadata):
        content = "This is attachment content."
        
        enriched = enricher.enrich_attachment_content(content, attachment_metadata)
        
        assert enriched.startswith('---\n')
        assert 'confluence_attachment_name: test.pdf' in enriched
        assert 'confluence_attachment_size: 1024' in enriched
        assert 'confluence_page_name: Parent Page' in enriched
        assert 'This is attachment content.' in enriched
    
    def test_extract_existing_frontmatter(self, enricher):
        content = """---
title: Existing Title
tags: [test, demo]
---

# Content

This is the content."""
        
        frontmatter = enricher._extract_frontmatter(content)
        assert frontmatter['title'] == 'Existing Title'
        assert frontmatter['tags'] == ['test', 'demo']
        
        content_without = enricher._remove_frontmatter(content)
        assert content_without.startswith('# Content')
    
    def test_merge_with_existing_frontmatter(self, enricher, page_metadata):
        content = """---
title: Existing Title
tags: [test, demo]
---

# Content

This is the content."""
        
        enriched = enricher.enrich_page_content(content, page_metadata)
        
        assert 'title: Existing Title' in enriched
        assert 'tags:\n- test\n- demo' in enriched
        assert 'confluence_page_name: Test Page' in enriched
    
    def test_format_timestamp(self, enricher):
        timestamp = '2024-01-01T10:00:00.000Z'
        formatted = enricher._format_timestamp(timestamp)
        assert formatted == '2024-01-01T10:00:00'
    
    def test_metadata_field_filtering(self):
        enricher = MetadataEnricher(include_fields=['space', 'author'])
        
        metadata = {
            'space_key': 'TEST',
            'space_name': 'Test Space',
            'page_title': 'Test Page',
            'author': {'display_name': 'John Smith'}
        }
        
        formatted = enricher._generate_page_metadata(metadata)
        
        assert 'confluence_space' in formatted
        assert 'confluence_author' in formatted
        assert 'confluence_page_name' not in formatted  # Should be filtered out
    
    def test_create_metadata_summary(self, enricher, page_metadata):
        summary = enricher.create_metadata_summary(page_metadata, 'page')
        
        assert summary['content_type'] == 'page'
        assert summary['page_title'] == 'Test Page'
        assert summary['space'] == 'TEST'
        assert 'metadata_fields' in summary
        assert 'fields' in summary
```

## Deliverables

1. **Extended Confluence API Client** (`confluence_client.py`)
   - New methods for space, page, and attachment metadata retrieval
   - URL building utilities
   - Complete metadata compilation methods

2. **Metadata Enricher** (`metadata_enricher.py`)
   - Frontmatter generation and management
   - Page and attachment metadata formatting
   - Configurable field inclusion
   - Timestamp formatting utilities

3. **Test Suite**
   - Unit tests for all new API methods
   - Integration tests for metadata compilation
   - Frontmatter processing tests
   - Error handling validation

## Success Criteria

- [ ] Extended Confluence API client retrieves all required metadata
- [ ] Metadata enricher adds comprehensive frontmatter to files
- [ ] Existing frontmatter is preserved and merged
- [ ] Timestamps are formatted correctly
- [ ] Author information is extracted properly
- [ ] Space and page hierarchies are captured
- [ ] Attachment metadata includes parent page information
- [ ] URL generation works for all content types
- [ ] Field filtering works as configured
- [ ] All tests pass with >90% coverage
- [ ] Error handling is robust and informative
