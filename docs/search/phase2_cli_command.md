# Phase 2: CLI Command Implementation (CORRECTED)

## Objective
Add the `search` command to the CLI interface with proper CQL query handling and pages-only filtering.

## Prerequisites
- Phase 1 completed successfully with corrected `SearchResults` class
- `SearchResults` class is working and tested for page filtering

## Files to Modify

### 1. `confluence_markdown_exporter/main.py`

**Action**: Add the new `search` command after the existing commands.

**Location**: After the `all_spaces` command function, before the `config` command.

**Code to Add**:

```python
@app.command(help="Export Confluence pages matching a CQL (Confluence Query Language) query.")
def search(
    cql_query: Annotated[str, typer.Argument(help="CQL query string (will be filtered to pages only)")],
    output_path: Annotated[Path | None, typer.Argument()] = None,
    max_results: Annotated[int, typer.Option("--limit", "-m", help="Maximum number of pages to export")] = 100,
    include_all_types: Annotated[bool, typer.Option("--include-all-types", help="Include blog posts, comments, etc. (default: pages only)")] = False,
) -> None:
    from confluence_markdown_exporter.confluence import SearchResults

    # Modify query based on include_all_types flag
    final_query = cql_query
    if include_all_types:
        print("⚠️  Including all content types (pages, blog posts, comments, attachments)")
        print("⚠️  Only pages will be exported as markdown - other content types will be skipped")
    else:
        print("🔍 Filtering results to pages only")

    with measure(f"Export search results for: {final_query}"):
        override_output_path_config(output_path)
        results = SearchResults.from_cql(final_query, limit=max_results)
        
        if results.page_ids:
            print(f"📄 Exporting {len(results.page_ids)} pages...")
            results.export()
            print(f"✅ Export completed! Check output directory: {settings.export.output_path}")
        else:
            print("❌ No pages found matching the query")
            print("💡 Try:")
            print("   - Broadening your search terms")
            print("   - Checking space names and user names")
            print("   - Using simpler CQL syntax")
            print("   - Running with --help to see example queries")
```

**Important**: Make sure this is added in the correct indentation level (same as other `@app.command` functions).

## Testing Phase 2

### 1. Test CLI Help Command
```bash
confluence-markdown-exporter --help
```

**Expected Output**: Should show the new `search` command in the list of available commands.

### 2. Test Search Command Help
```bash
confluence-markdown-exporter search --help
```

**Expected Output**:
```
Usage: confluence-markdown-exporter search [OPTIONS] CQL_QUERY [OUTPUT_PATH]

Export Confluence pages matching a CQL (Confluence Query Language) query.

Arguments:
  CQL_QUERY     CQL query string (will be filtered to pages only) [required]
  OUTPUT_PATH   [default: None]

Options:
  -m, --limit INTEGER     Maximum number of pages to export [default: 100]
  --include-all-types           Include blog posts, comments, etc. (default: pages only)
  --help                        Show this message and exit.
```

### 3. Test Page-Only Filtering
```bash
# These should all return pages only
confluence-markdown-exporter search "space = TEST" ./test_output/
confluence-markdown-exporter search "creator = jsmith" ./test_output/
confluence-markdown-exporter search "lastModified >= startOfWeek()" ./test_output/
```

**Expected Behavior**:
- Should show "🔍 Filtering results to pages only" message
- Should automatically add `AND type = page` to queries
- Should only export markdown files (no attachments, comments, etc.)

### 4. Test All Content Types Option
```bash
confluence-markdown-exporter search "space = TEST" ./test_output/ --include-all-types
```

**Expected Behavior**:
- Should show warning about including all content types
- Should still only export pages as markdown (other types skipped)
- Should show more results in the search but same number exported

### 5. Test Max Results Option
```bash
confluence-markdown-exporter search "type = page" ./test_output/ --limit 5
```

**Expected Behavior**:
- Should limit results to 5 pages maximum
- Should show "📄 Exporting 5 pages..." (or fewer if less than 5 exist)

### 6. Test Error Handling
```bash
confluence-markdown-exporter search "INVALID & SYNTAX" ./test_output/
```

**Expected Behavior**:
- Should show CQL syntax error message
- Should provide helpful tips about using 'AND' instead of '&'
- Should not crash
- Should complete gracefully with no exports

### 7. Test Empty Results
```bash
confluence-markdown-exporter search "space = NONEXISTENT" ./test_output/
```

**Expected Behavior**:
- Should show "❌ No pages found matching the query"
- Should provide helpful suggestions
- Should not crash

## Integration Test

### Full Workflow Test
Create a test script `test_phase2_corrected.py`:

