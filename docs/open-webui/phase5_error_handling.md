# Phase 5: Error Handling and Logging

## Overview
Implement comprehensive error handling and enhanced logging specifically for Open-WebUI operations with detailed progress reporting and robust error recovery.

## Task 5.1: Enhanced Logging

### Objective
Create specialized logging utilities for Open-WebUI operations with detailed progress reporting, error tracking, and export summaries.

### Files to Create
- `confluence_markdown_exporter/utils/open_webui_logger.py`
- `confluence_markdown_exporter/utils/progress_reporter.py`
- `confluence_markdown_exporter/utils/__init__.py` (update)

### Requirements
- Detailed progress reporting with success/failure status
- Structured logging for Open-WebUI operations
- Export statistics and summaries
- Configurable log levels and formats
- Performance metrics tracking

### Reference Implementation

```python
# confluence_markdown_exporter/utils/open_webui_logger.py

import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class OpenWebUILogEntry:
    """Structured log entry for Open-WebUI operations"""
    timestamp: str
    operation: str
    status: str  # 'success', 'failed', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class OpenWebUILogger:
    """Specialized logger for Open-WebUI operations"""
    
    def __init__(self, name: str = "open_webui", log_file: Optional[str] = None):
        """Initialize the Open-WebUI logger
        
        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.log_entries: List[OpenWebUILogEntry] = []
        self.start_time = datetime.now()
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            self._setup_logger(log_file)
    
    def _setup_logger(self, log_file: Optional[str] = None):
        """Setup logger configuration"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        self.logger.setLevel(logging.INFO)
    
    def log_operation_start(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Log the start of an operation
        
        Args:
            operation: Operation name
            details: Optional operation details
        """
        entry = OpenWebUILogEntry(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            status='info',
            message=f"Starting {operation}",
            details=details
        )
        
        self.log_entries.append(entry)
        self.logger.info(f"Starting {operation}")
        
        if details:
            self.logger.debug(f"Operation details: {json.dumps(details, indent=2)}")
    
    def log_operation_success(self, operation: str, message: str, 
                            details: Optional[Dict[str, Any]] = None,
                            duration_ms: Optional[int] = None):
        """Log successful operation
        
        Args:
            operation: Operation name
            message: Success message
            details: Optional operation details
            duration_ms: Operation duration in milliseconds
        """
        entry = OpenWebUILogEntry(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            status='success',
            message=message,
            details=details,
            duration_ms=duration_ms
        )
        
        self.log_entries.append(entry)
        self.logger.info(f"✓ {message}")
        
        if duration_ms:
            self.logger.debug(f"Operation completed in {duration_ms}ms")
    
    def log_operation_failure(self, operation: str, message: str, 
                            error: Optional[Exception] = None,
                            details: Optional[Dict[str, Any]] = None,
                            duration_ms: Optional[int] = None):
        """Log failed operation
        
        Args:
            operation: Operation name
            message: Failure message
            error: Optional exception
            details: Optional operation details
            duration_ms: Operation duration in milliseconds
        """
        error_details = {}
        if error:
            error_details = {
                'error_type': type(error).__name__,
                'error_message': str(error)
            }
        
        if details:
            error_details.update(details)
        
        entry = OpenWebUILogEntry(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            status='failed',
            message=message,
            details=error_details,
            duration_ms=duration_ms
        )
        
        self.log_entries.append(entry)
        self.logger.error(f"✗ {message}")
        
        if error:
            self.logger.error(f"Error details: {error}")
    
    def log_operation_warning(self, operation: str, message: str, 
                            details: Optional[Dict[str, Any]] = None):
        """Log operation warning
        
        Args:
            operation: Operation name
            message: Warning message
            details: Optional operation details
        """
        entry = OpenWebUILogEntry(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            status='warning',
            message=message,
            details=details
        )
        
        self.log_entries.append(entry)
        self.logger.warning(f"⚠ {message}")
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of all operations
        
        Returns:
            Dictionary with operation statistics
        """
        total_operations = len(self.log_entries)
        success_count = len([e for e in self.log_entries if e.status == 'success'])
        failed_count = len([e for e in self.log_entries if e.status == 'failed'])
        warning_count = len([e for e in self.log_entries if e.status == 'warning'])
        
        # Calculate total duration
        total_duration_ms = sum(
            e.duration_ms for e in self.log_entries 
            if e.duration_ms is not None
        )
        
        return {
            'total_operations': total_operations,
            'successful_operations': success_count,
            'failed_operations': failed_count,
            'warning_operations': warning_count,
            'success_rate': (success_count / total_operations * 100) if total_operations > 0 else 0,
            'total_duration_ms': total_duration_ms,
            'average_duration_ms': total_duration_ms / total_operations if total_operations > 0 else 0
        }
    
    def export_log_entries(self, file_path: str):
        """Export log entries to JSON file
        
        Args:
            file_path: Path to export file
        """
        try:
            log_data = {
                'export_timestamp': datetime.now().isoformat(),
                'session_start_time': self.start_time.isoformat(),
                'summary': self.get_operation_summary(),
                'entries': [entry.to_dict() for entry in self.log_entries]
            }
            
            with open(file_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.info(f"Log entries exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export log entries: {e}")
    
    def get_failed_operations(self) -> List[OpenWebUILogEntry]:
        """Get all failed operations
        
        Returns:
            List of failed operation entries
        """
        return [e for e in self.log_entries if e.status == 'failed']
    
    def get_operations_by_type(self, operation_type: str) -> List[OpenWebUILogEntry]:
        """Get operations by type
        
        Args:
            operation_type: Type of operation to filter by
            
        Returns:
            List of matching operation entries
        """
        return [e for e in self.log_entries if e.operation == operation_type]
    
    def clear_log_entries(self):
        """Clear all log entries"""
        self.log_entries.clear()
        self.start_time = datetime.now()
        self.logger.info("Log entries cleared")


# confluence_markdown_exporter/utils/progress_reporter.py

import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ProgressStatus:
    """Progress status information"""
    current: int
    total: int
    operation: str
    item_name: str
    status: str  # 'processing', 'success', 'failed'
    message: str
    start_time: datetime
    current_time: datetime
    
    @property
    def percentage(self) -> float:
        """Calculate percentage complete"""
        return (self.current / self.total * 100) if self.total > 0 else 0
    
    @property
    def elapsed_seconds(self) -> float:
        """Calculate elapsed time in seconds"""
        return (self.current_time - self.start_time).total_seconds()
    
    @property
    def estimated_total_seconds(self) -> float:
        """Estimate total time based on current progress"""
        if self.current == 0:
            return 0
        return self.elapsed_seconds / self.current * self.total
    
    @property
    def estimated_remaining_seconds(self) -> float:
        """Estimate remaining time"""
        return max(0, self.estimated_total_seconds - self.elapsed_seconds)

class ProgressReporter:
    """Progress reporter for Open-WebUI operations"""
    
    def __init__(self, logger: Optional[Any] = None, 
                 progress_callback: Optional[Callable[[ProgressStatus], None]] = None):
        """Initialize progress reporter
        
        Args:
            logger: Optional logger instance
            progress_callback: Optional callback function for progress updates
        """
        self.logger = logger
        self.progress_callback = progress_callback
        self.start_time = datetime.now()
        
        # Statistics
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.current_operation = 0
    
    def start_operation_batch(self, operation_type: str, total_items: int):
        """Start a batch operation
        
        Args:
            operation_type: Type of operation
            total_items: Total number of items to process
        """
        self.operation_type = operation_type
        self.total_operations = total_items
        self.current_operation = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.start_time = datetime.now()
        
        if self.logger:
            self.logger.info(f"Starting batch operation: {operation_type} ({total_items} items)")
    
    def report_item_start(self, item_name: str, item_index: int):
        """Report start of item processing
        
        Args:
            item_name: Name of the item being processed
            item_index: Index of the item (1-based)
        """
        self.current_operation = item_index
        
        status = ProgressStatus(
            current=item_index,
            total=self.total_operations,
            operation=self.operation_type,
            item_name=item_name,
            status='processing',
            message=f"Processing {item_name}",
            start_time=self.start_time,
            current_time=datetime.now()
        )
        
        if self.logger:
            self.logger.info(f"Processing {item_index}/{self.total_operations}: {item_name}")
        
        if self.progress_callback:
            self.progress_callback(status)
    
    def report_item_success(self, item_name: str, message: str = "Success"):
        """Report successful item processing
        
        Args:
            item_name: Name of the item
            message: Success message
        """
        self.successful_operations += 1
        
        status = ProgressStatus(
            current=self.current_operation,
            total=self.total_operations,
            operation=self.operation_type,
            item_name=item_name,
            status='success',
            message=message,
            start_time=self.start_time,
            current_time=datetime.now()
        )
        
        if self.logger:
            self.logger.info(f"Uploading '{item_name}' to knowledge base... Success")
        
        if self.progress_callback:
            self.progress_callback(status)
    
    def report_item_failure(self, item_name: str, error_message: str):
        """Report failed item processing
        
        Args:
            item_name: Name of the item
            error_message: Error message
        """
        self.failed_operations += 1
        
        status = ProgressStatus(
            current=self.current_operation,
            total=self.total_operations,
            operation=self.operation_type,
            item_name=item_name,
            status='failed',
            message=f"Failed: {error_message}",
            start_time=self.start_time,
            current_time=datetime.now()
        )
        
        if self.logger:
            self.logger.error(f"Uploading '{item_name}' to knowledge base... Failed: {error_message}")
        
        if self.progress_callback:
            self.progress_callback(status)
    
    def report_batch_complete(self):
        """Report completion of batch operation"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        success_rate = (self.successful_operations / self.total_operations * 100) if self.total_operations > 0 else 0
        
        if self.logger:
            self.logger.info(f"Batch operation completed:")
            self.logger.info(f"  Total items: {self.total_operations}")
            self.logger.info(f"  Successful: {self.successful_operations}")
            self.logger.info(f"  Failed: {self.failed_operations}")
            self.logger.info(f"  Success rate: {success_rate:.1f}%")
            self.logger.info(f"  Duration: {duration:.2f} seconds")
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary
        
        Returns:
            Dictionary with progress statistics
        """
        current_time = datetime.now()
        elapsed = (current_time - self.start_time).total_seconds()
        
        return {
            'operation_type': getattr(self, 'operation_type', 'unknown'),
            'total_operations': self.total_operations,
            'current_operation': self.current_operation,
            'successful_operations': self.successful_operations,
            'failed_operations': self.failed_operations,
            'progress_percentage': (self.current_operation / self.total_operations * 100) if self.total_operations > 0 else 0,
            'elapsed_seconds': elapsed,
            'estimated_remaining_seconds': max(0, elapsed / self.current_operation * (self.total_operations - self.current_operation)) if self.current_operation > 0 else 0
        }
    
    def format_progress_message(self, status: ProgressStatus) -> str:
        """Format progress message for display
        
        Args:
            status: Progress status
            
        Returns:
            Formatted progress message
        """
        percentage = status.percentage
        elapsed = status.elapsed_seconds
        remaining = status.estimated_remaining_seconds
        
        time_info = f"Elapsed: {elapsed:.1f}s"
        if remaining > 0:
            time_info += f", Remaining: {remaining:.1f}s"
        
        return f"[{percentage:.1f}%] {status.operation} ({status.current}/{status.total}) - {status.message} - {time_info}"
```

