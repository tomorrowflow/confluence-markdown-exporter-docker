# Multi-Mode Open WebUI Export Implementation Plan

## Overview

This document outlines the comprehensive implementation plan for extending the current `export-to-open-webui` command to support three distinct export modes using explicit subcommands:

- `export-to-open-webui space SPACE_KEY` (existing functionality)
- `export-to-open-webui page PAGE_ID` (new)
- `export-to-open-webui search CQL` (new)

## Current State Analysis

### Existing Implementation
The current implementation in `confluence_markdown_exporter/main.py` (lines 314-548) provides:
- Single `export-to-open-webui` command accepting only `space_key` as positional argument
- Complete set of optional parameters for filtering and configuration
- Integration with `OpenWebUIExporter.export_space()` method
- Existing `execute_search()` function with CQL support (lines 50-81)

### Key Infrastructure Available
- **Confluence API SDK**: `Page.from_id()`, `Space.from_key()`, `SearchResults.from_cql()`
- **OpenWebUIExporter**: Handles knowledge base creation and file uploads
- **Progress Reporting**: tqdm-based progress tracking with callbacks
- **Error Handling**: Comprehensive retry logic and error reporting
- **Content Processing**: MetadataEnricher, AttachmentFilter, file organization

## Architecture Design

### High-Level Architecture

```mermaid
graph TD
    A[CLI Entry Point] --> B{Subcommand Router}
    B -->|space| C[Space Export Handler]
    B -->|page| D[Page Export Handler]
    B -->|search| E[Search Export Handler]
    
    C --> F[Content Collector]
    D --> F
    E --> F
    
    F --> G[OpenWebUIExporter]
    G --> H[Knowledge Base Manager]
    G --> I[Progress Reporter]
    
    H --> J[Space-based KB Creation]
    I --> K[Unified Progress Tracking]
    
    subgraph "Content Sources"
        L[Space.from_key()]
        M[Page.from_id()]
        N[SearchResults.from_cql()]
    end
    
    C --> L
    D --> M
    E --> N
    
    subgraph "Export Pipeline"
        O[Page Collection]
        P[Attachment Processing]
        Q[Metadata Enrichment]
        R[OpenWebUI Upload]
    end
    
    F --> O
    O --> P
    P --> Q
    Q --> R
```

### Content Collection Strategy

```mermaid
graph LR
    A[ContentCollector Interface] --> B[SpaceContentCollector]
    A --> C[PageContentCollector]
    A --> D[SearchContentCollector]
    
    B --> E[Space.from_key()]
    C --> F[Page.from_id()]
    D --> G[SearchResults.from_cql()]
    
    E --> H[Pages List]
    F --> H
    G --> H
    
    H --> I[Space Grouping]
    I --> J[Knowledge Base Creation]
```

## Implementation Plan

### Phase 1: CLI Interface Restructuring

#### 1.1 Modify Main CLI Command Structure
**File**: `confluence_markdown_exporter/main.py`

**Current Structure**:
```python
@app.command("export-to-open-webui")
def export_to_open_webui(space_key: str, ...)
```

**New Structure**:
```python
@app.command("export-to-open-webui")
def export_to_open_webui():
    """Export Confluence content to Open WebUI knowledge bases."""
    pass

@export_to_open_webui.command("space")
def export_space_to_open_webui(space_key: str, ...)

@export_to_open_webui.command("page") 
def export_page_to_open_webui(page_id: str, ...)

@export_to_open_webui.command("search")
def export_search_to_open_webui(cql_query: str, ...)
```

#### 1.2 Parameter Consistency
All three subcommands will share the same optional parameters:
- `--output-path`: Optional output directory path
- `--show-progress`: Enable progress bars
- `--retry-errors`: Retry failed operations
- `--filter-image-types`: Filter image attachments by type
- `--filter-image-size-mb`: Filter images by size
- `--filter-attachment-types`: Filter non-image attachments by type
- `--filter-attachment-size-mb`: Filter attachments by size
- `--enrich-with-metadata`: Add Confluence metadata to exports
- `--redact-emails`: Remove email addresses from content
- `--redact-user-mentions`: Remove user mentions from content

