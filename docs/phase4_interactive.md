# Phase 4: Interactive CQL Builder (Optional Enhancement)

## Objective
Add an interactive command that helps users build CQL queries through a guided interface, making the tool more accessible to non-technical users.

## Prerequisites
- Phases 1, 2, and 3 completed successfully
- `questionary` dependency (already in requirements.txt)

## Files to Create/Modify

### 1. Create New File: `confluence_markdown_exporter/utils/cql_builder.py`

**Action**: Create a new file for the interactive CQL builder.

**Full File Content**:

```python
"""Interactive CQL query builder for common use cases."""

import questionary
from typing import Optional


def build_cql_interactively() -> Optional[str]:
    """Interactive CQL query builder for common use cases."""
    
    print("🔍 Interactive CQL Query Builder")
    print("This will help you build a Confluence search query step by step.\n")
    
    use_case = questionary.select(
        "What would you like to search for?",
        choices=[
            "Pages in a specific space",
            "Pages modified recently", 
            "Pages with specific labels",
            "Pages by author",
            "Pages with text in title",
            "Descendant pages of a parent",
            "Combination of criteria",
            "Write custom CQL query",
        ]
    ).ask()
    
    if not use_case:
        return None
    
    if use_case == "Pages in a specific space":
        return _build_space_query()
    
    elif use_case == "Pages modified recently":
        return _build_time_query()
    
    elif use_case == "Pages with specific labels":
        return _build_label_query()
    
    elif use_case == "Pages by author":
        return _build_author_query()
        
    elif use_case == "Pages with text in title":
        return _build_title_query()
        
    elif use_case == "Descendant pages of a parent":
        return _build_ancestor_query()
    
    elif use_case == "Combination of criteria":
        return _build_combination_query()
    
    else:  # Custom CQL query
        return _build_custom_query()


def _build_space_query() -> Optional[str]:
    """Build a space-based query."""
    space = questionary.text("Enter space key (e.g., DOCS, ENGINEERING):").ask()
    if not space:
        return None
    
    include_blogposts = questionary.confirm(
        "Include blog posts? (default: pages only)", 
        default=False
    ).ask()
    
    if include_blogposts:
        return f'space = "{space}"'
    else:
        return f'space = "{space}" AND type = page'


def _build_time_query() -> Optional[str]:
    """Build a time-based query."""
    time_field = questionary.select(
        "Search by:",
        choices=["Last modified", "Created date"]
    ).ask()
    
    if not time_field:
        return None
    
    field = "lastModified" if time_field == "Last modified" else "created"
    
    period = questionary.select(
        "Time period:",
        choices=[
            "This week", 
            "This month", 
            "This year",
            "Last 7 days",
            "Last 30 days",
            "Custom date"
        ]
    ).ask()
    
    if not period:
        return None
    
    period_map = {
        "This week": "startOfWeek()",
        "This month": "startOfMonth()", 
        "This year": "startOfYear()",
        "Last 7 days": "now('-7d')",
        "Last 30 days": "now('-30d')"
    }
    
    if period == "Custom date":
        date_str = questionary.text(
            "Enter date (YYYY-MM-DD format):",
            validate=lambda x: len(x) == 10 and x[4] == '-' and x[7] == '-'
        ).ask()
        if not date_str:
            return None
        return f'{field} >= "{date_str}" AND type = page'
    else:
        return f"{field} >= {period_map[period]} AND type = page"


def _build_label_query() -> Optional[str]:
    """Build a label-based query."""
    labels_input = questionary.text(
        "Enter labels (comma-separated, e.g., urgent, review, api):"
    ).ask()
    
    if not labels_input:
        return None
    
    labels = [label.strip() for label in labels_input.split(",")]
    
    if len(labels) == 1:
        return f'label = "{labels[0]}" AND type = page'
    else:
        label_list = ', '.join(f'"{label}"' for label in labels)
        return f"label IN ({label_list}) AND type = page"


def _build_author_query() -> Optional[str]:
    """Build an author-based query."""
    search_type = questionary.select(
        "Search for pages:",
        choices=["Created by user", "Contributed to by user", "Either created or contributed"]
    ).ask()
    
    if not search_type:
        return None
    
    username = questionary.text("Enter username:").ask()
    if not username:
        return None
    
    if search_type == "Created by user":
        return f'creator = "{username}" AND type = page'
    elif search_type == "Contributed to by user":
        return f'contributor = "{username}" AND type = page'
    else:  # Either
        return f'(creator = "{username}" OR contributor = "{username}") AND type = page'


def _build_title_query() -> Optional[str]:
    """Build a title-based query."""
    search_text = questionary.text("Enter text to search for in titles:").ask()
    if not search_text:
        return None
    
    search_type = questionary.select(
        "Search type:",
        choices=["Contains text (fuzzy)", "Exact phrase"]
    ).ask()
    
    if search_type == "Contains text (fuzzy)":
        return f'title ~ "{search_text}" AND type = page'
    else:
        return f'title = "{search_text}" AND type = page'


def _build_ancestor_query() -> Optional[str]:
    """Build an ancestor-based query."""
    ancestor_id = questionary.text(
        "Enter parent page ID (numeric):",
        validate=lambda x: x.isdigit() or x == ""
    ).ask()
    
    if not ancestor_id:
        return None
    
    return f"ancestor = {ancestor_id}"


def _build_combination_query() -> Optional[str]:
    """Build a combination query step by step."""
    print("\n📋 Building a combination query...")
    print("You'll add multiple criteria that will be combined with AND.\n")
    
    criteria = []
    
    while True:
        criterion_type = questionary.select(
            f"Add criterion #{len(criteria) + 1}:",
            choices=[
                "Space",
                "Time period", 
                "Author",
                "Label",
                "Title text",
                "✅ Finish building query"
            ]
        ).ask()
        
        if not criterion_type or criterion_type == "✅ Finish building query":
            break
        
        criterion = None
        
        if criterion_type == "Space":
            space = questionary.text("Space key:").ask()
            if space:
                criterion = f'space = "{space}"'
                
        elif criterion_type == "Time period":
            period = questionary.select(
                "Time period:",
                choices=["This week", "This month", "Last 7 days", "Last 30 days"]
            ).ask()
            period_map = {
                "This week": "startOfWeek()",
                "This month": "startOfMonth()", 
                "Last 7 days": "now('-7d')",
                "Last 30 days": "now('-30d')"
            }
            if period:
                criterion = f"lastModified >= {period_map[period]}"
                
        elif criterion_type == "Author":
            username = questionary.text("Username:").ask()
            if username:
                criterion = f'creator = "{username}"'
                
        elif criterion_type == "Label":
            label = questionary.text("Label name:").ask()
            if label:
                criterion = f'label = "{label}"'
                
        elif criterion_type == "Title text":
            text = questionary.text("Text in title:").ask()
            if text:
                criterion = f'title ~ "{text}"'
        
        if criterion:
            criteria.append(criterion)
            print(f"✅ Added: {criterion}")
    
    if not criteria:
        return None
    
    # Always add type = page unless space is specified (which might include blog posts)
    has_space_only = any("space =" in c and "type =" not in c for c in criteria)
    if not has_space_only:
        criteria.append("type = page")
    
    return " AND ".join(criteria)


def _build_custom_query() -> Optional[str]:
    """Allow user to enter custom CQL."""
    print("\n✏️  Custom CQL Query")
    print("You can use any valid CQL syntax. For reference:")
    print("- Fields: space, type, title, creator, label, created, lastModified")
    print("- Operators: =, !=, ~, IN, <, >, <=, >=")
    print("- Types: page, blogpost, comment, attachment")
    print("- Functions: startOfWeek(), startOfMonth(), now('-7d')")
    print("- Example: space = \"DOCS\" AND lastModified >= startOfWeek()\n")
    
    query = questionary.text(
        "Enter your CQL query:",
        validate=lambda x: len(x.strip()) > 0
    ).ask()
    
    return query.strip() if query else None


def preview_and_confirm_query(query: str) -> bool:
    """Show the query and confirm with user."""
    print(f"\n🔍 Generated CQL Query:")
    print(f"   {query}\n")
    
    return questionary.confirm(
        "Execute this query?",
        default=True
    ).ask()
```

