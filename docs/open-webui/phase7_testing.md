# Phase 7: Testing and Quality Assurance

## Overview
Implement comprehensive testing strategies, performance validation, and quality assurance measures to ensure a robust, production-ready Open-WebUI integration.

## Task 7.1: Comprehensive Testing Suite

### Objective
Create a complete testing framework covering unit tests, integration tests, end-to-end tests, and performance tests for the Open-WebUI integration.

### Files to Create
- `tests/integration/test_open_webui_integration.py` (create)
- `tests/performance/test_export_performance.py` (create)
- `tests/end_to_end/test_complete_workflow.py` (create)
- `tests/fixtures/open_webui_fixtures.py` (create)
- `tests/mocks/open_webui_mocks.py` (create)
- `pytest.ini` (update)
- `tox.ini` (create)

### Requirements
- Complete test coverage for all Open-WebUI components
- Integration tests with mocked and real services
- Performance benchmarks and stress tests
- End-to-end workflow validation
- Test data fixtures and factories
- Continuous integration compatibility

### Reference Implementation

```python
# tests/integration/test_open_webui_integration.py

"""
Integration tests for Open-WebUI functionality.
Tests the complete integration flow with mocked services.
"""

import pytest
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from confluence_markdown_exporter.clients.open_webui_client import OpenWebUIClient, OpenWebUIClientError
from confluence_markdown_exporter.clients.confluence_client import ConfluenceClient
from confluence_markdown_exporter.processors.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.processors.metadata_enricher import MetadataEnricher
from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.models.open_webui_models import OpenWebUIKnowledge, OpenWebUIFile
from confluence_markdown_exporter.utils.open_webui_logger import OpenWebUILogger

class TestOpenWebUIIntegration:
    """Integration tests for Open-WebUI functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_open_webui_client(self):
        """Mock Open-WebUI client"""
        client = Mock(spec=OpenWebUIClient)
        
        # Mock knowledge base operations
        knowledge_base = OpenWebUIKnowledge(
            id="kb_test_123",
            name="Test Space",
            description="Test Description",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        client.create_or_get_knowledge_base.return_value = knowledge_base
        client.find_knowledge_base_by_name.return_value = knowledge_base
        
        # Mock file operations
        test_file = OpenWebUIFile(
            id="file_test_123",
            filename="test.md",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        client.create_or_update_file.return_value = test_file
        client.upload_file.return_value = test_file
        
        # Mock other operations
        client.test_connection.return_value = True
        client.batch_add_files_to_knowledge.return_value = True
        client.add_file_to_knowledge.return_value = True
        
        return client
    
    @pytest.fixture
    def mock_confluence_client(self):
        """Mock Confluence client"""
        client = Mock(spec=ConfluenceClient)
        
        # Mock space details
        client.get_space_details.return_value = {
            "key": "TEST",
            "name": "Test Space",
            "homepageId": "123"
        }
        
        # Mock page metadata
        client.get_complete_page_metadata.return_value = {
            "page_id": "123",
            "page_title": "Test Page",
            "space_key": "TEST",
            "space_name": "Test Space",
            "author": {"display_name": "Test User"},
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z"
        }
        
        # Mock attachment metadata
        client.get_complete_attachment_metadata.return_value = {
            "attachment_id": "att123",
            "attachment_filename": "test.pdf",
            "attachment_size": 1024,
            "parent_page": {
                "page_id": "123",
                "page_title": "Test Page"
            }
        }
        
        client.build_space_url.return_value = "https://test.com/spaces/TEST"
        
        return client
    
    @pytest.fixture
    def sample_pages(self):
        """Sample pages for testing"""
        return [
            {
                "id": "123",
                "title": "Test Page 1",
                "space": {"key": "TEST"}
            },
            {
                "id": "124", 
                "title": "Test Page 2",
                "space": {"key": "TEST"}
            }
        ]
    
    @pytest.fixture
    def sample_attachments(self):
        """Sample attachments for testing"""
        return [
            {
                "id": "att123",
                "title": "document.pdf",
                "filename": "document.pdf",
                "size": 1024
            },
            {
                "id": "att124",
                "title": "image.jpg", 
                "filename": "image.jpg",
                "size": 2048
            }
        ]
    
    def test_complete_export_workflow(self, temp_dir, mock_open_webui_client, 
                                    mock_confluence_client, sample_pages, sample_attachments):
        """Test complete export workflow"""
        
        # Setup
        attachment_filter = AttachmentFilter("pdf,jpg")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=mock_open_webui_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher
        )
        
        # Create test files
        test_output_dir = Path(temp_dir) / "TEST"
        test_output_dir.mkdir(parents=True)
        
        # Create test page files
        (test_output_dir / "Test Page 1.md").write_text("# Test Page 1\n\nContent")
        (test_output_dir / "Test Page 2.md").write_text("# Test Page 2\n\nContent")
        
        # Create attachments directory
        attachments_dir = test_output_dir / "attachments"
        attachments_dir.mkdir()
        (attachments_dir / "document.pdf").write_bytes(b"PDF content")
        (attachments_dir / "image.jpg").write_bytes(b"JPG content")
        
        # Execute export
        summary = exporter.export_space("TEST", temp_dir, sample_pages, sample_attachments)
        
        # Verify results
        assert summary.knowledge_base_name == "Test Space"
        assert summary.total_pages == 2
        assert summary.total_attachments == 2
        assert summary.successful_pages == 2
        assert summary.successful_attachments == 2
        assert summary.failed_pages == 0
        assert summary.failed_attachments == 0
        
        # Verify API calls
        mock_open_webui_client.create_or_get_knowledge_base.assert_called_once()
        assert mock_open_webui_client.create_or_update_file.call_count == 4  # 2 pages + 2 attachments
        mock_open_webui_client.batch_add_files_to_knowledge.assert_called_once()
    
    def test_export_with_filtered_attachments(self, temp_dir, mock_open_webui_client,
                                            mock_confluence_client, sample_pages, sample_attachments):
        """Test export with attachment filtering"""
        
        # Setup filter to only allow PDF files
        attachment_filter = AttachmentFilter("pdf")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=mock_open_webui_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher
        )
        
        # Create test files
        test_output_dir = Path(temp_dir) / "TEST"
        test_output_dir.mkdir(parents=True)
        
        # Create test page files
        (test_output_dir / "Test Page 1.md").write_text("# Test Page 1\n\nContent")
        (test_output_dir / "Test Page 2.md").write_text("# Test Page 2\n\nContent")
        
        # Create attachments directory
        attachments_dir = test_output_dir / "attachments"
        attachments_dir.mkdir()
        (attachments_dir / "document.pdf").write_bytes(b"PDF content")
        (attachments_dir / "image.jpg").write_bytes(b"JPG content")
        
        # Execute export
        summary = exporter.export_space("TEST", temp_dir, sample_pages, sample_attachments)
        
        # Verify results - only 1 attachment should be processed (PDF)
        assert summary.total_attachments == 1  # Only PDF should be processed
        assert summary.successful_attachments == 1
        
        # Verify API calls - 2 pages + 1 attachment
        assert mock_open_webui_client.create_or_update_file.call_count == 3
    
    def test_export_with_metadata_enrichment(self, temp_dir, mock_open_webui_client,
                                           mock_confluence_client, sample_pages):
        """Test export with metadata enrichment"""
        
        attachment_filter = AttachmentFilter("pdf")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=mock_open_webui_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher
        )
        
        # Create test files
        test_output_dir = Path(temp_dir) / "TEST"
        test_output_dir.mkdir(parents=True)
        (test_output_dir / "Test Page 1.md").write_text("# Test Page 1\n\nContent")
        
        # Execute export
        summary = exporter.export_space("TEST", temp_dir, sample_pages[:1], [])
        
        # Verify metadata enrichment was called
        uploaded_content = mock_open_webui_client.create_or_update_file.call_args[0][1]
        
        # Should contain frontmatter with metadata
        assert "---" in uploaded_content
        assert "confluence_page_name: Test Page 1" in uploaded_content
        assert "confluence_space: TEST" in uploaded_content
        assert "confluence_author: Test User" in uploaded_content
    
    def test_export_error_handling(self, temp_dir, mock_confluence_client, sample_pages):
        """Test export error handling"""
        
        # Setup client that fails
        failing_client = Mock(spec=OpenWebUIClient)
        failing_client.create_or_get_knowledge_base.side_effect = OpenWebUIClientError("Connection failed")
        
        attachment_filter = AttachmentFilter("pdf")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=failing_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher
        )
        
        # Execute export
        summary = exporter.export_space("TEST", temp_dir, sample_pages, [])
        
        # Should handle error gracefully
        assert summary.failed_pages > 0
        assert len(summary.errors) > 0
    
    def test_batch_vs_individual_upload(self, temp_dir, mock_open_webui_client,
                                      mock_confluence_client, sample_pages):
        """Test batch vs individual upload modes"""
        
        attachment_filter = AttachmentFilter("pdf")
        metadata_enricher = MetadataEnricher()
        
        # Test batch upload
        exporter_batch = OpenWebUIExporter(
            open_webui_client=mock_open_webui_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=True
        )
        
        # Test individual upload
        exporter_individual = OpenWebUIExporter(
            open_webui_client=mock_open_webui_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=False
        )
        
        # Create test files
        test_output_dir = Path(temp_dir) / "TEST"
        test_output_dir.mkdir(parents=True)
        (test_output_dir / "Test Page 1.md").write_text("# Test Page 1\n\nContent")
        (test_output_dir / "Test Page 2.md").write_text("# Test Page 2\n\nContent")
        
        # Test batch upload
        mock_open_webui_client.reset_mock()
        exporter_batch.export_space("TEST", temp_dir, sample_pages, [])
        
        # Should use batch upload
        mock_open_webui_client.batch_add_files_to_knowledge.assert_called_once()
        mock_open_webui_client.add_file_to_knowledge.assert_not_called()
        
        # Test individual upload
        mock_open_webui_client.reset_mock()
        exporter_individual.export_space("TEST", temp_dir, sample_pages, [])
        
        # Should use individual upload
        mock_open_webui_client.batch_add_files_to_knowledge.assert_not_called()
        assert mock_open_webui_client.add_file_to_knowledge.call_count == 2

class TestOpenWebUIClientIntegration:
    """Integration tests for Open-WebUI client"""
    
    @pytest.fixture
    def mock_requests(self):
        """Mock requests for HTTP calls"""
        with patch('requests.Session') as mock_session:
            mock_instance = Mock()
            mock_session.return_value = mock_instance
            yield mock_instance
    
    def test_client_initialization(self):
        """Test client initialization"""
        client = OpenWebUIClient("https://test.com", "test-key")
        
        assert client.base_url == "https://test.com"
        assert client.api_key == "test-key"
        assert "Bearer test-key" in client.session.headers['Authorization']
    
    def test_connection_test(self, mock_requests):
        """Test connection testing"""
        client = OpenWebUIClient("https://test.com", "test-key")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_requests.request.return_value = mock_response
        
        result = client.test_connection()
        assert result == True
        
        # Mock failed response
        mock_requests.request.side_effect = Exception("Connection failed")
        result = client.test_connection()
        assert result == False
    
    def test_knowledge_base_operations(self, mock_requests):
        """Test knowledge base operations"""
        client = OpenWebUIClient("https://test.com", "test-key")
        
        # Mock list knowledge bases
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "kb1",
                "name": "Test KB",
                "description": "Test Description",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_requests.request.return_value = mock_response
        
        knowledge_bases = client.list_knowledge_bases()
        assert len(knowledge_bases) == 1
        assert knowledge_bases[0].name == "Test KB"
        
        # Mock find by name
        kb = client.find_knowledge_base_by_name("Test KB")
        assert kb is not None
        assert kb.name == "Test KB"
        
        # Mock not found
        kb = client.find_knowledge_base_by_name("Non-existent KB")
        assert kb is None
    
    def test_file_operations(self, mock_requests):
        """Test file operations"""
        client = OpenWebUIClient("https://test.com", "test-key")
        
        # Mock file upload
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "file1",
                "filename": "test.md",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
            mock_post.return_value = mock_response
            
            file_obj = client.upload_file("test.md", "content", "text/markdown")
            assert file_obj.filename == "test.md"
            assert file_obj.id == "file1"
    
    def test_error_handling(self, mock_requests):
        """Test error handling"""
        client = OpenWebUIClient("https://test.com", "test-key")
        
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_requests.request.return_value = mock_response
        
        with pytest.raises(OpenWebUIClientError):
            client.list_knowledge_bases()
```