```python
import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        print(f"Command: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return False, ""
    except Exception as e:
        print(f"Failed to run command: {e}")
        return False, ""

# Test commands
test_output = Path("./test_integration_output")
test_output.mkdir(exist_ok=True)

tests = [
    ("Help test", "confluence-markdown-exporter --help"),
    ("Search help test", "confluence-markdown-exporter search --help"),
    ("Invalid syntax test", "confluence-markdown-exporter search 'INVALID & SYNTAX' ./test_output/"),
    # Add real tests with your space:
    # ("Real search test", f"confluence-markdown-exporter search 'space = YOURSPACE' {test_output} --limit 2")
]

print("🧪 Testing Phase 2 Corrected Implementation\n")

for test_name, test_cmd in tests:
    print(f"Running {test_name}...")
    success, output = run_command(test_cmd)
    
    if "help" in test_name.lower():
        # For help tests, check if search command is mentioned
        if "search" in output:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED - 'search' not found in help")
    elif "invalid" in test_name.lower():
        # For invalid syntax, should not crash
        if success or "ERROR: Invalid CQL query syntax" in output:
            print(f"✅ {test_name}: PASSED - Handled gracefully")
        else:
            print(f"❌ {test_name}: FAILED - Did not handle error properly")
    else:
        print(f"{'✅' if success else '❌'} {test_name}: {'PASSED' if success else 'FAILED'}")
    
    print("-" * 60)

print("\n📋 Manual Tests Required:")
print("1. Test with a real space key from your Confluence")
print("2. Verify that only .md files are created (no other file types)")
print("3. Check that pages are exported with same quality as individual page export")
print("4. Test different CQL queries to ensure type filtering works")
```

Run: `python test_phase2_corrected.py`

### Verify Page-Only Export Behavior
Create a test script `test_pages_only.py`:

```python
import os
from pathlib import Path
from confluence_markdown_exporter.confluence import SearchResults

def test_pages_only_export():
    """Test that only pages are exported, not other content types."""
    
    # Create test output directory
    test_dir = Path("./test_pages_only")
    test_dir.mkdir(exist_ok=True)
    
    # Test with a query that might return mixed content
    try:
        # This should automatically filter to pages only
        results = SearchResults.from_cql("space = TEST", limit=5)
        
        print(f"Query: {results.query}")
        print(f"Should contain 'type = page': {'type = page' in results.query}")
        print(f"Pages found: {results.total_pages}")
        
        if results.page_ids:
            print(f"First few page IDs: {results.page_ids[:3]}")
        
        # Verify the export creates only .md files
        results.export()
        
        # Check files created
        md_files = list(test_dir.glob("**/*.md"))
        other_files = [f for f in test_dir.glob("**/*") if f.is_file() and not f.name.endswith('.md')]
        
        print(f"\nFiles created:")
        print(f"  Markdown files: {len(md_files)}")
        print(f"  Other files: {len(other_files)}")
        
        if other_files:
            print(f"  Other file types: {[f.suffix for f in other_files]}")
        
        return len(md_files) > 0 and len(other_files) == 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Pages-Only Export Behavior")
    success = test_pages_only_export()
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: Pages-only export test")
```

## Troubleshooting

### Common Issues

**Issue**: `search` command not showing in help
**Solution**: 
- Check indentation of the new function
- Ensure it's properly decorated with `@app.command`
- Restart your terminal/environment

**Issue**: CQL queries return no results
**Solution**: 
- Check that automatic type filtering is working
- Verify space names and user names exist
- Try simpler queries first
- Use `--include-all-types` to see if broader search returns results

**Issue**: Export creates non-markdown files
**Solution**: 
- This should not happen with corrected implementation
- Check that SearchResults is properly filtering to pages only
- Verify the export_pages function is working correctly

**Issue**: Error messages not helpful
**Solution**:
- Check that the improved error handling from Phase 1 is working
- Verify the import of SearchResults is correct

## Validation Checklist

Before proceeding to Phase 3:

- [ ] `confluence-markdown-exporter --help` shows the `search` command
- [ ] `confluence-markdown-exporter search --help` shows proper usage including page filtering
- [ ] Basic search query executes and filters to pages only
- [ ] `--limit` option works correctly
- [ ] `--include-all-types` option shows warning but still exports pages only
- [ ] Error handling works for invalid CQL queries with helpful messages
- [ ] Files are exported to the specified output directory as .md files only
- [ ] Empty results provide helpful suggestions

## Key Improvements in This Version

1. **Pages-Only by Default**: Clear messaging that only pages are exported
2. **Include All Types Option**: Advanced option for broader searches
3. **Better User Feedback**: Clear progress messages and error guidance
4. **Helpful Error Messages**: Specific suggestions for common issues
5. **Empty Results Handling**: Constructive suggestions when no results found

## Next Steps

Once Phase 2 is complete and all tests pass, proceed to Phase 3 for updated documentation that reflects the pages-only behavior and corrected CQL syntax.
