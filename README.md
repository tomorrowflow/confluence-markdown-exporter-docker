<p align="center">
  <a href="https://github.com/Spenhouet/confluence-markdown-exporter"><img src="https://raw.githubusercontent.com/Spenhouet/confluence-markdown-exporter/b8caaba935eea7e7017b887c86a740cb7bf99708/logo.png" alt="confluence-markdown-exporter"></a>
</p>
<p align="center">
    <em>The confluence-markdown-exporter exports Confluence pages in Markdown format. This exporter helps in migrating content from Confluence to platforms that support Markdown e.g. Obsidian, Gollum, Azure DevOps (ADO), Foam, Dendron and more.</em>
</p>
<p align="center">
  <a href="https://github.com/Spenhouet/confluence-markdown-exporter/actions/workflows/publish.yml"><img src="https://github.com/Spenhouet/confluence-markdown-exporter/actions/workflows/publish.yml/badge.svg" alt="Build and publish to PyPI"></a>
  <a href="https://pypi.org/project/confluence-markdown-exporter" target="_blank">
    <img src="https://img.shields.io/pypi/v/confluence-markdown-exporter?color=%2334D058&label=PyPI%20package" alt="Package version">
   </a>
</p>

## Features

- Converts Confluence pages to Markdown format.
- Uses the Atlassian API to export individual pages, pages including children, and whole spaces.
- Supports various Confluence elements such as headings, paragraphs, lists, tables, and more.
- Retains formatting such as bold, italic, and underline.
- Converts Confluence macros to equivalent Markdown syntax where possible.
- Handles images and attachments by linking them appropriately in the Markdown output.
- Supports extended Markdown features like tasks, alerts, and front matter.

## Supported Markdown Elements

- **Headings**: Converts Confluence headings to Markdown headings.
- **Paragraphs**: Converts Confluence paragraphs to Markdown paragraphs.
- **Lists**: Supports both ordered and unordered lists.
- **Tables**: Converts Confluence tables to Markdown tables.
- **Formatting**: Supports bold, italic, and underline text.
- **Links**: Converts Confluence links to Markdown links.
- **Images**: Converts Confluence images to Markdown images with appropriate links.
- **Code Blocks**: Converts Confluence code blocks to Markdown code blocks.
- **Tasks**: Converts Confluence tasks to Markdown task lists.
- **Alerts**: Converts Confluence info panels to Markdown alert blocks.
- **Front Matter**: Adds front matter to the Markdown files for metadata like page properties and page labels.

## Usage

To use the confluence-markdown-exporter, follow these steps:

### 1. Installation

Install python package via pip.

```sh
pip install confluence-markdown-exporter
```

### 2. Exporting

Run the exporter with the desired Confluence page ID or space key. Execute the console application by typing `confluence-markdown-exporter` and one of the commands `page`, `page-with-descendants`, `space`, `all-spaces` or `config`. If a command is unclear, you can always add `--help` to get additional information. 

> [!TIP]
> Instead of `confluence-markdown-exporter` you can also use the shorthand `cf-export`.

#### 2.1. Export Page

Export a single Confluence page by ID:

```sh
confluence-markdown-exporter page <page-id e.g. 645208921> <output path e.g. ./output_path/>
```

or by URL:

```sh
confluence-markdown-exporter page <page-url e.g. https://company.atlassian.net/MySpace/My+Page+Title> <output path e.g. ./output_path/>
```

#### 2.2. Export Page with Descendants

Export a Confluence page and all its descendant pages by page ID:

```sh
confluence-markdown-exporter page-with-descendants <page-id e.g. 645208921> <output path e.g. ./output_path/>
```

or by URL:

```sh
confluence-markdown-exporter page-with-descendants <page-url e.g. https://company.atlassian.net/MySpace/My+Page+Title> <output path e.g. ./output_path/>
```

#### 2.3. Export Space

Export all Confluence pages of a single Space:

```sh
confluence-markdown-exporter space <space-key e.g. MYSPACE> <output path e.g. ./output_path/>
```

#### 2.3. Export all Spaces

Export all Confluence pages across all spaces:

```sh
confluence-markdown-exporter all-spaces <output path e.g. ./output_path/>
```

#### 2.4. Export by CQL Search Query

Export Confluence pages matching a CQL (Confluence Query Language) query. **Only pages are exported** - blog posts, comments, and attachments are automatically filtered out.

```bash
python -m confluence_markdown_exporter.main search 'lastModified > now("-1d")' --limit 3
```

Search with multiple criteria:

```bash
confluence-markdown-exporter search "label = important AND creator = jsmith" ./output_path/
```

Limit the number of results:

```bash
confluence-markdown-exporter search "type = page" ./output_path/ --max-results 50
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
confluence-markdown-exporter search "creator = jsmith" ./output/ --max-results 25
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
confluence-markdown-exporter search "space = DOCS" ./output/ --max-results 5

# Add conditions gradually
confluence-markdown-exporter search "space = DOCS AND creator = jsmith" ./output/ --max-results 5

# Use fuzzy search for text
confluence-markdown-exporter search "space = DOCS AND title ~ API" ./output/ --max-results 5
```

For complete CQL syntax documentation, see: [Atlassian CQL Documentation](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)

## Configuration

All configuration and authentication is stored in a single JSON file managed by the application. You do not need to manually edit this file.

### Interactive Configuration

To interactively view and change configuration, run:

```sh
confluence-markdown-exporter config
```

This will open a menu where you can:
- See all config options and their current values
- Select a config to change (including authentication)
- Reset all config to defaults
- Navigate directly to any config section (e.g. `auth.confluence`)

### Available Configuration Options

| Key | Description | Default |
|-----|-------------|---------|
| export.output_path | The directory where all exported files and folders will be written. Used as the base for relative and absolute links. | ./ (current working directory) |
| export.page_href | How to generate links to pages in Markdown. Options: "relative" (default) or "absolute". "relative" links are relative to the page, "absolute" links start from the configured output path. | relative |
| export.page_path | Path template for exported pages | {space_name}/{homepage_title}/{ancestor_titles}/{page_title}.md |
| export.attachment_href | How to generate links to attachments in Markdown. Options: "relative" (default) or "absolute". "relative" links are relative to the page, "absolute" links start from the configured output path. | relative |
| export.attachment_path | Path template for attachments | {space_name}/attachments/{attachment_file_id}{attachment_extension} |
| export.page_breadcrumbs | Whether to include breadcrumb links at the top of the page. | True |
| export.include_document_title | Whether to include the document title in the exported markdown file. | True |
| retry_config.backoff_and_retry | Enable automatic retry with exponential backoff | True |
| retry_config.backoff_factor | Multiplier for exponential backoff | 2 |
| retry_config.max_backoff_seconds | Maximum seconds to wait between retries | 60 |
| retry_config.max_backoff_retries | Maximum number of retry attempts | 5 |
| retry_config.retry_status_codes | HTTP status codes that trigger a retry | \[413, 429, 502, 503, 504\] |
| auth.confluence.url | Confluence instance URL | "" |
| auth.confluence.username | Confluence username/email | "" |
| auth.confluence.api_token | Confluence API token | "" |
| auth.confluence.pat | Confluence Personal Access Token | "" |
| auth.jira.url | Jira instance URL | "" |
| auth.jira.username | Jira username/email | "" |
| auth.jira.api_token | Jira API token | "" |
| auth.jira.pat | Jira Personal Access Token | "" |

You can always view and change the current config with the interactive menu above.

### Configuration for Target Systems

Some platforms have specific requirements for Markdown formatting, file structure, or metadata. You can adjust the export configuration to optimize output for your target system. Below are some common examples:

#### Obsidian

- **Document Titel**: Obsidian already displays the document title. Ensure `export.include_document_title` is `False` so the documented title is not redundant.
- **Breadcrumbs**: Obsidian already displays page breadcrumbs. Ensure `export.breadcrumbs` is `False` so the breadcrumbs are not redundant.

#### Azure DevOps (ADO) Wikis

- **Absolute Attachment Links**: Ensure `export.attachment_href` is set to `absolute`.

### Custom Config File Location

By default, configuration is stored in a platform-specific application directory. You can override the config file location by setting the `CME_CONFIG_PATH` environment variable to the desired file path. If set, the application will read and write config from this file instead. Example:

```sh
export CME_CONFIG_PATH=/path/to/your/custom_config.json
```

This is useful for using different configs for different environments or for scripting.

## Update

Update python package via pip.

```sh
pip install confluence-markdown-exporter --upgrade
```

## Compatibility

This package is not tested extensively. Please check all output and report any issue [here](https://github.com/Spenhouet/confluence-markdown-exporter/issues).
It generally was tested on:
- Confluence Cloud 1000.0.0-b5426ab8524f (2025-05-28)
- Confluence Server 8.5.20

## Known Issues
1. **Missing Attachment File ID on Server**: For some Confluence Server version/configuration the attachment file ID might not be provided (https://github.com/Spenhouet/confluence-markdown-exporter/issues/39). In the default configuration, this is used for the export path. Solution: Adjust the attachment path in the export config and use the `{attachment_id}` or `{attachment_title}` instead.
2. **Connection Issues when behind Proxy or VPN**: There might be connection issues if your Confluence Server is behind a proxy or VPN (https://github.com/Spenhouet/confluence-markdown-exporter/issues/38). If you experience issues, help to fix this is appreciated.

## Contributing

If you would like to contribute, please read [our contribution guideline](CONTRIBUTING.md).

## License

This tool is an open source project released under the [MIT License](LICENSE).