```python
# tests/performance/test_export_performance.py

"""
Performance tests for Open-WebUI export operations.
Tests performance benchmarks and stress testing.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.processors.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.processors.metadata_enricher import MetadataEnricher

class TestExportPerformance:
    """Performance tests for export operations"""
    
    @pytest.fixture
    def mock_clients(self):
        """Mock clients for performance testing"""
        open_webui_client = Mock(spec=OpenWebUIClient)
        confluence_client = Mock()
        
        # Mock fast responses
        open_webui_client.create_or_get_knowledge_base.return_value = Mock(id="kb1", name="Test KB")
        open_webui_client.create_or_update_file.return_value = Mock(id="file1", filename="test.md")
        open_webui_client.batch_add_files_to_knowledge.return_value = True
        
        confluence_client.get_space_details.return_value = {"name": "Test Space"}
        confluence_client.get_complete_page_metadata.return_value = {"page_title": "Test Page"}
        confluence_client.build_space_url.return_value = "https://test.com"
        
        return open_webui_client, confluence_client
    
    def test_single_page_export_performance(self, mock_clients):
        """Test single page export performance"""
        open_webui_client, confluence_client = mock_clients
        
        attachment_filter = AttachmentFilter("md")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher
        )
        
        # Create test data
        pages = [{"id": "1", "title": "Test Page"}]
        
        # Time the export
        start_time = time.time()
        summary = exporter.export_space("TEST", "/tmp", pages, [])
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Assert performance (should be fast with mocked clients)
        assert duration < 1.0  # Should complete in under 1 second
        assert summary.successful_pages == 1
    
    def test_batch_export_performance(self, mock_clients):
        """Test batch export performance with multiple pages"""
        open_webui_client, confluence_client = mock_clients
        
        attachment_filter = AttachmentFilter("md")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=True
        )
        
        # Create test data - 100 pages
        pages = [{"id": str(i), "title": f"Test Page {i}"} for i in range(100)]
        
        # Time the export
        start_time = time.time()
        summary = exporter.export_space("TEST", "/tmp", pages, [])
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Assert performance
        assert duration < 5.0  # Should complete in under 5 seconds
        assert summary.successful_pages == 100
        
        # Verify batch upload was used
        open_webui_client.batch_add_files_to_knowledge.assert_called_once()
    
    def test_individual_vs_batch_upload_performance(self, mock_clients):
        """Compare individual vs batch upload performance"""
        open_webui_client, confluence_client = mock_clients
        
        attachment_filter = AttachmentFilter("md")
        metadata_enricher = MetadataEnricher()
        
        # Test data
        pages = [{"id": str(i), "title": f"Test Page {i}"} for i in range(50)]
        
        # Test batch upload
        exporter_batch = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=True
        )
        
        start_time = time.time()
        summary_batch = exporter_batch.export_space("TEST", "/tmp", pages, [])
        batch_duration = time.time() - start_time
        
        # Reset mocks
        open_webui_client.reset_mock()
        
        # Test individual upload
        exporter_individual = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=False
        )
        
        start_time = time.time()
        summary_individual = exporter_individual.export_space("TEST", "/tmp", pages, [])
        individual_duration = time.time() - start_time
        
        # Both should succeed
        assert summary_batch.successful_pages == 50
        assert summary_individual.successful_pages == 50
        
        # Batch should be faster (or at least not significantly slower)
        assert batch_duration <= individual_duration * 1.5  # Allow 50% tolerance
    
    def test_memory_usage_large_export(self, mock_clients):
        """Test memory usage for large exports"""
        open_webui_client, confluence_client = mock_clients
        
        attachment_filter = AttachmentFilter("md")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher
        )
        
        # Create large test data - 1000 pages
        pages = [{"id": str(i), "title": f"Test Page {i}"} for i in range(1000)]
        
        # Monitor memory usage (simplified)
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute export
        summary = exporter.export_space("TEST", "/tmp", pages, [])
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Assert reasonable memory usage
        assert memory_increase < 100  # Should not increase by more than 100MB
        assert summary.successful_pages == 1000
    
    def test_concurrent_exports(self, mock_clients):
        """Test concurrent export operations"""
        open_webui_client, confluence_client = mock_clients
        
        attachment_filter = AttachmentFilter("md")
        metadata_enricher = MetadataEnricher()
        
        def export_space(space_key, pages):
            """Export a space"""
            exporter = OpenWebUIExporter(
                open_webui_client=open_webui_client,
                confluence_client=confluence_client,
                attachment_filter=attachment_filter,
                metadata_enricher=metadata_enricher
            )
            return exporter.export_space(space_key, "/tmp", pages, [])
        
        # Create test data for multiple spaces
        spaces_data = [
            ("SPACE1", [{"id": f"1_{i}", "title": f"Page {i}"} for i in range(10)]),
            ("SPACE2", [{"id": f"2_{i}", "title": f"Page {i}"} for i in range(10)]),
            ("SPACE3", [{"id": f"3_{i}", "title": f"Page {i}"} for i in range(10)])
        ]
        
        # Run concurrent exports
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(export_space, space_key, pages)
                for space_key, pages in spaces_data
            ]
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assert all exports succeeded
        assert len(results) == 3
        for result in results:
            assert result.successful_pages == 10
        
        # Should complete reasonably quickly
        assert duration < 10.0  # Should complete in under 10 seconds
    
    @pytest.mark.slow
    def test_stress_test_large_files(self, mock_clients):
        """Stress test with large files"""
        open_webui_client, confluence_client = mock_clients
        
        # Mock large file content
        large_content = "x" * (1024 * 1024)  # 1MB content
        
        # Mock file reading to return large content
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', create=True) as mock_open:
            
            mock_file = Mock()
            mock_file.read.return_value = large_content
            mock_open.return_value.__enter__.return_value = mock_file
            
            attachment_filter = AttachmentFilter("md")
            metadata_enricher = MetadataEnricher()
            
            exporter = OpenWebUIExporter(
                open_webui_client=open_webui_client,
                confluence_client=confluence_client,
                attachment_filter=attachment_filter,
                metadata_enricher=metadata_enricher
            )
            
            # Create test data with large pages
            pages = [{"id": str(i), "title": f"Large Page {i}"} for i in range(10)]
            
            start_time = time.time()
            summary = exporter.export_space("TEST", "/tmp", pages, [])
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Assert performance with large files
            assert duration < 30.0  # Should complete in under 30 seconds
            assert summary.successful_pages == 10

class TestAttachmentFilterPerformance:
    """Performance tests for attachment filtering"""
    
    def test_large_attachment_list_filtering(self):
        """Test filtering performance with large attachment lists"""
        filter_obj = AttachmentFilter("md,txt,pdf")
        
        # Create large attachment list
        attachments = [
            {"filename": f"file_{i}.{'md' if i % 3 == 0 else 'txt' if i % 3 == 1 else 'jpg'}", "size": 1024}
            for i in range(10000)
        ]
        
        start_time = time.time()
        result = filter_obj.filter_attachments(attachments)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should filter quickly
        assert duration < 1.0  # Should complete in under 1 second
        assert len(result['allowed']) > 0
        assert len(result['filtered']) > 0
    
    def test_extension_parsing_performance(self):
        """Test extension parsing performance"""
        # Large extension list
        extensions = ",".join([f"ext{i}" for i in range(1000)])
        
        start_time = time.time()
        filter_obj = AttachmentFilter(extensions)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should parse quickly
        assert duration < 0.1  # Should complete in under 0.1 seconds
        assert len(filter_obj.allowed_extensions) == 1000

class TestMetadataEnricherPerformance:
    """Performance tests for metadata enrichment"""
    
    def test_large_content_enrichment(self):
        """Test metadata enrichment with large content"""
        enricher = MetadataEnricher()
        
        # Large content
        large_content = "# Large Page\n\n" + "Content paragraph. " * 10000
        
        metadata = {
            "page_title": "Large Page",
            "space_key": "TEST",
            "space_name": "Test Space",
            "author": {"display_name": "Test User"},
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z"
        }
        
        start_time = time.time()
        enriched_content = enricher.enrich_page_content(large_content, metadata)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should enrich quickly
        assert duration < 1.0  # Should complete in under 1 second
        assert "confluence_page_name: Large Page" in enriched_content
        assert len(enriched_content) > len(large_content)  # Should have added metadata
    
    def test_batch_metadata_enrichment(self):
        """Test batch metadata enrichment"""
        enricher = MetadataEnricher()
        
        # Multiple content items
        contents = [f"# Page {i}\n\nContent for page {i}" for i in range(100)]
        metadatas = [
            {
                "page_title": f"Page {i}",
                "space_key": "TEST",
                "author": {"display_name": "Test User"}
            }
            for i in range(100)
        ]
        
        start_time = time.time()
        enriched_contents = [
            enricher.enrich_page_content(content, metadata)
            for content, metadata in zip(contents, metadatas)
        ]
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should enrich batch quickly
        assert duration < 5.0  # Should complete in under 5 seconds
        assert len(enriched_contents) == 100
        
        # Verify all were enriched
        for i, enriched in enumerate(enriched_contents):
            assert f"confluence_page_name: Page {i}" in enriched
```