### 2. Modify: `confluence_markdown_exporter/main.py`

**Action**: Add the interactive search command after the existing `search` command.

**Code to Add**:

```python
@app.command(help="Interactive CQL query builder and export.")
def search_interactive(
    output_path: Annotated[Path | None, typer.Argument()] = None,
    max_results: Annotated[int, typer.Option("--max-results", "-m", help="Maximum number of results to export")] = 100,
) -> None:
    from confluence_markdown_exporter.utils.cql_builder import build_cql_interactively, preview_and_confirm_query
    from confluence_markdown_exporter.confluence import SearchResults

    try:
        cql_query = build_cql_interactively()
        if not cql_query:
            print("❌ No query provided. Exiting.")
            return
        
        if not preview_and_confirm_query(cql_query):
            print("❌ Query cancelled by user.")
            return
        
        with measure(f"Export search results for: {cql_query}"):
            override_output_path_config(output_path)
            results = SearchResults.from_cql(cql_query, limit=max_results)
            results.export()
            
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
```

### 3. Update Documentation in README.md

**Action**: Add documentation for the interactive command.

**Location**: After the existing search documentation in section 2.4

**Code to Add**:

```markdown

##### Interactive Search Builder

For users who prefer a guided interface, use the interactive search builder:

```bash
confluence-markdown-exporter search-interactive ./output_path/
```

This will guide you through building a CQL query step by step with options for:
- Space-based searches
- Time-based filters
- Author searches  
- Label filtering
- Title text searches
- Complex combinations

The interactive mode is perfect for:
- Users new to CQL syntax
- Building complex multi-criteria queries
- Exploring available search options
- Learning CQL through examples
```