### Phase 2: Content Collection Abstraction

#### 2.1 Create Content Collection Interface
**New File**: `confluence_markdown_exporter/utils/content_collector.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from confluence_markdown_exporter.confluence import Page

class ContentCollector(ABC):
    """Abstract base class for collecting content from different sources."""
    
    @abstractmethod
    def collect_pages(self) -> List[Page]:
        """Collect pages based on the export mode."""
        pass
    
    @abstractmethod
    def get_spaces_involved(self) -> List[str]:
        """Get list of space keys involved in this export."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of what's being exported."""
        pass

class SpaceContentCollector(ContentCollector):
    """Collects all pages from a specific Confluence space."""
    
    def __init__(self, space_key: str):
        self.space_key = space_key
    
    def collect_pages(self) -> List[Page]:
        # Use existing Space.from_key() logic
        from confluence_markdown_exporter.confluence import Space
        space = Space.from_key(self.space_key)
        return space.pages
    
    def get_spaces_involved(self) -> List[str]:
        return [self.space_key]
    
    def get_description(self) -> str:
        return f"Space: {self.space_key}"

class PageContentCollector(ContentCollector):
    """Collects a single page by ID."""
    
    def __init__(self, page_id: str):
        self.page_id = page_id
        self._page = None
    
    def collect_pages(self) -> List[Page]:
        # Use Page.from_id() to get single page
        from confluence_markdown_exporter.confluence import Page
        if self._page is None:
            self._page = Page.from_id(self.page_id)
        return [self._page]
    
    def get_spaces_involved(self) -> List[str]:
        # Extract space from page metadata
        if self._page is None:
            self.collect_pages()  # Load page to get space info
        return [self._page.space_key]
    
    def get_description(self) -> str:
        return f"Page ID: {self.page_id}"

class SearchContentCollector(ContentCollector):
    """Collects pages based on CQL search query."""
    
    def __init__(self, cql_query: str, limit: int = 100):
        self.cql_query = cql_query
        self.limit = limit
        self._pages = None
    
    def collect_pages(self) -> List[Page]:
        # Use existing execute_search() and SearchResults.from_cql()
        if self._pages is None:
            from confluence_markdown_exporter.main import execute_search
            from confluence_markdown_exporter.confluence import Page
            page_ids = execute_search(self.cql_query, limit=self.limit)
            self._pages = [Page.from_id(page_id) for page_id in page_ids]
        return self._pages
    
    def get_spaces_involved(self) -> List[str]:
        # Extract unique spaces from collected pages
        if self._pages is None:
            self.collect_pages()
        return list(set(page.space_key for page in self._pages))
    
    def get_description(self) -> str:
        return f"CQL Query: {self.cql_query}"
```

### Phase 3: OpenWebUIExporter Generalization

#### 3.1 Refactor OpenWebUIExporter Class
**File**: `confluence_markdown_exporter/utils/open_webui_exporter.py`

**Current Method**:
```python
def export_space(self, space_key: str, ...) -> None:
```