```python
# tests/end_to_end/test_complete_workflow.py

"""
End-to-end tests for the complete Open-WebUI integration workflow.
Tests the entire process from configuration to export completion.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from confluence_markdown_exporter.main import ConfluenceMarkdownExporter
from confluence_markdown_exporter.config.config_manager import ConfigManager

class TestCompleteWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        yield config_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            "auth": {
                "confluence": {
                    "url": "https://test.atlassian.net",
                    "username": "test@example.com",
                    "api_token": "test-token"
                },
                "open_webui": {
                    "url": "https://openwebui.test.com",
                    "api_key": "test-api-key"
                }
            },
            "export": {
                "export_to_open_webui": True,
                "open_webui_attachment_extensions": "md,txt,pdf",
                "open_webui_batch_add": True,
                "include_document_title": True,
                "page_breadcrumbs": True
            },
            "retry_config": {
                "backoff_and_retry": True,
                "max_backoff_retries": 3
            }
        }
    
    def test_complete_space_export_workflow(self, temp_config_dir, temp_output_dir, sample_config):
        """Test complete space export workflow"""
        
        # Create config file
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Mock all external dependencies
        with patch('confluence_markdown_exporter.clients.confluence_client.ConfluenceClient') as mock_confluence, \
             patch('confluence_markdown_exporter.clients.open_webui_client.OpenWebUIClient') as mock_openwebui, \
             patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._get_space_pages') as mock_get_pages, \
             patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._get_space_attachments') as mock_get_attachments, \
             patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._export_space_to_markdown') as mock_export_md:
            
            # Setup mocks
            mock_confluence_instance = Mock()
            mock_confluence.return_value = mock_confluence_instance
            mock_confluence_instance.test_connection.return_value = True
            
            mock_openwebui_instance = Mock()
            mock_openwebui.return_value = mock_openwebui_instance
            mock_openwebui_instance.test_connection.return_value = True
            
            mock_get_pages.return_value = [
                {"id": "123", "title": "Test Page 1"},
                {"id": "124", "title": "Test Page 2"}
            ]
            
            mock_get_attachments.return_value = [
                {"id": "att123", "title": "document.pdf", "filename": "document.pdf"}
            ]
            
            mock_export_md.return_value = True
            
            # Create test markdown files
            space_dir = Path(temp_output_dir) / "TESTSPACE"
            space_dir.mkdir(parents=True)
            (space_dir / "Test Page 1.md").write_text("# Test Page 1\n\nContent")
            (space_dir / "Test Page 2.md").write_text("# Test Page 2\n\nContent")
            
            attachments_dir = space_dir / "attachments"
            attachments_dir.mkdir()
            (attachments_dir / "document.pdf").write_bytes(b"PDF content")
            
            # Initialize exporter
            with patch.dict('os.environ', {'CME_CONFIG_PATH': str(config_file)}):
                config_manager = ConfigManager(str(config_file))
                exporter = ConfluenceMarkdownExporter(config_manager)
                
                # Execute export
                result = exporter.export_space("TESTSPACE", temp_output_dir)
                
                # Verify results
                assert result == True
                
                # Verify markdown export was called
                mock_export_md.assert_called_once_with("TESTSPACE", temp_output_dir)
                
                # Verify Open-WebUI components were initialized
                mock_openwebui.assert_called_once()
                mock_openwebui_instance.test_connection.assert_called()
    
    def test_configuration_validation_workflow(self, temp_config_dir, sample_config):
        """Test configuration validation workflow"""
        
        # Test with invalid config
        invalid_config = sample_config.copy()
        invalid_config["auth"]["open_webui"]["api_key"] = ""  # Invalid empty API key
        
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        with patch.dict('os.environ', {'CME_CONFIG_PATH': str(config_file)}):
            config_manager = ConfigManager(str(config_file))
            
            # Should detect invalid configuration
            with patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._initialize_open_webui_components') as mock_init:
                mock_init.return_value = None  # Simulate initialization failure
                
                exporter = ConfluenceMarkdownExporter(config_manager)
                
                # Should not have Open-WebUI components
                assert exporter.open_webui_exporter is None
    
    def test_connection_failure_workflow(self, temp_config_dir, temp_output_dir, sample_config):
        """Test workflow when connections fail"""
        
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Mock connection failures
        with patch('confluence_markdown_exporter.clients.confluence_client.ConfluenceClient') as mock_confluence, \
             patch('confluence_markdown_exporter.clients.open_webui_client.OpenWebUIClient') as mock_openwebui:
            
            mock_confluence_instance = Mock()
            mock_confluence.return_value = mock_confluence_instance
            mock_confluence_instance.test_connection.return_value = False  # Connection fails
            
            mock_openwebui_instance = Mock()
            mock_openwebui.return_value = mock_openwebui_instance
            mock_openwebui_instance.test_connection.return_value = False  # Connection fails
            
            with patch.dict('os.environ', {'CME_CONFIG_PATH': str(config_file)}):
                config_manager = ConfigManager(str(config_file))
                exporter = ConfluenceMarkdownExporter(config_manager)
                
                # Should handle connection failures gracefully
                assert exporter.open_webui_exporter is None
    
    def test_partial_export_success_workflow(self, temp_config_dir, temp_output_dir, sample_config):
        """Test workflow when some exports succeed and others fail"""
        
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        with patch('confluence_markdown_exporter.clients.confluence_client.ConfluenceClient') as mock_confluence, \
             patch('confluence_markdown_exporter.clients.open_webui_client.OpenWebUIClient') as mock_openwebui, \
             patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._export_space_to_markdown') as mock_export_md:
            
            # Setup mocks
            mock_confluence_instance = Mock()
            mock_confluence.return_value = mock_confluence_instance
            mock_confluence_instance.test_connection.return_value = True
            
            mock_openwebui_instance = Mock()
            mock_openwebui.return_value = mock_openwebui_instance
            mock_openwebui_instance.test_connection.return_value = True
            
            mock_export_md.return_value = True  # Markdown export succeeds
            
            # Mock partial Open-WebUI export failure
            with patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._export_space_to_open_webui') as mock_export_owui:
                mock_export_owui.return_value = False  # Open-WebUI export fails
                
                with patch.dict('os.environ', {'CME_CONFIG_PATH': str(config_file)}):
                    config_manager = ConfigManager(str(config_file))
                    exporter = ConfluenceMarkdownExporter(config_manager)
                    
                    # Export should still succeed (markdown export worked)
                    result = exporter.export_space("TESTSPACE", temp_output_dir)
                    
                    # Should succeed overall (markdown export succeeded)
                    assert result == True
    
    def test_cli_integration_workflow(self, temp_config_dir, sample_config):
        """Test CLI integration workflow"""
        
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Mock CLI components
        with patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter') as mock_exporter_class, \
             patch('confluence_markdown_exporter.main.ConfigManager') as mock_config_manager, \
             patch('sys.argv', ['confluence-markdown-exporter', 'test-connection']):
            
            mock_config_manager_instance = Mock()
            mock_config_manager.return_value = mock_config_manager_instance
            
            mock_exporter_instance = Mock()
            mock_exporter_class.return_value = mock_exporter_instance
            mock_exporter_instance.test_open_webui_connection.return_value = True
            
            # Import and run main
            from confluence_markdown_exporter.main import main
            
            # Should not raise exception
            try:
                main()
            except SystemExit as e:
                # Should exit with success code
                assert e.code in [None, 0]
    
    def test_error_recovery_workflow(self, temp_config_dir, temp_output_dir, sample_config):
        """Test error recovery workflow"""
        
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        with patch('confluence_markdown_exporter.clients.confluence_client.ConfluenceClient') as mock_confluence, \
             patch('confluence_markdown_exporter.clients.open_webui_client.OpenWebUIClient') as mock_openwebui:
            
            mock_confluence_instance = Mock()
            mock_confluence.return_value = mock_confluence_instance
            mock_confluence_instance.test_connection.return_value = True
            
            mock_openwebui_instance = Mock()
            mock_openwebui.return_value = mock_openwebui_instance
            mock_openwebui_instance.test_connection.return_value = True
            
            # Mock first export attempt fails, second succeeds
            with patch('confluence_markdown_exporter.main.ConfluenceMarkdownExporter._export_space_to_open_webui') as mock_export:
                mock_export.side_effect = [False, True]  # First fails, second succeeds
                
                with patch.dict('os.environ', {'CME_CONFIG_PATH': str(config_file)}):
                    config_manager = ConfigManager(str(config_file))
                    exporter = ConfluenceMarkdownExporter(config_manager)
                    
                    # First export
                    result1 = exporter.export_space("TESTSPACE", temp_output_dir)
                    
                    # Second export (retry)
                    result2 = exporter.export_space("TESTSPACE", temp_output_dir)
                    
                    # Second attempt should succeed
                    assert result2 == True
    
    @pytest.mark.integration
    def test_real_configuration_workflow(self, temp_config_dir):
        """Test with real configuration (requires environment variables)"""
        
        import os
        
        # Skip if required environment variables are not set
        required_vars = ['TEST_CONFLUENCE_URL', 'TEST_CONFLUENCE_TOKEN', 'TEST_OPENWEBUI_URL', 'TEST_OPENWEBUI_KEY']
        if not all(var in os.environ for var in required_vars):
            pytest.skip("Integration test requires environment variables")
        
        # Create real configuration
        real_config = {
            "auth": {
                "confluence": {
                    "url": os.environ['TEST_CONFLUENCE_URL'],
                    "api_token": os.environ['TEST_CONFLUENCE_TOKEN']
                },
                "open_webui": {
                    "url": os.environ['TEST_OPENWEBUI_URL'],
                    "api_key": os.environ['TEST_OPENWEBUI_KEY']
                }
            },
            "export": {
                "export_to_open_webui": True,
                "open_webui_attachment_extensions": "md,txt",
                "open_webui_batch_add": True
            }
        }
        
        config_file = temp_config_dir / "app_data.json"
        with open(config_file, 'w') as f:
            json.dump(real_config, f)
        
        with patch.dict('os.environ', {'CME_CONFIG_PATH': str(config_file)}):
            config_manager = ConfigManager(str(config_file))
            exporter = ConfluenceMarkdownExporter(config_manager)
            
            # Test connections
            assert exporter.test_open_webui_connection() == True
            
            # Get status
            status = exporter.get_export_status()
            assert status['open_webui_configured'] == True
            assert status['open_webui_connected'] == True
```

