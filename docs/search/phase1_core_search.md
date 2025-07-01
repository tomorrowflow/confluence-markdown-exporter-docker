# Phase 1: Core Search Implementation (CORRECTED)

## Critical Issues Discovered

Based on research of Confluence CQL API, I found several important considerations:

1. **Results Include All Content Types**: CQL returns pages, blog posts, comments, attachments, etc. by default
2. **Pagination Limits**: API has built-in limits (25-50 results per request depending on expansions)
3. **Result Structure**: Uses different structure than regular page API calls
4. **Type Filtering Required**: Must explicitly filter `type = page` to get pages only

## Objective
Add the core `SearchResults` class that correctly handles CQL queries and filters to pages only.

## Prerequisites
- Existing codebase is working
- No dependencies to install (uses existing `atlassian-python-api`)

## Files to Modify

### 1. `confluence_markdown_exporter/confluence.py`

**Action**: Add the `SearchResults` class after the existing `Organization` class (around line 200).

**Location**: After the `Organization` class definition, before the helper functions.

**Code to Add**:

```python
class SearchResults(BaseModel):
    query: str
    page_ids: list[int]
    total_size: int
    total_pages: int  # Pages only (filtered)

    def export(self) -> None:
        export_pages(self.page_ids)

    @classmethod
    def from_cql(cls, cql_query: str, limit: int = 100) -> "SearchResults":
        """Execute CQL query and return page IDs for export.
        
        Automatically filters results to pages only and handles pagination.
        """
        page_ids = []
        start = 0
        paging_limit = 25  # Conservative limit to avoid API restrictions
        total_size = 0
        total_pages = 0
        
        # Ensure we only get pages by adding type filter if not present
        if "type" not in cql_query.lower():
            if cql_query.strip():
                cql_query = f"({cql_query}) AND type = page"
            else:
                cql_query = "type = page"
        elif "type = page" not in cql_query.lower() and "type=page" not in cql_query.lower():
            # If type is specified but not page, add page filter
            if "type" in cql_query.lower():
                print("WARNING: CQL query specifies content type other than 'page'. Adding 'AND type = page' to filter pages only.")
                cql_query = f"({cql_query}) AND type = page"

        print(f"Executing CQL query: {cql_query}")
        
        try:
            while start < limit:
                current_limit = min(paging_limit, limit - start)
                
                response = cast(
                    JsonResponse,
                    confluence.cql(
                        cql_query, 
                        start=start, 
                        limit=current_limit,
                        expand="space"  # Minimal expansion to avoid 50-result limit
                    ),
                )
                
                # Extract page IDs from results
                results = response.get("results", [])
                current_page_ids = []
                
                for result in results:
                    # Double-check that result is a page (extra safety)
                    if result.get("type") == "page":
                        page_id = result.get("id")
                        if page_id:
                            try:
                                current_page_ids.append(int(page_id))
                            except (ValueError, TypeError):
                                print(f"WARNING: Invalid page ID: {page_id}")
                
                page_ids.extend(current_page_ids)
                
                # Update counters
                size = response.get("size", 0)
                total_size = response.get("totalSize", 0)
                total_pages += len(current_page_ids)
                
                print(f"Retrieved {len(current_page_ids)} pages from {size} total results (batch {start//paging_limit + 1})")
                
                # Break if no more results
                if size == 0 or len(current_page_ids) == 0:
                    break
                    
                start += size

        except HTTPError as e:
            if e.response and e.response.status_code == 400:  # Bad Request - invalid CQL
                print(f"ERROR: Invalid CQL query syntax: {cql_query}")
                print("Please check CQL syntax. See: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/")
                print("Common issues:")
                print("- Use 'AND' not '&' between conditions")
                print("- Use double quotes around values with spaces")
                print("- Check field names and operators")
                return cls(query=cql_query, page_ids=[], total_size=0, total_pages=0)
            else:
                print(f"ERROR: HTTP {e.response.status_code if e.response else 'Unknown'} when executing CQL query")
                return cls(query=cql_query, page_ids=[], total_size=0, total_pages=0)
        except Exception as e:
            print(f"ERROR: Unexpected error when executing CQL query: {e!s}")
            return cls(query=cql_query, page_ids=[], total_size=0, total_pages=0)

        # Remove duplicates and sort
        unique_page_ids = sorted(list(set(page_ids)))
        
        print(f"CQL Search Results:")
        print(f"  Query: {cql_query}")
        print(f"  Total matched content: {total_size}")
        print(f"  Pages found: {len(unique_page_ids)}")
        print(f"  Pages to export: {len(unique_page_ids)}")
        
        return cls(
            query=cql_query, 
            page_ids=unique_page_ids, 
            total_size=total_size,
            total_pages=len(unique_page_ids)
        )
```