### Testing Requirements

```python
# tests/test_open_webui_logger.py

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json
import tempfile
import os

from confluence_markdown_exporter.utils.open_webui_logger import OpenWebUILogger, OpenWebUILogEntry
from confluence_markdown_exporter.utils.progress_reporter import ProgressReporter, ProgressStatus

class TestOpenWebUILogger:
    @pytest.fixture
    def logger(self):
        return OpenWebUILogger("test_logger")
    
    def test_logger_initialization(self, logger):
        assert logger.logger.name == "test_logger"
        assert len(logger.log_entries) == 0
        assert logger.start_time is not None
    
    def test_log_operation_start(self, logger):
        details = {"key": "value"}
        logger.log_operation_start("test_operation", details)
        
        assert len(logger.log_entries) == 1
        entry = logger.log_entries[0]
        assert entry.operation == "test_operation"
        assert entry.status == "info"
        assert entry.details == details
    
    def test_log_operation_success(self, logger):
        logger.log_operation_success("test_operation", "Success message", duration_ms=100)
        
        assert len(logger.log_entries) == 1
        entry = logger.log_entries[0]
        assert entry.operation == "test_operation"
        assert entry.status == "success"
        assert entry.message == "Success message"
        assert entry.duration_ms == 100
    
    def test_log_operation_failure(self, logger):
        error = Exception("Test error")
        logger.log_operation_failure("test_operation", "Failed message", error)
        
        assert len(logger.log_entries) == 1
        entry = logger.log_entries[0]
        assert entry.operation == "test_operation"
        assert entry.status == "failed"
        assert entry.message == "Failed message"
        assert "error_type" in entry.details
        assert entry.details["error_type"] == "Exception"
    
    def test_log_operation_warning(self, logger):
        logger.log_operation_warning("test_operation", "Warning message")
        
        assert len(logger.log_entries) == 1
        entry = logger.log_entries[0]
        assert entry.operation == "test_operation"
        assert entry.status == "warning"
        assert entry.message == "Warning message"
    
    def test_get_operation_summary(self, logger):
        logger.log_operation_success("op1", "Success", duration_ms=100)
        logger.log_operation_failure("op2", "Failed", duration_ms=200)
        logger.log_operation_warning("op3", "Warning")
        
        summary = logger.get_operation_summary()
        
        assert summary["total_operations"] == 3
        assert summary["successful_operations"] == 1
        assert summary["failed_operations"] == 1
        assert summary["warning_operations"] == 1
        assert summary["success_rate"] == pytest.approx(33.33, rel=1e-2)
        assert summary["total_duration_ms"] == 300
    
    def test_export_log_entries(self, logger):
        logger.log_operation_success("test_op", "Success")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            logger.export_log_entries(temp_path)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "export_timestamp" in data
            assert "summary" in data
            assert "entries" in data
            assert len(data["entries"]) == 1
            assert data["entries"][0]["operation"] == "test_op"
            
        finally:
            os.unlink(temp_path)
    
    def test_get_failed_operations(self, logger):
        logger.log_operation_success("op1", "Success")
        logger.log_operation_failure("op2", "Failed")
        logger.log_operation_failure("op3", "Failed")
        
        failed_ops = logger.get_failed_operations()
        assert len(failed_ops) == 2
        assert all(op.status == "failed" for op in failed_ops)
    
    def test_get_operations_by_type(self, logger):
        logger.log_operation_success("upload", "Success")
        logger.log_operation_success("upload", "Success")
        logger.log_operation_success("download", "Success")
        
        upload_ops = logger.get_operations_by_type("upload")
        assert len(upload_ops) == 2
        assert all(op.operation == "upload" for op in upload_ops)

class TestProgressReporter:
    @pytest.fixture
    def reporter(self):
        return ProgressReporter()
    
    def test_reporter_initialization(self, reporter):
        assert reporter.total_operations == 0
        assert reporter.successful_operations == 0
        assert reporter.failed_operations == 0
        assert reporter.current_operation == 0
    
    def test_start_operation_batch(self, reporter):
        reporter.start_operation_batch("upload", 10)
        
        assert reporter.operation_type == "upload"
        assert reporter.total_operations == 10
        assert reporter.current_operation == 0
    
    def test_report_item_success(self, reporter):
        reporter.start_operation_batch("upload", 2)
        reporter.report_item_start("file1.md", 1)
        reporter.report_item_success("file1.md", "Success")
        
        assert reporter.successful_operations == 1
        assert reporter.failed_operations == 0
    
    def test_report_item_failure(self, reporter):
        reporter.start_operation_batch("upload", 2)
        reporter.report_item_start("file1.md", 1)
        reporter.report_item_failure("file1.md", "Error message")
        
        assert reporter.successful_operations == 0
        assert reporter.failed_operations == 1
    
    def test_get_progress_summary(self, reporter):
        reporter.start_operation_batch("upload", 5)
        reporter.current_operation = 2
        reporter.successful_operations = 1
        reporter.failed_operations = 1
        
        summary = reporter.get_progress_summary()
        
        assert summary["operation_type"] == "upload"
        assert summary["total_operations"] == 5
        assert summary["current_operation"] == 2
        assert summary["successful_operations"] == 1
        assert summary["failed_operations"] == 1
        assert summary["progress_percentage"] == 40.0
    
    def test_progress_status_calculations(self):
        start_time = datetime.now()
        current_time = datetime.now()
        
        status = ProgressStatus(
            current=2,
            total=10,
            operation="upload",
            item_name="test.md",
            status="processing",
            message="Processing",
            start_time=start_time,
            current_time=current_time
        )
        
        assert status.percentage == 20.0
        assert status.elapsed_seconds >= 0
        assert status.estimated_total_seconds >= 0
    
    def test_format_progress_message(self, reporter):
        start_time = datetime.now()
        current_time = datetime.now()
        
        status = ProgressStatus(
            current=2,
            total=10,
            operation="upload",
            item_name="test.md",
            status="processing",
            message="Processing test.md",
            start_time=start_time,
            current_time=current_time
        )
        
        message = reporter.format_progress_message(status)
        
        assert "[20.0%]" in message
        assert "upload" in message
        assert "(2/10)" in message
        assert "Processing test.md" in message
        assert "Elapsed:" in message
```