```ini
# pytest.ini

[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests (may take several minutes)
    end_to_end: End-to-end tests
    real_api: Tests that require real API access
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
```

```ini
# tox.ini

[tox]
envlist = py39, py310, py311, py312, lint, type-check, coverage
isolated_build = True

[testenv]
deps = 
    pytest>=6.0
    pytest-cov
    pytest-mock
    pytest-xdist
    requests-mock
    psutil
commands = 
    pytest {posargs} tests/unit tests/integration

[testenv:performance]
deps = 
    {[testenv]deps}
    memory_profiler
commands = 
    pytest {posargs} tests/performance -m "not slow"

[testenv:slow]
deps = 
    {[testenv]deps}
    memory_profiler
commands = 
    pytest {posargs} tests/performance -m "slow"

[testenv:end_to_end]
deps = 
    {[testenv]deps}
commands = 
    pytest {posargs} tests/end_to_end

[testenv:lint]
deps = 
    flake8
    black
    isort
commands = 
    flake8 confluence_markdown_exporter tests
    black --check confluence_markdown_exporter tests
    isort --check-only confluence_markdown_exporter tests

[testenv:type-check]
deps = 
    mypy
    types-requests
    types-PyYAML
commands = 
    mypy confluence_markdown_exporter

[testenv:coverage]
deps = 
    {[testenv]deps}
    coverage[toml]
commands = 
    coverage erase
    coverage run -m pytest tests/unit tests/integration
    coverage report --show-missing
    coverage html
    coverage xml

[testenv:docs]
deps = 
    sphinx
    sphinx-rtd-theme
commands = 
    sphinx-build -b html docs docs/_build/html

[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .tox,
    .pytest_cache,
    build,
    dist,
    *.egg-info

[coverage:run]
source = confluence_markdown_exporter
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */.*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

## Task 7.2: Performance Benchmarking and Optimization

### Objective
Establish performance benchmarks, identify bottlenecks, and implement optimizations for the Open-WebUI integration.

### Files to Create
- `benchmarks/export_benchmarks.py` (create)
- `benchmarks/memory_profile.py` (create)
- `benchmarks/network_performance.py` (create)
- `tools/performance_analyzer.py` (create)
- `tools/benchmark_runner.py` (create)

### Requirements
- Establish baseline performance metrics
- Identify and resolve performance bottlenecks
- Memory usage optimization
- Network performance optimization
- Scalability testing
- Performance regression detection

### Reference Implementation

```python
# benchmarks/export_benchmarks.py