**New Methods**:
```python
def export_content(self, collector: ContentCollector, 
                  output_path: Optional[Path] = None,
                  show_progress: bool = True,
                  retry_errors: bool = False,
                  filter_image_types: Optional[List[str]] = None,
                  filter_image_size_mb: Optional[float] = None,
                  filter_attachment_types: Optional[List[str]] = None,
                  filter_attachment_size_mb: Optional[float] = None,
                  enrich_with_metadata: bool = False,
                  redact_emails: bool = False,
                  redact_user_mentions: bool = False) -> None:
    """Unified export method that works with any content collector."""
    
    # Collect pages using the provided collector
    pages = collector.collect_pages()
    spaces_involved = collector.get_spaces_involved()
    
    # Group pages by space for knowledge base organization
    pages_by_space = self._group_pages_by_space(pages)
    
    # Process each space separately
    for space_key, space_pages in pages_by_space.items():
        self._export_space_pages(space_key, space_pages, ...)

def export_space(self, space_key: str, ...) -> None:
    """Backward compatibility wrapper."""
    collector = SpaceContentCollector(space_key)
    return self.export_content(collector, ...)

def _group_pages_by_space(self, pages: List[Page]) -> Dict[str, List[Page]]:
    """Group pages by their space keys."""
    pages_by_space = {}
    for page in pages:
        space_key = page.space_key
        if space_key not in pages_by_space:
            pages_by_space[space_key] = []
        pages_by_space[space_key].append(page)
    return pages_by_space

def _export_space_pages(self, space_key: str, pages: List[Page], ...) -> None:
    """Export a specific set of pages to a space-based knowledge base."""
    # Existing export logic adapted for arbitrary page lists
    pass
```

#### 3.2 Knowledge Base Management Strategy
Since all pages belong to spaces, the knowledge base naming strategy remains unchanged:
- Collect all pages using the appropriate collector
- Group pages by their space keys
- Create/use knowledge bases named after space keys
- Handle multi-space scenarios (for search exports that span multiple spaces)

### Phase 4: Progress Reporting Enhancement

#### 4.1 Unified Progress Tracking
**Enhancement**: `confluence_markdown_exporter/utils/open_webui_exporter.py`

```python
class ExportProgress:
    """Unified progress tracking for all export modes."""
    
    def __init__(self, collector: ContentCollector):
        self.collector = collector
        self.total_pages = 0
        self.total_attachments = 0
        self.processed_pages = 0
        self.processed_attachments = 0
        self.current_space = None
    
    def initialize_counts(self, pages: List[Page]):
        """Initialize progress counters based on collected pages."""
        self.total_pages = len(pages)
        self.total_attachments = sum(len(page.attachments) for page in pages)
    
    def update_page_progress(self, increment: int = 1):
        self.processed_pages += increment
    
    def update_attachment_progress(self, increment: int = 1):
        self.processed_attachments += increment
    
    def set_current_space(self, space_key: str):
        self.current_space = space_key
    
    def get_status_message(self) -> str:
        """Get current progress status message."""
        base_msg = f"Exporting {self.collector.get_description()}"
        if self.current_space:
            base_msg += f" (Current space: {self.current_space})"
        return base_msg
```

### Phase 5: Error Handling and Validation

#### 5.1 Input Validation
**New File**: `confluence_markdown_exporter/utils/export_validators.py`

```python
def validate_page_id(page_id: str) -> None:
    """Validate that page ID exists and is accessible."""
    try:
        from confluence_markdown_exporter.confluence import Page
        Page.from_id(page_id)
    except Exception as e:
        raise ValueError(f"Invalid or inaccessible page ID '{page_id}': {e}")

def validate_space_key(space_key: str) -> None:
    """Validate that space key exists and is accessible."""
    try:
        from confluence_markdown_exporter.confluence import Space
        Space.from_key(space_key)
    except Exception as e:
        raise ValueError(f"Invalid or inaccessible space key '{space_key}': {e}")

def validate_cql_query(cql_query: str, limit: int = 100) -> None:
    """Validate CQL query syntax and test execution."""
    try:
        from confluence_markdown_exporter.main import execute_search
        results = execute_search(cql_query, limit=min(limit, 10))  # Test with small limit
        if not results:
            raise ValueError(f"CQL query returned no results: '{cql_query}'")
    except Exception as e:
        raise ValueError(f"Invalid CQL query '{cql_query}': {e}")
```

#### 5.2 Error Handling Patterns
- Reuse existing retry logic from `execute_search()`
- Handle API rate limiting consistently across all modes
- Provide meaningful error messages for each export mode
- Graceful handling of partial failures in multi-space scenarios

## Implementation Sequence