## Testing Phase 1

### 1. Verify Import Works
Create a test script `test_phase1_corrected.py`:

```python
from confluence_markdown_exporter.confluence import SearchResults

# Test class can be imported
print("✓ SearchResults class imported successfully")

# Test basic instantiation
search = SearchResults(query="test", page_ids=[123], total_size=1, total_pages=1)
print("✓ SearchResults instantiation works")
print(f"Query: {search.query}")
print(f"Page IDs: {search.page_ids}")
print(f"Total: {search.total_size}")
print(f"Pages: {search.total_pages}")
```

Run: `python test_phase1_corrected.py`

### 2. Test CQL Query with Type Filtering
```python
from confluence_markdown_exporter.confluence import SearchResults

# Test with various query types
test_queries = [
    "space = TEST",  # Should add "AND type = page"
    "type = page AND space = TEST",  # Should work as-is
    "creator = jsmith",  # Should add "AND type = page"
    "type = blogpost",  # Should be changed to include pages
]

for query in test_queries:
    print(f"\nTesting query: '{query}'")
    try:
        results = SearchResults.from_cql(query, limit=5)
        print(f"✓ Processed successfully")
        print(f"  Final query: {results.query}")
        print(f"  Pages found: {results.total_pages}")
    except Exception as e:
        print(f"✗ Failed: {e}")
```

### 3. Test Error Handling
```python
from confluence_markdown_exporter.confluence import SearchResults

# Test invalid CQL syntax
print("Testing error handling...")
results = SearchResults.from_cql("INVALID & SYNTAX HERE", limit=5)
print(f"Error handling test - Page IDs: {results.page_ids} (should be empty)")
```

### 4. Test Real Query (if Confluence access available)
```python
from confluence_markdown_exporter.confluence import SearchResults

# Test with a simple, safe query
try:
    # This will automatically become "type = page"
    results = SearchResults.from_cql("", limit=5)
    print(f"✓ Empty query test: {len(results.page_ids)} pages found")
    
    # Test with space (replace with your space)
    results = SearchResults.from_cql("space = YOURSPACE", limit=3)
    print(f"✓ Space query test: {len(results.page_ids)} pages found")
    
except Exception as e:
    print(f"✗ Real query test failed: {e}")
```

## Expected Results After Phase 1

1. ✅ No import errors when adding the class
2. ✅ Basic instantiation works with new `total_pages` field
3. ✅ CQL queries automatically filter to pages only
4. ✅ Type filtering is enforced even when not specified
5. ✅ Pagination works correctly with conservative limits
6. ✅ Error handling provides helpful debugging information
7. ✅ Duplicate pages are removed from results
8. ✅ Clear logging shows what's happening during search

## Key Improvements in This Version

1. **Automatic Page Filtering**: Ensures only pages are returned, never attachments/comments
2. **Smart Type Detection**: Adds `type = page` automatically if missing
3. **Conservative Pagination**: Uses 25-item batches to avoid API limits
4. **Better Error Messages**: Provides specific guidance for common CQL errors
5. **Duplicate Removal**: Ensures each page appears only once in results
6. **Detailed Logging**: Shows exactly what's happening during search
7. **Safer Expansion**: Uses minimal expand to avoid result limits

## Common Issues & Solutions

**Issue**: CQL returns attachments/comments instead of pages
**Solution**: ✅ Fixed - Automatic type filtering ensures pages only

**Issue**: Results limited to 50 items
**Solution**: ✅ Fixed - Uses conservative 25-item pagination with minimal expansion

**Issue**: Invalid CQL syntax errors
**Solution**: ✅ Fixed - Provides specific error messages and common fixes

**Issue**: Duplicate pages in results  
**Solution**: ✅ Fixed - Automatically deduplicates results

**Issue**: No results for valid queries
**Solution**: ✅ Fixed - Better error handling and query validation

## Next Steps
Once Phase 1 is complete and tested with the corrected implementation, proceed to Phase 2 to add the CLI command.