"""
Performance benchmarks for Open-WebUI export operations.
Establishes baseline performance metrics and identifies bottlenecks.
"""

import time
import psutil
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import os

from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.processors.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.processors.metadata_enricher import MetadataEnricher

@dataclass
class BenchmarkResult:
    """Benchmark result data"""
    test_name: str
    duration_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    files_processed: int
    files_per_second: float
    success_rate: float
    errors: List[str]
    metadata: Dict[str, Any]

class ExportBenchmark:
    """Benchmark suite for export operations"""
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = output_dir
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmark tests"""
        self.logger.info("Starting benchmark suite")
        
        benchmarks = [
            self.benchmark_single_page_export,
            self.benchmark_small_space_export,
            self.benchmark_medium_space_export,
            self.benchmark_large_space_export,
            self.benchmark_attachment_filtering,
            self.benchmark_metadata_enrichment,
            self.benchmark_batch_vs_individual,
            self.benchmark_concurrent_exports,
            self.benchmark_memory_usage,
            self.benchmark_network_performance
        ]
        
        for benchmark in benchmarks:
            try:
                result = benchmark()
                self.results.append(result)
                self.logger.info(f"Completed {result.test_name}: {result.duration_seconds:.2f}s")
            except Exception as e:
                self.logger.error(f"Benchmark {benchmark.__name__} failed: {e}")
        
        # Save results
        self.save_results()
        
        return self.results
    
    def benchmark_single_page_export(self) -> BenchmarkResult:
        """Benchmark single page export"""
        test_name = "single_page_export"
        
        # Setup
        pages = [{"id": "1", "title": "Test Page"}]
        attachments = []
        
        # Execute benchmark
        start_time = time.time()
        memory_before = self.process.memory_info().rss / 1024 / 1024
        cpu_before = self.process.cpu_percent()
        
        summary = self._run_mock_export("TEST", pages, attachments)
        
        end_time = time.time()
        memory_after = self.process.memory_info().rss / 1024 / 1024
        cpu_after = self.process.cpu_percent()
        
        duration = end_time - start_time
        memory_usage = memory_after - memory_before
        cpu_usage = cpu_after - cpu_before
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            files_processed=1,
            files_per_second=1 / duration if duration > 0 else 0,
            success_rate=summary.success_rate,
            errors=summary.errors,
            metadata={"pages": len(pages), "attachments": len(attachments)}
        )
    
    def benchmark_small_space_export(self) -> BenchmarkResult:
        """Benchmark small space export (10 pages)"""
        test_name = "small_space_export"
        
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(10)]
        attachments = [{"id": f"att{i}", "title": f"file{i}.pdf"} for i in range(5)]
        
        start_time = time.time()
        memory_before = self.process.memory_info().rss / 1024 / 1024
        
        summary = self._run_mock_export("SMALL", pages, attachments)
        
        end_time = time.time()
        memory_after = self.process.memory_info().rss / 1024 / 1024
        
        duration = end_time - start_time
        memory_usage = memory_after - memory_before
        total_files = len(pages) + len(attachments)
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0,  # Skip CPU measurement for simplicity
            files_processed=total_files,
            files_per_second=total_files / duration if duration > 0 else 0,
            success_rate=summary.success_rate,
            errors=summary.errors,
            metadata={"pages": len(pages), "attachments": len(attachments)}
        )
    
    def benchmark_medium_space_export(self) -> BenchmarkResult:
        """Benchmark medium space export (100 pages)"""
        test_name = "medium_space_export"
        
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(100)]
        attachments = [{"id": f"att{i}", "title": f"file{i}.pdf"} for i in range(50)]
        
        start_time = time.time()
        memory_before = self.process.memory_info().rss / 1024 / 1024
        
        summary = self._run_mock_export("MEDIUM", pages, attachments)
        
        end_time = time.time()
        memory_after = self.process.memory_info().rss / 1024 / 1024
        
        duration = end_time - start_time
        memory_usage = memory_after - memory_before
        total_files = len(pages) + len(attachments)
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0,
            files_processed=total_files,
            files_per_second=total_files / duration if duration > 0 else 0,
            success_rate=summary.success_rate,
            errors=summary.errors,
            metadata={"pages": len(pages), "attachments": len(attachments)}
        )
    
    def benchmark_large_space_export(self) -> BenchmarkResult:
        """Benchmark large space export (1000 pages)"""
        test_name = "large_space_export"
        
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(1000)]
        attachments = [{"id": f"att{i}", "title": f"file{i}.pdf"} for i in range(500)]
        
        start_time = time.time()
        memory_before = self.process.memory_info().rss / 1024 / 1024
        
        summary = self._run_mock_export("LARGE", pages, attachments)
        
        end_time = time.time()
        memory_after = self.process.memory_info().rss / 1024 / 1024
        
        duration = end_time - start_time
        memory_usage = memory_after - memory_before
        total_files = len(pages) + len(attachments)
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0,
            files_processed=total_files,
            files_per_second=total_files / duration if duration > 0 else 0,
            success_rate=summary.success_rate,
            errors=summary.errors,
            metadata={"pages": len(pages), "attachments": len(attachments)}
        )
    
    def benchmark_attachment_filtering(self) -> BenchmarkResult:
        """Benchmark attachment filtering performance"""
        test_name = "attachment_filtering"
        
        # Create large attachment list
        attachments = []
        for i in range(10000):
            ext = ["md", "txt", "pdf", "jpg", "png", "doc", "docx"][i % 7]
            attachments.append({
                "id": f"att{i}",
                "title": f"file{i}.{ext}",
                "filename": f"file{i}.{ext}",
                "size": 1024 * (i % 100 + 1)
            })
        
        filter_obj = AttachmentFilter("md,txt,pdf")
        
        start_time = time.time()
        memory_before = self.process.memory_info().rss / 1024 / 1024
        
        result = filter_obj.filter_attachments(attachments)
        
        end_time = time.time()
        memory_after = self.process.memory_info().rss / 1024 / 1024
        
        duration = end_time - start_time
        memory_usage = memory_after - memory_before
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0,
            files_processed=len(attachments),
            files_per_second=len(attachments) / duration if duration > 0 else 0,
            success_rate=100.0,
            errors=[],
            metadata={
                "total_attachments": len(attachments),
                "allowed_attachments": len(result['allowed']),
                "filtered_attachments": len(result['filtered'])
            }
        )
    
    def benchmark_metadata_enrichment(self) -> BenchmarkResult:
        """Benchmark metadata enrichment performance"""
        test_name = "metadata_enrichment"
        
        enricher = MetadataEnricher()
        
        # Create test data
        contents = []
        metadatas = []
        for i in range(1000):
            contents.append(f"# Page {i}\n\n" + "Content paragraph. " * 100)
            metadatas.append({
                "page_title": f"Page {i}",
                "space_key": "TEST",
                "space_name": "Test Space",
                "author": {"display_name": "Test User"},
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z"
            })
        
        start_time = time.time()
        memory_before = self.process.memory_info().rss / 1024 / 1024
        
        enriched_contents = []
        for content, metadata in zip(contents, metadatas):
            enriched_content = enricher.enrich_page_content(content, metadata)
            enriched_contents.append(enriched_content)
        
        end_time = time.time()
        memory_after = self.process.memory_info().rss / 1024 / 1024
        
        duration = end_time - start_time
        memory_usage = memory_after - memory_before
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0,
            files_processed=len(contents),
            files_per_second=len(contents) / duration if duration > 0 else 0,
            success_rate=100.0,
            errors=[],
            metadata={"content_items": len(contents)}
        )
    
    def benchmark_batch_vs_individual(self) -> BenchmarkResult:
        """Benchmark batch vs individual upload performance"""
        test_name = "batch_vs_individual"
        
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(100)]
        
        # Test batch upload
        start_time = time.time()
        batch_summary = self._run_mock_export("BATCH", pages, [], use_batch=True)
        batch_duration = time.time() - start_time
        
        # Test individual upload
        start_time = time.time()
        individual_summary = self._run_mock_export("INDIVIDUAL", pages, [], use_batch=False)
        individual_duration = time.time() - start_time
        
        # Calculate performance difference
        performance_improvement = (individual_duration - batch_duration) / individual_duration * 100
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=batch_duration,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            files_processed=len(pages),
            files_per_second=len(pages) / batch_duration if batch_duration > 0 else 0,
            success_rate=batch_summary.success_rate,
            errors=batch_summary.errors,
            metadata={
                "batch_duration": batch_duration,
                "individual_duration": individual_duration,
                "performance_improvement_percent": performance_improvement
            }
        )
    
    def benchmark_concurrent_exports(self) -> BenchmarkResult:
        """Benchmark concurrent export performance"""
        test_name = "concurrent_exports"
        
        # This would require more complex setup with threading
        # For now, return a placeholder result
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=0.1,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            files_processed=0,
            files_per_second=0,
            success_rate=100.0,
            errors=[],
            metadata={"note": "Concurrent export benchmark not implemented"}
        )
    
    def benchmark_memory_usage(self) -> BenchmarkResult:
        """Benchmark memory usage patterns"""
        test_name = "memory_usage"
        
        # Monitor memory usage during export
        memory_samples = []
        
        def memory_monitor():
            while True:
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                time.sleep(0.1)
        
        import threading
        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()
        
        # Run export
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(500)]
        
        start_time = time.time()
        summary = self._run_mock_export("MEMORY", pages, [])
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Calculate memory statistics
        if memory_samples:
            max_memory = max(memory_samples)
            min_memory = min(memory_samples)
            avg_memory = sum(memory_samples) / len(memory_samples)
            memory_growth = max_memory - min_memory
        else:
            max_memory = min_memory = avg_memory = memory_growth = 0
        
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_usage_mb=memory_growth,
            cpu_usage_percent=0,
            files_processed=len(pages),
            files_per_second=len(pages) / duration if duration > 0 else 0,
            success_rate=summary.success_rate,
            errors=summary.errors,
            metadata={
                "max_memory_mb": max_memory,
                "min_memory_mb": min_memory,
                "avg_memory_mb": avg_memory,
                "memory_growth_mb": memory_growth
            }
        )
    
    def benchmark_network_performance(self) -> BenchmarkResult:
        """Benchmark network performance patterns"""
        test_name = "network_performance"
        
        # This would require actual network calls
        # For now, return a placeholder result
        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=0.1,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            files_processed=0,
            files_per_second=0,
            success_rate=100.0,
            errors=[],
            metadata={"note": "Network performance benchmark not implemented"}
        )
    
    def _run_mock_export(self, space_key: str, pages: List[Dict], attachments: List[Dict], use_batch: bool = True):
        """Run mock export for benchmarking"""
        from unittest.mock import Mock
        
        # Create mock clients
        mock_open_webui_client = Mock()
        mock_confluence_client = Mock()
        
        # Setup mock responses
        mock_open_webui_client.create_or_get_knowledge_base.return_value = Mock(
            id="kb1", name="Test KB"
        )
        mock_open_webui_client.create_or_update_file.return_value = Mock(
            id="file1", filename="test.md"
        )
        mock_open_webui_client.batch_add_files_to_knowledge.return_value = True
        mock_open_webui_client.add_file_to_knowledge.return_value = True
        
        mock_confluence_client.get_space_details.return_value = {"name": "Test Space"}
        mock_confluence_client.get_complete_page_metadata.return_value = {
            "page_title": "Test Page"
        }
        mock_confluence_client.build_space_url.return_value = "https://test.com"
        
        # Create exporter
        attachment_filter = AttachmentFilter("pdf,md,txt")
        metadata_enricher = MetadataEnricher()
        
        exporter = OpenWebUIExporter(
            open_webui_client=mock_open_webui_client,
            confluence_client=mock_confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=use_batch
        )
        
        # Mock file reading
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', create=True) as mock_open:
            
            mock_file = Mock()
            mock_file.read.return_value = "# Test Content\n\nPage content"
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Run export
            summary = exporter.export_space(space_key, "/tmp", pages, attachments)
            
            return summary
    
    def save_results(self):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        results_data = {
            "timestamp": timestamp,
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "platform": os.name
            },
            "results": [
                {
                    "test_name": result.test_name,
                    "duration_seconds": result.duration_seconds,
                    "memory_usage_mb": result.memory_usage_mb,
                    "cpu_usage_percent": result.cpu_usage_percent,
                    "files_processed": result.files_processed,
                    "files_per_second": result.files_per_second,
                    "success_rate": result.success_rate,
                    "errors": result.errors,
                    "metadata": result.metadata
                }
                for result in self.results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        self.logger.info(f"Benchmark results saved to {filepath}")
    
    def generate_report(self) -> str:
        """Generate benchmark report"""
        report = ["# Open-WebUI Export Benchmark Report\n"]
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary table
        report.append("## Summary\n")
        report.append("| Test | Duration (s) | Files/s | Memory (MB) | Success Rate |\n")
        report.append("|------|--------------|---------|-------------|-------------|\n")
        
        for result in self.results:
            report.append(
                f"| {result.test_name} | {result.duration_seconds:.2f} | "
                f"{result.files_per_second:.2f} | {result.memory_usage_mb:.2f} | "
                f"{result.success_rate:.1f}% |\n"
            )
        
        # Detailed results
        report.append("\n## Detailed Results\n")
        for result in self.results:
            report.append(f"### {result.test_name}\n")
            report.append(f"- Duration: {result.duration_seconds:.2f} seconds\n")
            report.append(f"- Files processed: {result.files_processed}\n")
            report.append(f"- Throughput: {result.files_per_second:.2f} files/second\n")
            report.append(f"- Memory usage: {result.memory_usage_mb:.2f} MB\n")
            report.append(f"- Success rate: {result.success_rate:.1f}%\n")
            
            if result.metadata:
                report.append(f"- Metadata: {result.metadata}\n")
            
            if result.errors:
                report.append(f"- Errors: {len(result.errors)}\n")
            
            report.append("\n")
        
        return "".join(report)

def main():
    """Run benchmarks"""
    benchmark = ExportBenchmark()
    results = benchmark.run_all_benchmarks()
    
    # Generate and save report
    report = benchmark.generate_report()
    with open("benchmark_report.md", "w") as f:
        f.write(report)
    
    print("Benchmark completed. See benchmark_report.md for results.")

if __name__ == "__main__":
    main()
```

## Deliverables

1. **Comprehensive Testing Suite**
   - Unit tests for all Open-WebUI components
   - Integration tests with mocked services
   - End-to-end workflow tests
   - Performance benchmarks and stress tests

2. **Testing Infrastructure**
   - Test fixtures and mocks for consistent testing
   - Pytest configuration for different test types
   - Tox configuration for multi-environment testing
   - Coverage reporting and analysis

3. **Performance Benchmarking**
   - Baseline performance metrics
   - Memory usage profiling
   - Network performance analysis
   - Scalability testing

4. **Quality Assurance Tools**
   - Automated test running
   - Performance regression detection
   - Code quality metrics
   - Documentation validation

## Success Criteria

- [ ] Unit test coverage exceeds 90% for all Open-WebUI components
- [ ] Integration tests validate complete workflow scenarios
- [ ] Performance benchmarks establish baseline metrics
- [ ] End-to-end tests verify real-world usage patterns
- [ ] Memory usage remains stable under load
- [ ] Network performance meets acceptable thresholds
- [ ] Test suite runs reliably in CI/CD environment
- [ ] Performance regression detection is automated
- [ ] Code quality metrics meet established standards
- [ ] All tests pass consistently across supported Python versions
- [ ] Documentation includes testing and performance guidelines
- [ ] Production readiness is validated through comprehensive testing

This comprehensive testing and quality assurance phase ensures that the Open-WebUI integration is robust, performant, and ready for production deployment.