```mermaid
graph LR
    A[Phase 1: CLI Restructuring] --> B[Phase 2: Content Collectors]
    B --> C[Phase 3: Exporter Generalization]
    C --> D[Phase 4: Progress Enhancement]
    D --> E[Phase 5: Error Handling]
    E --> F[Testing & Validation]
```

### Step-by-Step Implementation Order

1. **Create Content Collector Abstraction**
   - Implement `ContentCollector` interface and concrete classes
   - Test each collector independently

2. **Implement Individual Collectors**
   - `SpaceContentCollector` (adapt existing logic)
   - `PageContentCollector` (new implementation)
   - `SearchContentCollector` (adapt existing search logic)

3. **Refactor OpenWebUIExporter**
   - Add `export_content()` method
   - Implement page grouping by space
   - Maintain backward compatibility with `export_space()`

4. **Update CLI Interface**
   - Convert to subcommand structure with Typer
   - Implement three subcommands with shared parameters
   - Add input validation for each mode

5. **Enhance Progress Reporting**
   - Implement unified progress tracking
   - Update progress messages for different export modes
   - Handle multi-space progress reporting

6. **Add Input Validation**
   - Implement validation functions for each input type
   - Integrate validation into CLI commands
   - Provide helpful error messages

7. **Update Error Handling**
   - Ensure consistent error patterns across modes
   - Handle mode-specific error scenarios
   - Test error recovery mechanisms

8. **Backward Compatibility Testing**
   - Verify existing space exports work unchanged
   - Test parameter compatibility
   - Validate knowledge base naming consistency

9. **Integration Testing**
   - Test all three modes end-to-end
   - Verify multi-space scenarios
   - Test edge cases and error conditions

## Usage Examples

### Space Export (Existing)
```bash
python -m confluence_markdown_exporter.main export-to-open-webui space MYSPACE --show-progress
```

### Page Export (New)
```bash
python -m confluence_markdown_exporter.main export-to-open-webui page 123456789 --show-progress --enrich-with-metadata
```

### Search Export (New)
```bash
python -m confluence_markdown_exporter.main export-to-open-webui search "space = MYSPACE AND type = page" --show-progress --filter-image-size-mb 5
```

## Key Benefits

1. **Modularity**: Each export mode is handled by a dedicated collector
2. **Consistency**: All modes share the same optional parameters and behavior
3. **Maintainability**: Clear separation of concerns between content collection and export logic
4. **Extensibility**: Easy to add new export modes in the future
5. **Backward Compatibility**: Existing space export functionality remains unchanged
6. **Space-based Organization**: Natural knowledge base organization by Confluence spaces

## Potential Challenges and Mitigations

### 1. Multi-space Search Results
**Challenge**: Search queries may return pages from multiple spaces
**Mitigation**: Create separate knowledge bases for each space involved, group pages appropriately

### 2. Large Search Result Sets
**Challenge**: CQL queries might return many pages
**Mitigation**: Use existing limit parameter and implement pagination if needed

### 3. Page Access Permissions
**Challenge**: Single page exports might fail due to permissions
**Mitigation**: Provide clear error messages and suggest using space export instead

### 4. CLI Breaking Changes
**Challenge**: Current users expect the old interface
**Mitigation**: Maintain backward compatibility wrapper and provide clear migration documentation

### 5. Knowledge Base Naming Conflicts
**Challenge**: Multiple export operations might target the same space
**Mitigation**: Use existing knowledge base update/merge logic from current implementation

## Testing Strategy

### Unit Tests
- Test each content collector independently
- Validate input validation functions
- Test progress tracking components

### Integration Tests
- End-to-end testing for each export mode
- Multi-space scenario testing
- Error handling and recovery testing

### Backward Compatibility Tests
- Verify existing space export functionality
- Test parameter compatibility
- Validate knowledge base organization

This implementation plan provides a comprehensive roadmap for extending the Open WebUI export functionality while maintaining the existing user experience and ensuring robust, maintainable code.
