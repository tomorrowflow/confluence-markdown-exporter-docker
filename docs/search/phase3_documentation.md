# Phase 3: Documentation Updates (CORRECTED)

## Objective
Update the README.md file to document the search functionality with accurate CQL syntax, pages-only filtering behavior, and clear troubleshooting guidance.

## Prerequisites
- Phase 1 and Phase 2 completed successfully with corrected implementations
- Search command is working and tested for pages-only export

## Files to Modify

### 1. `README.md`

**Action**: Add new section for search functionality in the Usage section.

**Location**: After section "#### 2.3. Export all Spaces" and before section "### 3. Output"

**Code to Add**:

```markdown
#### 2.4. Export by CQL Search Query

Export Confluence pages matching a CQL (Confluence Query Language) query. **Only pages are exported** - blog posts, comments, and attachments are automatically filtered out.

```bash
confluence-markdown-exporter search "space = MYSPACE AND lastModified >= startOfWeek()" <output path e.g. ./output_path/>
```

Search with multiple criteria:

```bash
confluence-markdown-exporter search "label = important AND creator = jsmith" ./output_path/
```

Limit the number of results:

```bash
confluence-markdown-exporter search "type = page" ./output_path/ --limit 50
```

**Important Notes:**
- 🔍 **Pages Only**: Searches automatically filter to pages only. Blog posts, comments, and attachments are excluded from export.
- 📝 **Automatic Type Filtering**: If you don't specify `type = page`, it's automatically added to your query.
- 📄 **Markdown Export**: Only page content is exported as markdown files, maintaining the same quality as individual page exports.

**Common CQL Query Patterns:**

| Use Case | CQL Query Example | What It Does |
|----------|------------------|--------------|
| **Pages in specific space** | `space = ENGINEERING` | All pages in ENGINEERING space |
| **Recent updates** | `lastModified >= startOfMonth()` | Pages modified this month |
| **Pages by author** | `creator = jsmith` | Pages created by user jsmith |
| **Pages edited by author** | `contributor = jsmith` | Pages edited by user jsmith |
| **Pages with labels** | `label IN (urgent, review)` | Pages tagged with urgent OR review |
| **Multiple labels** | `label = urgent AND label = review` | Pages tagged with urgent AND review |
| **Text search** | `title ~ "API"` | Pages with "API" in the title |
| **Descendant pages** | `ancestor = 12345` | All pages under page ID 12345 |
| **Date range** | `created >= "2024-01-01" AND created < "2024-02-01"` | Pages created in January 2024 |
| **Complex search** | `space = DOCS AND (label = api OR title ~ "API") AND lastModified >= startOfMonth()` | Multi-criteria search |

**Advanced Options:**

```bash
# Include all content types in search (still exports pages only)
confluence-markdown-exporter search "space = DOCS" ./output/ --include-all-types

# Limit results
confluence-markdown-exporter search "creator = jsmith" ./output/ --limit 25
```

**CQL Syntax Reference:**

**Fields (commonly used):**
- `space` - Space key (e.g., `space = DOCS`)
- `title` - Page title (e.g., `title = "My Page"` or `title ~ "keyword"`)
- `creator` - Page creator (e.g., `creator = jsmith`)
- `contributor` - Page contributor/editor (e.g., `contributor = jsmith`)
- `label` - Page labels (e.g., `label = important`)
- `created` - Creation date (e.g., `created >= startOfWeek()`)
- `lastModified` - Last modified date (e.g., `lastModified >= "2024-01-01"`)
- `ancestor` - Parent page ID (e.g., `ancestor = 12345`)

**Operators:**
- `=` - Equals (exact match)
- `!=` - Not equals
- `~` - Contains/fuzzy match (e.g., `title ~ "keyword"`)
- `!~` - Does not contain
- `IN` - In list (e.g., `label IN (urgent, review)`)
- `NOT IN` - Not in list
- `<`, `>`, `<=`, `>=` - Comparison (for dates/numbers)

**Date Functions:**
- `startOfWeek()` - Beginning of current week
- `startOfMonth()` - Beginning of current month
- `startOfYear()` - Beginning of current year
- `endOfWeek()`, `endOfMonth()`, `endOfYear()` - End of periods
- `now('-7d')` - 7 days ago
- `now('-1M')` - 1 month ago

**Logical Operators:**
- `AND` - Both conditions must be true
- `OR` - Either condition can be true
- `NOT` - Condition must not be true
- `()` - Group conditions

**Common CQL Mistakes and Fixes:**

❌ **Wrong**: `space = DOCS & creator = jsmith`  
✅ **Correct**: `space = DOCS AND creator = jsmith`

❌ **Wrong**: `title = My Page Title`  
✅ **Correct**: `title = "My Page Title"` (use quotes for spaces)

❌ **Wrong**: `label = urgent, review`  
✅ **Correct**: `label IN (urgent, review)` or `label = urgent OR label = review`

❌ **Wrong**: `created > 2024-01-01`  
✅ **Correct**: `created >= "2024-01-01"` (use quotes for dates)

**Troubleshooting Search Issues:**

If your search returns no results:

1. **Check space keys**: Ensure space keys exist and are spelled correctly
2. **Verify user names**: Use exact usernames as they appear in Confluence
3. **Simplify query**: Start with simple queries like `space = YOURSPACE`
4. **Check permissions**: Ensure you have access to the spaces you're searching
5. **Use fuzzy search**: Try `title ~ "keyword"` instead of exact matches
6. **Check date formats**: Use quotes around dates: `"2024-01-01"`

**Example Troubleshooting Session:**

```bash
# Start simple
confluence-markdown-exporter search "space = DOCS" ./output/ --limit 5