## Task 5.2: Connection and Export Validation

### Objective
Create comprehensive validation for Open-WebUI connections and export operations with proper error handling and recovery mechanisms.

### Files to Create
- `confluence_markdown_exporter/validators/open_webui_validator.py`
- `confluence_markdown_exporter/validators/export_validator.py`
- `confluence_markdown_exporter/validators/__init__.py` (create)

### Requirements
- Connection validation with detailed error reporting
- Export precondition validation
- Configuration validation
- Network and authentication error handling
- Retry mechanisms for transient failures

### Reference Implementation

```python
# confluence_markdown_exporter/validators/open_webui_validator.py

import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin
import time

from ..clients.open_webui_client import OpenWebUIClient, OpenWebUIClientError
from ..utils.open_webui_logger import OpenWebUILogger

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

class OpenWebUIValidator:
    """Validator for Open-WebUI connections and operations"""
    
    def __init__(self, client: OpenWebUIClient, logger: Optional[OpenWebUILogger] = None):
        """Initialize validator
        
        Args:
            client: Open-WebUI client
            logger: Optional logger for validation operations
        """
        self.client = client
        self.validation_logger = logger
        self.retry_attempts = 3
        self.retry_delay = 1.0
    
    def validate_connection(self) -> ValidationResult:
        """Validate connection to Open-WebUI
        
        Returns:
            ValidationResult with connection status
        """
        try:
            if self.validation_logger:
                self.validation_logger.log_operation_start("validate_connection")
            
            # Test basic connectivity
            connectivity_result = self._test_connectivity()
            if not connectivity_result.is_valid:
                return connectivity_result
            
            # Test authentication
            auth_result = self._test_authentication()
            if not auth_result.is_valid:
                return auth_result
            
            # Test API permissions
            permissions_result = self._test_permissions()
            if not permissions_result.is_valid:
                return permissions_result
            
            if self.validation_logger:
                self.validation_logger.log_operation_success(
                    "validate_connection",
                    "Connection validation successful"
                )
            
            return ValidationResult(
                is_valid=True,
                message="Connection to Open-WebUI validated successfully"
            )
            
        except Exception as e:
            if self.validation_logger:
                self.validation_logger.log_operation_failure(
                    "validate_connection",
                    f"Connection validation failed: {str(e)}",
                    e
                )
            
            return ValidationResult(
                is_valid=False,
                message=f"Connection validation failed: {str(e)}",
                error_code="CONNECTION_VALIDATION_ERROR"
            )
    
    def _test_connectivity(self) -> ValidationResult:
        """Test basic network connectivity"""
        try:
            # Parse URL
            parsed_url = urlparse(self.client.base_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ValidationResult(
                    is_valid=False,
                    message="Invalid URL format",
                    error_code="INVALID_URL"
                )
            
            # Test with HEAD request first (lightweight)
            try:
                response = requests.head(self.client.base_url, timeout=10)
                if response.status_code in [200, 404, 405]:  # 405 is OK for HEAD
                    return ValidationResult(
                        is_valid=True,
                        message="Network connectivity confirmed"
                    )
            except requests.RequestException:
                pass
            
            # If HEAD fails, try GET
            try:
                response = requests.get(self.client.base_url, timeout=10)
                if response.status_code < 500:  # Any non-server error is connectivity
                    return ValidationResult(
                        is_valid=True,
                        message="Network connectivity confirmed"
                    )
            except requests.RequestException as e:
                return ValidationResult(
                    is_valid=False,
                    message=f"Network connectivity failed: {str(e)}",
                    error_code="NETWORK_ERROR"
                )
            
            return ValidationResult(
                is_valid=False,
                message="Server returned error status",
                error_code="SERVER_ERROR"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Connectivity test failed: {str(e)}",
                error_code="CONNECTIVITY_ERROR"
            )
    
    def _test_authentication(self) -> ValidationResult:
        """Test API authentication"""
        try:
            # Try to list knowledge bases (requires authentication)
            knowledge_bases = self.client.list_knowledge_bases()
            
            return ValidationResult(
                is_valid=True,
                message="Authentication successful",
                details={"knowledge_bases_count": len(knowledge_bases)}
            )
            
        except OpenWebUIClientError as e:
            if e.status_code == 401:
                return ValidationResult(
                    is_valid=False,
                    message="Authentication failed: Invalid API key",
                    error_code="INVALID_API_KEY"
                )
            elif e.status_code == 403:
                return ValidationResult(
                    is_valid=False,
                    message="Authentication failed: Insufficient permissions",
                    error_code="INSUFFICIENT_PERMISSIONS"
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    message=f"Authentication test failed: {str(e)}",
                    error_code="AUTH_ERROR"
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Authentication test failed: {str(e)}",
                error_code="AUTH_TEST_ERROR"
            )
    
    def _test_permissions(self) -> ValidationResult:
        """Test required API permissions"""
        try:
            permissions = {
                "list_knowledge": False,
                "create_knowledge": False,
                "list_files": False,
                "upload_files": False
            }
            
            # Test list knowledge bases
            try:
                self.client.list_knowledge_bases()
                permissions["list_knowledge"] = True
            except OpenWebUIClientError:
                pass
            
            # Test list files
            try:
                self.client.search_files("*")
                permissions["list_files"] = True
            except OpenWebUIClientError:
                pass
            
            # Test create knowledge base (we won't actually create one)
            # This is harder to test without side effects
            permissions["create_knowledge"] = True  # Assume if auth works, this works
            permissions["upload_files"] = True     # Assume if auth works, this works
            
            # Check if we have minimum required permissions
            required_permissions = ["list_knowledge", "list_files"]
            missing_permissions = [p for p in required_permissions if not permissions[p]]
            
            if missing_permissions:
                return ValidationResult(
                    is_valid=False,
                    message=f"Missing required permissions: {', '.join(missing_permissions)}",
                    details={"permissions": permissions},
                    error_code="MISSING_PERMISSIONS"
                )
            
            return ValidationResult(
                is_valid=True,
                message="Required permissions confirmed",
                details={"permissions": permissions}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Permission test failed: {str(e)}",
                error_code="PERMISSION_TEST_ERROR"
            )
    
    def validate_knowledge_base_access(self, knowledge_base_name: str) -> ValidationResult:
        """Validate access to a specific knowledge base
        
        Args:
            knowledge_base_name: Name of the knowledge base
            
        Returns:
            ValidationResult for knowledge base access
        """
        try:
            # Try to find the knowledge base
            knowledge_base = self.client.find_knowledge_base_by_name(knowledge_base_name)
            
            if knowledge_base:
                return ValidationResult(
                    is_valid=True,
                    message=f"Knowledge base '{knowledge_base_name}' found and accessible",
                    details={"knowledge_base_id": knowledge_base.id}
                )
            else:
                return ValidationResult(
                    is_valid=True,
                    message=f"Knowledge base '{knowledge_base_name}' not found (will be created)",
                    details={"needs_creation": True}
                )
                
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Knowledge base access validation failed: {str(e)}",
                error_code="KNOWLEDGE_BASE_ACCESS_ERROR"
            )
    
    def validate_file_upload_capability(self, test_content: str = "test") -> ValidationResult:
        """Test file upload capability
        
        Args:
            test_content: Test content to upload
            
        Returns:
            ValidationResult for file upload capability
        """
        try:
            # Upload a test file
            test_filename = f"test_upload_{int(time.time())}.txt"
            
            try:
                file_obj = self.client.upload_file(test_filename, test_content, "text/plain")
                
                # Clean up - try to delete the test file
                try:
                    # Note: Delete functionality depends on Open-WebUI API
                    # For now, we'll leave the test file
                    pass
                except:
                    pass
                
                return ValidationResult(
                    is_valid=True,
                    message="File upload capability confirmed",
                    details={"test_file_id": file_obj.id}
                )
                
            except OpenWebUIClientError as e:
                if e.status_code == 413:
                    return ValidationResult(
                        is_valid=False,
                        message="File upload failed: File too large",
                        error_code="FILE_TOO_LARGE"
                    )
                elif e.status_code == 415:
                    return ValidationResult(
                        is_valid=False,
                        message="File upload failed: Unsupported media type",
                        error_code="UNSUPPORTED_MEDIA_TYPE"
                    )
                else:
                    return ValidationResult(
                        is_valid=False,
                        message=f"File upload failed: {str(e)}",
                        error_code="UPLOAD_ERROR"
                    )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"File upload test failed: {str(e)}",
                error_code="UPLOAD_TEST_ERROR"
            )
    
    def validate_with_retry(self, validation_func, max_retries: int = None) -> ValidationResult:
        """Validate with retry logic for transient failures
        
        Args:
            validation_func: Validation function to execute
            max_retries: Maximum number of retries
            
        Returns:
            ValidationResult from validation function
        """
        if max_retries is None:
            max_retries = self.retry_attempts
        
        for attempt in range(max_retries + 1):
            try:
                result = validation_func()
                
                if result.is_valid or attempt == max_retries:
                    return result
                
                # If validation failed and we have retries left, wait and retry
                if attempt < max_retries:
                    logger.warning(f"Validation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                
            except Exception as e:
                if attempt == max_retries:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Validation failed after {max_retries + 1} attempts: {str(e)}",
                        error_code="VALIDATION_RETRY_EXHAUSTED"
                    )
                
                logger.warning(f"Validation error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                time.sleep(self.retry_delay)
                self.retry_delay *= 2
        
        return ValidationResult(
            is_valid=False,
            message="Validation failed after all retry attempts",
            error_code="VALIDATION_FAILED"
        )
    
    def run_comprehensive_validation(self) -> Dict[str, ValidationResult]:
        """Run comprehensive validation of all Open-WebUI capabilities
        
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        # Connection validation
        results["connection"] = self.validate_connection()
        
        # If connection fails, skip other tests
        if not results["connection"].is_valid:
            return results
        
        # File upload capability
        results["file_upload"] = self.validate_file_upload_capability()
        
        return results


# confluence_markdown_exporter/validators/export_validator.py

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os

from ..processors.attachment_filter import AttachmentFilter
from .open_webui_validator import OpenWebUIValidator, ValidationResult

logger = logging.getLogger(__name__)

class ExportValidator:
    """Validator for export operations"""
    
    def __init__(self, open_webui_validator: OpenWebUIValidator, 
                 attachment_filter: AttachmentFilter):
        """Initialize export validator
        
        Args:
            open_webui_validator: Open-WebUI validator
            attachment_filter: Attachment filter
        """
        self.open_webui_validator = open_webui_validator
        self.attachment_filter = attachment_filter
    
    def validate_export_preconditions(self, space_key: str, output_path: str,
                                    pages: List[Dict[str, Any]],
                                    attachments: List[Dict[str, Any]]) -> ValidationResult:
        """Validate preconditions for export
        
        Args:
            space_key: Confluence space key
            output_path: Output path
            pages: List of pages to export
            attachments: List of attachments to export
            
        Returns:
            ValidationResult for export preconditions
        """
        try:
            # Validate output path
            path_result = self._validate_output_path(output_path)
            if not path_result.is_valid:
                return path_result
            
            # Validate pages
            pages_result = self._validate_pages(pages)
            if not pages_result.is_valid:
                return pages_result
            
            # Validate attachments
            attachments_result = self._validate_attachments(attachments)
            if not attachments_result.is_valid:
                return attachments_result
            
            # Validate Open-WebUI connection
            connection_result = self.open_webui_validator.validate_connection()
            if not connection_result.is_valid:
                return connection_result
            
            return ValidationResult(
                is_valid=True,
                message="Export preconditions validated successfully",
                details={
                    "space_key": space_key,
                    "total_pages": len(pages),
                    "total_attachments": len(attachments),
                    "output_path": output_path
                }
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Export precondition validation failed: {str(e)}",
                error_code="EXPORT_PRECONDITION_ERROR"
            )
    
    def _validate_output_path(self, output_path: str) -> ValidationResult:
        """Validate output path exists and is writable"""
        try:
            path = Path(output_path)
            
            # Check if path exists
            if not path.exists():
                return ValidationResult(
                    is_valid=False,
                    message=f"Output path does not exist: {output_path}",
                    error_code="OUTPUT_PATH_NOT_FOUND"
                )
            
            # Check if path is a directory
            if not path.is_dir():
                return ValidationResult(
                    is_valid=False,
                    message=f"Output path is not a directory: {output_path}",
                    error_code="OUTPUT_PATH_NOT_DIRECTORY"
                )
            
            # Check if path is writable
            if not os.access(path, os.W_OK):
                return ValidationResult(
                    is_valid=False,
                    message=f"Output path is not writable: {output_path}",
                    error_code="OUTPUT_PATH_NOT_WRITABLE"
                )
            
            return ValidationResult(
                is_valid=True,
                message="Output path validated successfully"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Output path validation failed: {str(e)}",
                error_code="OUTPUT_PATH_VALIDATION_ERROR"
            )
    
    def _validate_pages(self, pages: List[Dict[str, Any]]) -> ValidationResult:
        """Validate pages for export"""
        try:
            if not pages:
                return ValidationResult(
                    is_valid=True,
                    message="No pages to validate (empty list is valid)"
                )
            
            # Check for required fields
            missing_fields = []
            for i, page in enumerate(pages):
                if not page.get('id'):
                    missing_fields.append(f"Page {i}: missing 'id' field")
                if not page.get('title'):
                    missing_fields.append(f"Page {i}: missing 'title' field")
            
            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    message=f"Pages validation failed: {', '.join(missing_fields)}",
                    error_code="PAGES_MISSING_FIELDS"
                )
            
            return ValidationResult(
                is_valid=True,
                message=f"Pages validated successfully ({len(pages)} pages)"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Pages validation failed: {str(e)}",
                error_code="PAGES_VALIDATION_ERROR"
            )
    
    def _validate_attachments(self, attachments: List[Dict[str, Any]]) -> ValidationResult:
        """Validate attachments for export"""
        try:
            if not attachments:
                return ValidationResult(
                    is_valid=True,
                    message="No attachments to validate (empty list is valid)"
                )
            
            # Filter attachments
            filter_result = self.attachment_filter.filter_attachments(attachments)
            allowed_attachments = filter_result['allowed']
            filtered_attachments = filter_result['filtered']
            
            # Check for required fields in allowed attachments
            missing_fields = []
            for i, attachment in enumerate(allowed_attachments):
                if not attachment.get('id'):
                    missing_fields.append(f"Attachment {i}: missing 'id' field")
                if not attachment.get('title') and not attachment.get('filename'):
                    missing_fields.append(f"Attachment {i}: missing 'title' or 'filename' field")
            
            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    message=f"Attachments validation failed: {', '.join(missing_fields)}",
                    error_code="ATTACHMENTS_MISSING_FIELDS"
                )
            
            return ValidationResult(
                is_valid=True,
                message=f"Attachments validated successfully ({len(allowed_attachments)} allowed, {len(filtered_attachments)} filtered)",
                details={
                    "allowed_attachments": len(allowed_attachments),
                    "filtered_attachments": len(filtered_attachments)
                }
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Attachments validation failed: {str(e)}",
                error_code="ATTACHMENTS_VALIDATION_ERROR"
            )
    
    def validate_file_access(self, file_path: str) -> ValidationResult:
        """Validate access to a specific file
        
        Args:
            file_path: Path to file
            
        Returns:
            ValidationResult for file access
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return ValidationResult(
                    is_valid=False,
                    message=f"File does not exist: {file_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            if not path.is_file():
                return ValidationResult(
                    is_valid=False,
                    message=f"Path is not a file: {file_path}",
                    error_code="NOT_A_FILE"
                )
            
            if not os.access(path, os.R_OK):
                return ValidationResult(
                    is_valid=False,
                    message=f"File is not readable: {file_path}",
                    error_code="FILE_NOT_READABLE"
                )
            
            return ValidationResult(
                is_valid=True,
                message="File access validated successfully",
                details={"file_size": path.stat().st_size}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"File access validation failed: {str(e)}",
                error_code="FILE_ACCESS_VALIDATION_ERROR"
            )
    
    def run_export_validation(self, space_key: str, output_path: str,
                            pages: List[Dict[str, Any]],
                            attachments: List[Dict[str, Any]]) -> Dict[str, ValidationResult]:
        """Run comprehensive export validation
        
        Args:
            space_key: Confluence space key
            output_path: Output path
            pages: List of pages to export
            attachments: List of attachments to export
            
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        # Validate preconditions
        results["preconditions"] = self.validate_export_preconditions(
            space_key, output_path, pages, attachments
        )
        
        # Validate Open-WebUI comprehensive
        results.update(self.open_webui_validator.run_comprehensive_validation())
        
        return results
```

## Deliverables

1. **Enhanced Logging System** (`open_webui_logger.py`, `progress_reporter.py`)
   - Structured logging for Open-WebUI operations
   - Progress reporting with detailed status updates
   - Export statistics and summaries
   - Log export and analysis capabilities

2. **Comprehensive Validation System** (`open_webui_validator.py`, `export_validator.py`)
   - Connection validation with retry logic
   - Authentication and permission testing
   - Export precondition validation
   - File access validation

3. **Test Suite**
   - Unit tests for logging utilities
   - Integration tests for validation components
   - Mock-based testing for network operations
   - Error handling and edge case validation

## Success Criteria

- [ ] Structured logging captures all Open-WebUI operations
- [ ] Progress reporting shows detailed status with success/failure
- [ ] Export summaries provide comprehensive statistics
- [ ] Connection validation detects and reports specific issues
- [ ] Authentication validation identifies permission problems
- [ ] Export precondition validation prevents invalid operations
- [ ] Retry logic handles transient failures gracefully
- [ ] Error messages are informative and actionable
- [ ] All tests pass with >90% coverage
- [ ] Log entries can be exported for analysis
- [ ] Validation results include specific error codes
- [ ] Performance metrics are tracked and reported