## Testing Phase 4

### 1. Test Interactive Builder
```bash
confluence-markdown-exporter search-interactive ./test_interactive/
```

**Test Each Menu Option**:
1. Select "Pages in a specific space" → enter a space key
2. Select "Pages modified recently" → choose "This week"
3. Select "Pages with specific labels" → enter some labels
4. Select "Pages by author" → enter a username
5. Select "Write custom CQL query" → enter a custom query

### 2. Test Integration with Search
Create test script `test_phase4.py`:

```python
from confluence_markdown_exporter.utils.cql_builder import (
    _build_space_query, 
    _build_time_query,
    preview_and_confirm_query
)

# Test individual functions
print("Testing CQL builder functions...")

# These would normally be interactive, but we can test the logic
print("✓ CQL builder functions imported successfully")

# Test preview function
test_query = 'space = "TEST" AND type = page'
print(f"Preview test query: {test_query}")
```

### 3. Test Error Handling
```bash
# Test cancellation (press Ctrl+C during interactive session)
confluence-markdown-exporter search-interactive ./test/

# Test with empty inputs (just press Enter on prompts)
confluence-markdown-exporter search-interactive ./test/
```

### 4. User Experience Test
Ask someone else to try the interactive mode and provide feedback on:
- Clarity of prompts
- Ease of use
- Usefulness of generated queries

## Integration Test Script

Create `test_phase4_complete.py`:

```python
"""Complete test of interactive CQL functionality."""

import subprocess
import tempfile
from pathlib import Path

def test_interactive_help():
    """Test that the interactive command shows in help."""
    result = subprocess.run(
        ["confluence-markdown-exporter", "--help"], 
        capture_output=True, text=True
    )
    return "search-interactive" in result.stdout

def test_interactive_command_help():
    """Test the interactive command help."""
    result = subprocess.run(
        ["confluence-markdown-exporter", "search-interactive", "--help"], 
        capture_output=True, text=True
    )
    return result.returncode == 0 and "Interactive CQL query builder" in result.stdout

# Run tests
print("🧪 Testing Phase 4 Interactive CQL Builder")

if test_interactive_help():
    print("✅ Interactive command appears in main help")
else:
    print("❌ Interactive command missing from main help")

if test_interactive_command_help():
    print("✅ Interactive command help works")
else:
    print("❌ Interactive command help failed")

print("\n📝 Manual test required:")
print("Run: confluence-markdown-exporter search-interactive ./test/")
print("Try each menu option to ensure the interactive experience works.")
```

## Quality Checklist

### Functionality
- [ ] Interactive builder launches without errors
- [ ] All menu options work correctly
- [ ] Generated queries are syntactically valid
- [ ] Preview and confirmation works
- [ ] Integration with export functionality works
- [ ] Error handling for cancelled operations

### User Experience  
- [ ] Clear, intuitive prompts
- [ ] Helpful guidance text
- [ ] Logical flow through options
- [ ] Easy to cancel/exit
- [ ] Good error messages
- [ ] Preview before execution

### Code Quality
- [ ] Well-structured functions
- [ ] Proper error handling
- [ ] Clear variable names
- [ ] Documented functions
- [ ] Follows existing code style

## Troubleshooting

**Issue**: `questionary` import errors
**Solution**: Verify questionary is in requirements.txt and installed

**Issue**: Interactive prompts don't work in some terminals
**Solution**: Test in different terminals, add note to documentation

**Issue**: Complex queries don't work as expected
**Solution**: Test generated queries manually, improve validation

## Final Validation

After Phase 4 completion:

1. **All Phases Working**: Test the complete workflow
2. **Documentation Updated**: All new features documented
3. **User Experience**: Get feedback from actual users
4. **Error Handling**: All edge cases handled gracefully

## Usage Summary

After all phases, users will have:

```bash
# Basic search
confluence-markdown-exporter search "space = DOCS" ./output/

# Interactive search  
confluence-markdown-exporter search-interactive ./output/

# All existing functionality still works
confluence-markdown-exporter page 12345 ./output/
confluence-markdown-exporter space DOCS ./output/
```

This completes the full CQL search implementation with both programmatic and user-friendly interfaces.