# Add conditions gradually  
confluence-markdown-exporter search "space = DOCS AND creator = jsmith" ./output/ --limit 5

# Use fuzzy search for text
confluence-markdown-exporter search "space = DOCS AND title ~ API" ./output/ --limit 5
```

For complete CQL syntax documentation, see: [Atlassian CQL Documentation](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
```

### 2. Update Table of Contents (if present)

**Action**: If your README has a table of contents, add the new section.

**Location**: In the table of contents section

**Code to Add**:
```markdown
  - [2.4. Export by CQL Search Query](#24-export-by-cql-search-query)
```

### 3. Update the shorthand tip section

**Action**: Update the tip about using `cf-export` to include the search command.

**Location**: Find the existing tip section that mentions `cf-export`

**Update the existing text**:
```markdown
Tip

Instead of confluence-markdown-exporter you can also use the shorthand cf-export for all commands including search.

Examples:
- `cf-export page 12345 ./output/`
- `cf-export search "space = DOCS" ./output/`
- `cf-export search "creator = jsmith AND lastModified >= startOfWeek()" ./output/ --limit 20`
```

## Testing Phase 3

### 1. Verify Documentation Formatting
- Open the README.md file in a markdown viewer (GitHub, VS Code, etc.)
- Check that all tables render correctly
- Ensure code blocks are properly formatted
- Verify links work

### 2. Test All Example Commands
Test every command example from the documentation:

```bash
# Test basic examples
confluence-markdown-exporter search "space = YOURSPACE" ./test_docs/
confluence-markdown-exporter search "creator = jsmith" ./test_docs/
confluence-markdown-exporter search "lastModified >= startOfWeek()" ./test_docs/

# Test complex examples
confluence-markdown-exporter search "space = DOCS AND label = important" ./test_docs/
confluence-markdown-exporter search "title ~ API AND created >= startOfMonth()" ./test_docs/

# Test options
confluence-markdown-exporter search "space = DOCS" ./test_docs/ --limit 5
confluence-markdown-exporter search "space = DOCS" ./test_docs/ --include-all-types

# Test troubleshooting examples
confluence-markdown-exporter search "space = NONEXISTENT" ./test_docs/  # Should show helpful error
```

### 3. Validate CQL Examples
Create a test script `test_cql_documentation.py`:

```python
"""Test that all CQL examples from documentation are syntactically valid."""

from confluence_markdown_exporter.confluence import SearchResults

# All CQL queries from the documentation
doc_queries = [
    # Basic patterns
    "space = ENGINEERING",
    "lastModified >= startOfMonth()",
    "creator = jsmith", 
    "contributor = jsmith",
    "label IN (urgent, review)",
    "label = urgent AND label = review",
    "title ~ \"API\"",
    "ancestor = 12345",
    "created >= \"2024-01-01\" AND created < \"2024-02-01\"",
    "space = DOCS AND (label = api OR title ~ \"API\") AND lastModified >= startOfMonth()",
    
    # Corrected examples
    "space = DOCS AND creator = jsmith",
    "title = \"My Page Title\"",
    "label = urgent OR label = review", 
    "created >= \"2024-01-01\"",
    
    # Date functions
    "created >= startOfWeek()",
    "lastModified >= now('-7d')",
    "created >= now('-1M')",
]

print("🧪 Testing CQL Examples from Documentation")
print("=" * 50)

passed = 0
failed = 0

for i, query in enumerate(doc_queries, 1):
    try:
        # Test with limit 1 to minimize API calls but validate syntax
        results = SearchResults.from_cql(query, limit=1)
        print(f"✅ Example {i:2d}: Valid syntax")
        print(f"   Query: {query}")
        print(f"   Final: {results.query}")
        passed += 1
    except Exception as e:
        print(f"❌ Example {i:2d}: FAILED")
        print(f"   Query: {query}")
        print(f"   Error: {e}")
        failed += 1
    print()

print("=" * 50)
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("🎉 All documentation examples are valid!")
else:
    print("⚠️  Some examples need to be fixed in documentation")
```

Run: `python test_cql_documentation.py`

### 4. Test Troubleshooting Guidance
```bash
# Test each common mistake to ensure error messages are helpful

# Test & instead of AND
confluence-markdown-exporter search "space = DOCS & creator = jsmith" ./test_docs/

# Test missing quotes
confluence-markdown-exporter search "title = My Page Title" ./test_docs/

# Test invalid date format
confluence-markdown-exporter search "created > 2024-01-01" ./test_docs/

# Test non-existent space
confluence-markdown-exporter search "space = NONEXISTENT" ./test_docs/
```

Each should provide helpful error messages as documented.

## Quality Checklist

### Content Accuracy
- [ ] All example commands tested and work
- [ ] CQL syntax is accurately documented 
- [ ] Pages-only behavior clearly explained
- [ ] Troubleshooting section addresses real issues
- [ ] Common mistakes section prevents user errors

### Documentation Quality
- [ ] Tables render correctly
- [ ] Code blocks are properly formatted
- [ ] Consistent formatting with existing docs
- [ ] Clear, concise explanations
- [ ] Logical flow and organization

### Completeness
- [ ] Basic usage covered
- [ ] Advanced options documented
- [ ] Error scenarios explained
- [ ] Reference to official documentation
- [ ] Troubleshooting guide included

### User Experience
- [ ] Beginner-friendly examples
- [ ] Progressive complexity (simple to advanced)
- [ ] Common use cases covered
- [ ] Clear problem-solution pairs
- [ ] Easy to scan and find information

## Create Quick Reference Card (Optional)

Create a separate file `CQL_QUICK_REFERENCE.md` for easy lookup:

```markdown
# CQL Quick Reference for Confluence Markdown Exporter

## 🚀 Quick Start
```bash
# Export pages from a space
cf-export search "space = MYSPACE" ./output/

# Export recent pages
cf-export search "lastModified >= startOfWeek()" ./output/

# Export pages by author
cf-export search "creator = username" ./output/
```

## 📋 Common Patterns
| Pattern | Example |
|---------|---------|
| Space | `space = DOCS` |
| Author | `creator = jsmith` |
| Recent | `lastModified >= startOfWeek()` |
| Labels | `label IN (urgent, api)` |
| Title | `title ~ "keyword"` |
| Combined | `space = DOCS AND creator = jsmith` |

## ⚠️ Remember
- Use `AND` not `&`
- Quote values with spaces: `"My Title"`
- Pages only - no attachments/comments
- Use `~` for fuzzy text search
```

## Validation Steps

Before proceeding to Phase 4:

1. **Documentation Accuracy**: All examples work as documented
2. **Clarity**: New users can follow examples successfully  
3. **Completeness**: Common use cases and issues covered
4. **Integration**: New docs fit seamlessly with existing content
5. **Troubleshooting**: Error scenarios provide actionable guidance

## Next Steps

Phase 3 provides comprehensive documentation for the corrected CQL search functionality. Phase 4 is optional and adds an interactive CQL builder that incorporates the pages-only filtering and improved error handling.
