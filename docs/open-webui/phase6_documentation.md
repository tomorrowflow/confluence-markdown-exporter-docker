# Phase 6: Documentation and Final Integration

## Overview
Complete the implementation with comprehensive documentation, examples, and final integration testing to ensure a polished, production-ready solution.

## Task 6.1: Update Documentation

### Objective
Create comprehensive documentation for the Open-WebUI integration including setup guides, configuration options, and troubleshooting information.

### Files to Update/Create
- `README.md` (update)
- `docs/open-webui-integration.md` (create)
- `docs/configuration-guide.md` (create)
- `docs/troubleshooting.md` (create)
- `CHANGELOG.md` (update)

### Requirements
- Clear setup instructions for Open-WebUI integration
- Configuration parameter documentation
- Usage examples with screenshots/code samples
- Troubleshooting guide with common issues
- Migration guide from previous versions

### Reference Implementation

```markdown
# README.md (Updated sections)

## Open-WebUI Integration

The confluence-markdown-exporter now supports direct export to Open-WebUI knowledge bases, allowing you to seamlessly migrate your Confluence content to your Open-WebUI instance.

### Features

- **Automatic Knowledge Base Creation**: Creates knowledge bases named after your Confluence spaces
- **Metadata Enrichment**: Adds comprehensive Confluence metadata to exported files
- **Attachment Filtering**: Configurable file type filtering for attachments
- **Batch Upload**: Efficient batch processing for large exports
- **Progress Reporting**: Detailed progress tracking with success/failure reporting
- **Error Handling**: Robust error handling with detailed logging

### Quick Start

1. **Configure Open-WebUI Settings**
   ```bash
   python -m confluence_markdown_exporter.main config
   ```
   - Navigate to "Authentication" → "Open-WebUI"
   - Enter your Open-WebUI URL and API key
   - Navigate to "Export Settings" → "Open-WebUI Export"
   - Enable "Export to Open-WebUI"

2. **Export a Space**
   ```bash
   confluence-markdown-exporter space MYSPACE ./output_path/
   ```

3. **Check Your Open-WebUI Instance**
   - Your content will be available in a knowledge base named after your space
   - Files include enriched metadata from Confluence

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `auth.open_webui.url` | Open-WebUI instance URL | "" |
| `auth.open_webui.api_key` | Open-WebUI API key | "" |
| `export.export_to_open_webui` | Enable Open-WebUI export | false |
| `export.open_webui_attachment_extensions` | Allowed file extensions | "md,txt,pdf" |
| `export.open_webui_batch_add` | Use batch upload | true |

### Authentication

To use Open-WebUI integration, you need:

1. **Open-WebUI API Key**: Generate an API key from your Open-WebUI instance
2. **Proper Permissions**: Ensure your API key has permissions to create knowledge bases and upload files

### Metadata Enrichment

Exported files include comprehensive metadata:

**For Pages:**
```yaml
---
confluence_space: "MYSPACE"
confluence_space_name: "My Space"
confluence_homepage: "Home Page Title"
confluence_ancestors: ["Parent Page", "Child Page"]
confluence_page_name: "Current Page"
confluence_author: "john.doe@company.com"
confluence_created: "2024-01-15T10:30:00Z"
confluence_updated: "2024-01-20T14:45:00Z"
confluence_page_id: "12345"
confluence_page_url: "https://company.atlassian.net/wiki/spaces/MYSPACE/pages/12345"
---
```

**For Attachments:**
```yaml
---
confluence_space: "MYSPACE"
confluence_attachment_name: "document.pdf"
confluence_attachment_size: 1024000
confluence_attachment_media_type: "application/pdf"
confluence_attachment_url: "https://company.atlassian.net/wiki/download/attachments/12345/document.pdf"
confluence_parent_page_id: "12345"
---
```

### Troubleshooting

**Connection Issues:**
- Verify your Open-WebUI URL and API key
- Test connection: `confluence-markdown-exporter test-connection`
- Check firewall and network settings

**Upload Failures:**
- Check file size limits (default: 10MB)
- Verify file extensions are allowed
- Check Open-WebUI storage capacity

**Permission Errors:**
- Ensure API key has required permissions
- Check Open-WebUI user role settings

For detailed troubleshooting, see [docs/troubleshooting.md](docs/troubleshooting.md).
```

```markdown
# docs/open-webui-integration.md

# Open-WebUI Integration Guide

## Overview

This guide provides comprehensive information about integrating the confluence-markdown-exporter with Open-WebUI knowledge bases.

## Architecture

The Open-WebUI integration consists of several components:

1. **Open-WebUI API Client**: Handles communication with Open-WebUI
2. **Attachment Filter**: Filters files based on extensions and size
3. **Metadata Enricher**: Adds Confluence metadata to exported files
4. **Export Controller**: Orchestrates the export process
5. **Progress Reporter**: Provides detailed progress updates

## Configuration

### Authentication Configuration

```json
{
  "auth": {
    "open_webui": {
      "url": "https://your-openwebui-instance.com",
      "api_key": "your-api-key-here"
    }
  }
}
```

### Export Configuration

```json
{
  "export": {
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx",
    "open_webui_batch_add": true
  }
}
```

## Usage Examples

### Basic Space Export

```bash
# Configure first
python -m confluence_markdown_exporter.main config

# Export space
confluence-markdown-exporter space ENGINEERING ./output/
```

### Page Export with Descendants

```bash
confluence-markdown-exporter page-with-descendants 123456 ./output/
```

### Testing Connection

```bash
confluence-markdown-exporter test-connection
```

## API Key Setup

### Generating API Keys in Open-WebUI

1. Log in to your Open-WebUI instance
2. Navigate to Settings → API Keys
3. Click "Generate New Key"
4. Copy the generated key
5. Set appropriate permissions for knowledge base management

### Required Permissions

Your API key needs the following permissions:
- Read knowledge bases
- Create knowledge bases
- Upload files
- Manage knowledge base files

## Knowledge Base Management

### Naming Convention

Knowledge bases are created with the following naming scheme:
- **Name**: Confluence space name (e.g., "Engineering Documentation")
- **Description**: "Automated Confluence Export of [space_url]"

### File Organization

Files are organized within knowledge bases:
- Pages are uploaded as `.md` files
- Attachments maintain their original extensions
- All files include enriched metadata

## Metadata Schema

### Page Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `confluence_space` | Space key | "ENG" |
| `confluence_space_name` | Space display name | "Engineering" |
| `confluence_homepage` | Homepage title | "Engineering Home" |
| `confluence_ancestors` | Parent page titles | ["Docs", "API"] |
| `confluence_page_name` | Page title | "API Reference" |
| `confluence_author` | Page author | "john.doe@company.com" |
| `confluence_created` | Creation timestamp | "2024-01-15T10:30:00Z" |
| `confluence_updated` | Last update timestamp | "2024-01-20T14:45:00Z" |
| `confluence_page_id` | Confluence page ID | "12345" |
| `confluence_page_url` | Direct page URL | "https://..." |

### Attachment Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `confluence_attachment_name` | Attachment filename | "diagram.pdf" |
| `confluence_attachment_size` | File size in bytes | 1024000 |
| `confluence_attachment_media_type` | MIME type | "application/pdf" |
| `confluence_attachment_url` | Direct download URL | "https://..." |
| `confluence_parent_page_id` | Parent page ID | "12345" |

## Advanced Configuration

### Attachment Filtering

Control which attachments are exported:

```json
{
  "export": {
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx,jpg,png"
  }
}
```

### Batch Upload Settings

Configure batch upload behavior:

```json
{
  "export": {
    "open_webui_batch_add": true
  }
}
```

When enabled, files are uploaded in batches for better performance. When disabled, files are uploaded individually with more granular error handling.

## Performance Considerations

### Large Exports

For large Confluence spaces:
- Enable batch upload for better performance
- Monitor Open-WebUI storage capacity
- Consider filtering attachments to reduce size

### Network Optimization

- Use wired connections for large exports
- Ensure stable network connectivity
- Consider running exports during off-peak hours

## Security Considerations

### API Key Security

- Store API keys securely
- Use environment variables for production
- Rotate API keys regularly
- Limit API key permissions to minimum required

### Network Security

- Use HTTPS for Open-WebUI connections
- Consider VPN for remote Open-WebUI instances
- Implement proper firewall rules

## Monitoring and Logging

### Progress Monitoring

The exporter provides detailed progress information:

```
Processing 1/50: Getting Started.md
Uploading 'Getting Started.md' to knowledge base 'Engineering Docs'... Success
Processing 2/50: API Reference.md
Uploading 'API Reference.md' to knowledge base 'Engineering Docs'... Success
```

### Export Summaries

Detailed summaries are provided after export:

```
=== Export Summary ===
Knowledge Base: Engineering Docs (kb_12345)
Total Files: 45
  - Pages: 35
  - Attachments: 10
Successful: 43 (95.6%)
  - Pages: 35
  - Attachments: 8
Failed: 2
  - Pages: 0
  - Attachments: 2
Duration: 120.5 seconds
```

### Log Files

Logs are available in the application log directory:
- Operation logs
- Error details
- Performance metrics
- Export summaries

## Integration with CI/CD

### Automated Exports

```yaml
# GitHub Actions example
name: Export to Open-WebUI
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install confluence-markdown-exporter
      - name: Export to Open-WebUI
        env:
          CONFLUENCE_URL: ${{ secrets.CONFLUENCE_URL }}
          CONFLUENCE_TOKEN: ${{ secrets.CONFLUENCE_TOKEN }}
          OPENWEBUI_URL: ${{ secrets.OPENWEBUI_URL }}
          OPENWEBUI_API_KEY: ${{ secrets.OPENWEBUI_API_KEY }}
        run: |
          confluence-markdown-exporter space ENGINEERING ./output/
```

## Best Practices

### Content Organization

1. **Consistent Naming**: Use clear, consistent naming for spaces and pages
2. **Proper Tagging**: Use Confluence labels for better organization
3. **Regular Updates**: Schedule regular exports to keep content current

### Maintenance

1. **Monitor Storage**: Keep track of Open-WebUI storage usage
2. **Clean Up**: Remove outdated knowledge bases regularly
3. **Backup**: Maintain backups of critical knowledge bases

### Quality Assurance

1. **Test Exports**: Test with small spaces before large exports
2. **Validate Content**: Verify exported content is complete and accurate
3. **Monitor Errors**: Review error logs and address issues promptly

## Migration Strategies

### Initial Migration

1. **Audit Content**: Review Confluence content before migration
2. **Clean Up**: Remove obsolete or duplicate content
3. **Plan Structure**: Design Open-WebUI knowledge base structure
4. **Test Process**: Run test exports with sample content
5. **Full Migration**: Execute full migration during maintenance window

### Ongoing Synchronization

1. **Scheduled Exports**: Set up automated exports for regular updates
2. **Incremental Updates**: Consider implementing incremental updates
3. **Change Tracking**: Monitor and log content changes
4. **Conflict Resolution**: Handle conflicts between manual and automated updates

## Support and Resources

### Documentation

- [API Reference](api-reference.md)
- [Configuration Guide](configuration-guide.md)
- [Troubleshooting](troubleshooting.md)

### Community

- GitHub Issues: Report bugs and feature requests
- Discussions: Community support and tips
- Wiki: Additional documentation and examples

### Professional Support

For enterprise support and custom implementations, contact the development team.
```

```markdown
# docs/configuration-guide.md

# Configuration Guide

## Configuration File Structure

The configuration is stored in a JSON file with the following structure:

```json
{
  "auth": {
    "confluence": { /* Confluence settings */ },
    "jira": { /* Jira settings */ },
    "open_webui": { /* Open-WebUI settings */ }
  },
  "export": {
    /* Export settings including Open-WebUI options */
  },
  "retry_config": {
    /* Retry and backoff settings */
  }
}
```

## Authentication Configuration

### Open-WebUI Authentication

```json
{
  "auth": {
    "open_webui": {
      "url": "https://your-openwebui-instance.com",
      "api_key": "your-api-key-here"
    }
  }
}
```

**Parameters:**
- `url`: Full URL to your Open-WebUI instance (required)
- `api_key`: API key for authentication (required)

**Validation:**
- URL must be a valid HTTP/HTTPS URL
- API key must have required permissions

### Environment Variables

You can also use environment variables:

```bash
export OPENWEBUI_URL="https://your-openwebui-instance.com"
export OPENWEBUI_API_KEY="your-api-key-here"
```

## Export Configuration

### Basic Export Settings

```json
{
  "export": {
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx",
    "open_webui_batch_add": true
  }
}
```

**Parameters:**
- `export_to_open_webui`: Enable/disable Open-WebUI export (default: false)
- `open_webui_attachment_extensions`: Comma-separated list of allowed file extensions (default: "md,txt,pdf")
- `open_webui_batch_add`: Use batch upload for better performance (default: true)

### Advanced Export Settings

```json
{
  "export": {
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx,jpg,png,gif",
    "open_webui_batch_add": true,
    "open_webui_max_file_size_mb": 10,
    "open_webui_timeout_seconds": 300,
    "open_webui_retry_attempts": 3
  }
}
```

**Additional Parameters:**
- `open_webui_max_file_size_mb`: Maximum file size in MB (default: 10)
- `open_webui_timeout_seconds`: Request timeout in seconds (default: 30)
- `open_webui_retry_attempts`: Number of retry attempts for failed uploads (default: 3)

## File Extension Configuration

### Supported Extensions

The following file extensions are commonly supported:

**Text Files:**
- `md` - Markdown
- `txt` - Plain text
- `json` - JSON
- `xml` - XML
- `html` - HTML
- `css` - CSS
- `js` - JavaScript
- `py` - Python
- `java` - Java
- `cpp` - C++
- `yaml` - YAML
- `yml` - YAML

**Documents:**
- `pdf` - PDF
- `doc` - Word (old format)
- `docx` - Word
- `xls` - Excel (old format)
- `xlsx` - Excel
- `ppt` - PowerPoint (old format)
- `pptx` - PowerPoint

**Images:**
- `jpg` - JPEG
- `png` - PNG
- `gif` - GIF
- `svg` - SVG

### Custom Extensions

You can specify custom extensions:

```json
{
  "export": {
    "open_webui_attachment_extensions": "md,txt,pdf,custom1,custom2"
  }
}
```

## Metadata Configuration

### Metadata Enrichment

Metadata enrichment is enabled by default. You can configure which metadata fields to include:

```json
{
  "export": {
    "open_webui_metadata_fields": [
      "space",
      "author",
      "created",
      "updated",
      "ancestors",
      "page_name",
      "url"
    ]
  }
}
```

**Available Fields:**
- `space`: Confluence space information
- `author`: Page/attachment author
- `created`: Creation timestamp
- `updated`: Last update timestamp
- `ancestors`: Parent page hierarchy
- `page_name`: Page title
- `url`: Direct URLs to content

## Performance Configuration

### Batch Upload Settings

```json
{
  "export": {
    "open_webui_batch_add": true,
    "open_webui_batch_size": 10
  }
}
```

### Retry Configuration

```json
{
  "retry_config": {
    "backoff_and_retry": true,
    "backoff_factor": 2,
    "max_backoff_seconds": 60,
    "max_backoff_retries": 5,
    "retry_status_codes": [413, 429, 502, 503, 504]
  }
}
```

## Interactive Configuration

### Using the Configuration Menu

```bash
python -m confluence_markdown_exporter.main config
```

**Menu Navigation:**
1. Authentication → Open-WebUI
2. Export Settings → Open-WebUI Export
3. Test connections and validate settings

### Configuration Validation

The system validates configuration automatically:
- URL format validation
- API key authentication test
- Permission verification
- File extension validation

## Configuration Examples

### Minimal Configuration

```json
{
  "auth": {
    "confluence": {
      "url": "https://company.atlassian.net",
      "api_token": "your-confluence-token"
    },
    "open_webui": {
      "url": "https://openwebui.company.com",
      "api_key": "your-openwebui-key"
    }
  },
  "export": {
    "export_to_open_webui": true
  }
}
```

### Full Configuration

```json
{
  "auth": {
    "confluence": {
      "url": "https://company.atlassian.net",
      "username": "user@company.com",
      "api_token": "your-confluence-token"
    },
    "open_webui": {
      "url": "https://openwebui.company.com",
      "api_key": "your-openwebui-key"
    }
  },
  "export": {
    "output_path": "./exports",
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx,jpg,png",
    "open_webui_batch_add": true,
    "open_webui_max_file_size_mb": 25,
    "include_document_title": true,
    "page_breadcrumbs": true
  },
  "retry_config": {
    "backoff_and_retry": true,
    "backoff_factor": 2,
    "max_backoff_seconds": 120,
    "max_backoff_retries": 3
  }
}
```

## Environment-Specific Configuration

### Development Environment

```json
{
  "auth": {
    "open_webui": {
      "url": "http://localhost:8080",
      "api_key": "dev-api-key"
    }
  },
  "export": {
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt",
    "open_webui_batch_add": false
  }
}
```

### Production Environment

```json
{
  "auth": {
    "open_webui": {
      "url": "https://openwebui.company.com",
      "api_key": "${OPENWEBUI_API_KEY}"
    }
  },
  "export": {
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx",
    "open_webui_batch_add": true,
    "open_webui_max_file_size_mb": 50
  }
}
```

## Configuration Management

### Version Control

Store configuration templates in version control:

```
config/
├── app_data.json.template
├── development.json
├── staging.json
└── production.json
```

### Configuration Deployment

```bash
# Copy environment-specific config
cp config/production.json ~/.config/confluence-markdown-exporter/app_data.json

# Or use environment variable
export CME_CONFIG_PATH=/path/to/production.json
```

## Troubleshooting Configuration

### Common Issues

1. **Invalid URL Format**
   - Ensure URL includes protocol (http/https)
   - Check for typos in domain name

2. **Authentication Failures**
   - Verify API key is correct
   - Check API key permissions
   - Test with `test-connection` command

3. **File Upload Failures**
   - Check file size limits
   - Verify file extensions are allowed
   - Check Open-WebUI storage capacity

### Validation Commands

```bash
# Test connection
confluence-markdown-exporter test-connection

# Validate configuration
python -m confluence_markdown_exporter.main config --validate

# Debug mode
confluence-markdown-exporter --debug space MYSPACE ./output/
```

## Best Practices

1. **Security**: Never commit API keys to version control
2. **Environment Variables**: Use environment variables for sensitive data
3. **Validation**: Always validate configuration before production use
4. **Backup**: Keep backup copies of working configurations
5. **Documentation**: Document custom configuration choices
```

```markdown
# docs/troubleshooting.md

# Troubleshooting Guide

## Common Issues and Solutions

### Connection Issues

#### "Connection to Open-WebUI failed"

**Symptoms:**
- Cannot connect to Open-WebUI instance
- Timeout errors
- Network-related errors

**Solutions:**
1. **Check URL Format**
   ```bash
   # Correct formats
   https://openwebui.company.com
   http://localhost:8080
   
   # Incorrect formats
   openwebui.company.com  # Missing protocol
   https://openwebui.company.com/  # Trailing slash OK but not required
   ```

2. **Test Network Connectivity**
   ```bash
   # Test basic connectivity
   curl -I https://your-openwebui-instance.com
   
   # Test specific API endpoint
   curl -H "Authorization: Bearer your-api-key" https://your-openwebui-instance.com/api/v1/knowledge/
   ```

3. **Check Firewall Settings**
   - Ensure Open-WebUI port is accessible
   - Check corporate firewall rules
   - Verify VPN settings if applicable

#### "Authentication failed: Invalid API key"

**Symptoms:**
- 401 Unauthorized errors
- Authentication failures

**Solutions:**
1. **Verify API Key**
   - Check API key is correctly copied
   - Ensure no extra spaces or characters
   - Verify API key hasn't expired

2. **Check API Key Permissions**
   - Ensure API key has required permissions
   - Check user role settings in Open-WebUI
   - Verify knowledge base access rights

3. **Test API Key Manually**
   ```bash
   curl -H "Authorization: Bearer your-api-key" \
        https://your-openwebui-instance.com/api/v1/knowledge/
   ```

### Export Issues

#### "Failed to create knowledge base"

**Symptoms:**
- Knowledge base creation fails
- Permission errors during creation

**Solutions:**
1. **Check Permissions**
   - Verify API key has knowledge base creation rights
   - Check user role permissions
   - Ensure sufficient storage space

2. **Validate Knowledge Base Name**
   - Check for invalid characters in space name
   - Verify name length limits
   - Ensure name doesn't conflict with existing knowledge bases

#### "File upload failed"

**Symptoms:**
- Individual file uploads fail
- Batch upload errors
- File size or type errors

**Solutions:**
1. **Check File Size Limits**
   ```json
   {
     "export": {
       "open_webui_max_file_size_mb": 10
     }
   }
   ```

2. **Verify File Extensions**
   ```json
   {
     "export": {
       "open_webui_attachment_extensions": "md,txt,pdf,docx"
     }
   }
   ```

3. **Check Storage Capacity**
   - Verify Open-WebUI has sufficient storage
   - Check disk space on Open-WebUI server
   - Review storage quotas

#### "Some files failed to upload"

**Symptoms:**
- Partial export success
- Some files upload successfully, others fail

**Solutions:**
1. **Review Error Logs**
   - Check detailed error messages
   - Identify patterns in failures
   - Look for specific file issues

2. **Retry Failed Files**
   - Re-run export (existing files will be updated)
   - Use individual file upload mode
   - Check specific file permissions

### Performance Issues

#### "Export is very slow"

**Symptoms:**
- Long export times
- Slow progress updates
- Timeout errors

**Solutions:**
1. **Enable Batch Upload**
   ```json
   {
     "export": {
       "open_webui_batch_add": true
     }
   }
   ```

2. **Optimize File Selection**
   - Filter out large attachments
   - Limit file types
   - Use smaller batch sizes

3. **Network Optimization**
   - Use wired connection instead of Wi-Fi
   - Run during off-peak hours
   - Check network bandwidth

#### "Memory issues during export"

**Symptoms:**
- Out of memory errors
- System slowdown
- Process crashes

**Solutions:**
1. **Reduce Batch Size**
   ```json
   {
     "export": {
       "open_webui_batch_size": 5
     }
   }
   ```

2. **Export in Smaller Chunks**
   - Export individual pages instead of entire spaces
   - Use page-with-descendants for smaller sections
   - Process attachments separately

### Configuration Issues

#### "Configuration validation failed"

**Symptoms:**
- Invalid configuration errors
- Missing required fields
- Format validation failures

**Solutions:**
1. **Use Interactive Configuration**
   ```bash
   python -m confluence_markdown_exporter.main config
   ```

2. **Validate JSON Format**
   ```bash
   # Check JSON syntax
   python -c "import json; print(json.load(open('config.json')))"
   ```

3. **Check Required Fields**
   - Ensure all required fields are present
   - Verify field types and formats
   - Check for typos in field names

#### "Environment variable not found"

**Symptoms:**
- Environment variable errors
- Missing configuration values

**Solutions:**
1. **Set Environment Variables**
   ```bash
   export OPENWEBUI_URL="https://your-instance.com"
   export OPENWEBUI_API_KEY="your-api-key"
   ```

2. **Use Configuration File**
   ```bash
   export CME_CONFIG_PATH=/path/to/config.json
   ```

### Metadata Issues

#### "Metadata not appearing in Open-WebUI"

**Symptoms:**
- Files uploaded without metadata
- Missing frontmatter
- Incomplete metadata

**Solutions:**
1. **Check Metadata Configuration**
   ```json
   {
     "export": {
       "open_webui_metadata_fields": ["space", "author", "created", "updated"]
     }
   }
   ```

2. **Verify Confluence Permissions**
   - Ensure access to page metadata
   - Check author information availability
   - Verify space details access

3. **Test Metadata Extraction**
   - Check individual page exports
   - Verify metadata appears in local files
   - Test with different content types

## Diagnostic Commands

### Connection Testing

```bash
# Test Open-WebUI connection
confluence-markdown-exporter test-connection

# Test with debug output
confluence-markdown-exporter --debug test-connection
```

### Configuration Validation

```bash
# Validate configuration
python -m confluence_markdown_exporter.main config --validate

# Show current configuration
python -m confluence_markdown_exporter.main config --show
```

### Export Debugging

```bash
# Enable debug logging
confluence-markdown-exporter --debug --verbose space MYSPACE ./output/

# Test with single page
confluence-markdown-exporter --debug page 12345 ./output/
```

## Log Analysis

### Log Locations

**Default Log Locations:**
- Linux: `~/.local/share/confluence-markdown-exporter/logs/`
- macOS: `~/Library/Application Support/confluence-markdown-exporter/logs/`
- Windows: `%APPDATA%\confluence-markdown-exporter\logs\`

### Log Levels

```bash
# Set log level
export CME_LOG_LEVEL=DEBUG

# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Common Log Patterns

**Connection Issues:**
```
ERROR - OpenWebUIClient - Connection failed: [Errno 111] Connection refused
```

**Authentication Issues:**
```
ERROR - OpenWebUIClient - Authentication failed: 401 Unauthorized
```

**File Upload Issues:**
```
ERROR - OpenWebUIExporter - File upload failed: 413 Request Entity Too Large
```

## Error Codes

### Connection Errors

| Code | Description | Solution |
|------|-------------|----------|
| `CONNECTION_REFUSED` | Server refused connection | Check URL and firewall |
| `TIMEOUT` | Request timed out | Check network and server status |
| `DNS_ERROR` | Domain name resolution failed | Check URL and DNS settings |

### Authentication Errors

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_API_KEY` | API key is invalid | Verify API key |
| `EXPIRED_API_KEY` | API key has expired | Generate new API key |
| `INSUFFICIENT_PERMISSIONS` | API key lacks permissions | Check user permissions |

### Export Errors

| Code | Description | Solution |
|------|-------------|----------|
| `FILE_TOO_LARGE` | File exceeds size limit | Reduce file size or increase limit |
| `INVALID_FILE_TYPE` | File type not allowed | Check extension configuration |
| `STORAGE_FULL` | Open-WebUI storage full | Free up storage space |

## Getting Help

### Before Seeking Help

1. **Check Documentation**
   - Review configuration guide
   - Check API documentation
   - Read troubleshooting guide

2. **Enable Debug Logging**
   - Use `--debug` flag
   - Check log files
   - Note specific error messages

3. **Test Minimal Configuration**
   - Test with basic settings
   - Isolate the issue
   - Try different approaches

### Support Channels

1. **GitHub Issues**
   - Report bugs and feature requests
   - Search existing issues
   - Provide detailed reproduction steps

2. **Documentation**
   - Check online documentation
   - Review example configurations
   - Look for similar use cases

3. **Community Support**
   - Discussion forums
   - Community wiki
   - User-contributed solutions

### Information to Include

When seeking help, include:

1. **Version Information**
   ```bash
   confluence-markdown-exporter --version
   ```

2. **Configuration (sanitized)**
   - Remove sensitive information
   - Include relevant settings
   - Show error-producing configuration

3. **Error Messages**
   - Full error messages
   - Log excerpts
   - Stack traces if available

4. **Environment Details**
   - Operating system
   - Python version
   - Network configuration
   - Open-WebUI version

5. **Reproduction Steps**
   - Exact commands used
   - Expected vs actual behavior
   - Minimal reproduction case

## Recovery Procedures

### Partial Export Recovery

If an export fails partway through:

1. **Identify Successful Uploads**
   - Check export summary
   - Review log files
   - List files in knowledge base

2. **Resume Export**
   - Re-run same command
   - System will update existing files
   - Only new/failed files will be processed

3. **Manual Cleanup**
   - Remove failed/corrupted files
   - Verify file integrity
   - Check metadata completeness

### Configuration Recovery

If configuration is corrupted:

1. **Restore from Backup**
   ```bash
   cp config.json.backup ~/.config/confluence-markdown-exporter/app_data.json
   ```

2. **Rebuild Configuration**
   ```bash
   python -m confluence_markdown_exporter.main config
   ```

3. **Validate Configuration**
   ```bash
   confluence-markdown-exporter test-connection
   ```

This comprehensive troubleshooting guide should help users resolve most common issues with the Open-WebUI integration.
```

## Task 6.2: Add Examples and Templates

### Objective
Provide practical examples and templates for common use cases and configurations.

### Files to Create
- `examples/basic-export.py` (create)
- `examples/advanced-configuration.json` (create)
- `examples/ci-cd-workflow.yml` (create)
- `examples/batch-export-script.py` (create)
- `templates/custom-metadata-template.yaml` (create)

### Requirements
- Working code examples for common scenarios
- Configuration templates for different environments
- CI/CD integration examples
- Custom metadata templates
- Batch processing examples

### Reference Implementation

```python
# examples/basic-export.py

"""
Basic Open-WebUI Export Example

This example demonstrates how to export a Confluence space to Open-WebUI
using the Python API directly.
"""

import logging
from pathlib import Path
from confluence_markdown_exporter.config.config_manager import ConfigManager
from confluence_markdown_exporter.clients.confluence_client import ConfluenceClient
from confluence_markdown_exporter.clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.processors.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.processors.metadata_enricher import MetadataEnricher
from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main export function"""
    
    # Configuration
    CONFLUENCE_URL = "https://your-company.atlassian.net"
    CONFLUENCE_TOKEN = "your-confluence-token"
    OPENWEBUI_URL = "https://your-openwebui-instance.com"
    OPENWEBUI_API_KEY = "your-openwebui-api-key"
    SPACE_KEY = "MYSPACE"
    OUTPUT_PATH = "./exports"
    
    try:
        # Initialize clients
        logger.info("Initializing clients...")
        
        # Confluence client
        confluence_client = ConfluenceClient(
            base_url=CONFLUENCE_URL,
            api_token=CONFLUENCE_TOKEN
        )
        
        # Open-WebUI client
        open_webui_client = OpenWebUIClient(
            base_url=OPENWEBUI_URL,
            api_key=OPENWEBUI_API_KEY
        )
        
        # Test connections
        logger.info("Testing connections...")
        
        if not confluence_client.test_connection():
            logger.error("Failed to connect to Confluence")
            return False
        
        if not open_webui_client.test_connection():
            logger.error("Failed to connect to Open-WebUI")
            return False
        
        # Initialize processors
        logger.info("Initializing processors...")
        
        attachment_filter = AttachmentFilter(
            allowed_extensions="md,txt,pdf,docx,xlsx"
        )
        
        metadata_enricher = MetadataEnricher()
        
        # Initialize exporter
        exporter = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=True
        )
        
        # Get space content
        logger.info(f"Retrieving space content for {SPACE_KEY}...")
        
        # This would use your existing logic to get pages and attachments
        pages = get_space_pages(confluence_client, SPACE_KEY)
        attachments = get_space_attachments(confluence_client, SPACE_KEY)
        
        logger.info(f"Found {len(pages)} pages and {len(attachments)} attachments")
        
        # Export to Open-WebUI
        logger.info("Starting export to Open-WebUI...")
        
        summary = exporter.export_space(
            space_key=SPACE_KEY,
            output_path=OUTPUT_PATH,
            pages=pages,
            attachments=attachments
        )
        
        # Print summary
        logger.info("Export completed!")
        logger.info(summary.get_summary_text())
        
        return summary.success_rate > 90  # Consider successful if >90% uploaded
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False

def get_space_pages(confluence_client, space_key):
    """Get all pages in a space"""
    # Placeholder - implement based on your existing logic
    return []

def get_space_attachments(confluence_client, space_key):
    """Get all attachments in a space"""
    # Placeholder - implement based on your existing logic
    return []

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

```json
// examples/advanced-configuration.json

{
  "auth": {
    "confluence": {
      "url": "https://company.atlassian.net",
      "username": "exporter@company.com",
      "api_token": "${CONFLUENCE_API_TOKEN}"
    },
    "open_webui": {
      "url": "https://openwebui.company.com",
      "api_key": "${OPENWEBUI_API_KEY}"
    }
  },
  "export": {
    "output_path": "./exports",
    "page_href": "absolute",
    "attachment_href": "absolute",
    "page_breadcrumbs": true,
    "include_document_title": true,
    "export_to_open_webui": true,
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx,jpg,png,gif,svg",
    "open_webui_batch_add": true,
    "open_webui_max_file_size_mb": 25,
    "open_webui_timeout_seconds": 300,
    "open_webui_metadata_fields": [
      "space",
      "author", 
      "created",
      "updated",
      "ancestors",
      "page_name",
      "url",
      "labels",
      "version"
    ]
  },
  "retry_config": {
    "backoff_and_retry": true,
    "backoff_factor": 2,
    "max_backoff_seconds": 120,
    "max_backoff_retries": 5,
    "retry_status_codes": [413, 429, 500, 502, 503, 504]
  },
  "logging": {
    "level": "INFO",
    "file": "./logs/export.log",
    "max_file_size_mb": 10,
    "backup_count": 5
  }
}
```

```yaml
# examples/ci-cd-workflow.yml

name: Confluence to Open-WebUI Export

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      space_key:
        description: 'Confluence space key to export'
        required: true
        default: 'DOCS'
      force_full_export:
        description: 'Force full export (ignore incremental)'
        required: false
        default: 'false'
        type: boolean

jobs:
  export:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install confluence-markdown-exporter
      
      - name: Setup configuration
        run: |
          mkdir -p ~/.config/confluence-markdown-exporter
          cat > ~/.config/confluence-markdown-exporter/app_data.json << 'EOF'
          {
            "auth": {
              "confluence": {
                "url": "${{ secrets.CONFLUENCE_URL }}",
                "username": "${{ secrets.CONFLUENCE_USERNAME }}",
                "api_token": "${{ secrets.CONFLUENCE_API_TOKEN }}"
              },
              "open_webui": {
                "url": "${{ secrets.OPENWEBUI_URL }}",
                "api_key": "${{ secrets.OPENWEBUI_API_KEY }}"
              }
            },
            "export": {
              "export_to_open_webui": true,
              "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx",
              "open_webui_batch_add": true
            }
          }
          EOF
      
      - name: Test connections
        run: |
          confluence-markdown-exporter test-connection
      
      - name: Export spaces
        run: |
          # Export multiple spaces
          spaces=("DOCS" "ENGINEERING" "PRODUCT")
          
          for space in "${spaces[@]}"; do
            echo "Exporting space: $space"
            confluence-markdown-exporter space "$space" "./exports/$space/"
            
            if [ $? -eq 0 ]; then
              echo "✓ Successfully exported $space"
            else
              echo "✗ Failed to export $space"
              exit 1
            fi
          done
      
      - name: Upload export logs
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: export-logs
          path: |
            ./exports/
            ~/.local/share/confluence-markdown-exporter/logs/
          retention-days: 30
      
      - name: Notify on failure
        if: failure()
        run: |
          # Send notification (customize as needed)
          echo "Export failed - check logs for details"
          # curl -X POST -H 'Content-type: application/json' \
          #   --data '{"text":"Confluence export failed"}' \
          #   ${{ secrets.SLACK_WEBHOOK_URL }}

  cleanup:
    runs-on: ubuntu-latest
    needs: export
    if: always()
    
    steps:
      - name: Cleanup old exports
        run: |
          # Cleanup logic for old exports
          echo "Cleaning up old exports..."
          # Add your cleanup logic here
```

```python
# examples/batch-export-script.py

"""
Batch Export Script for Multiple Spaces

This script demonstrates how to export multiple Confluence spaces
to Open-WebUI with proper error handling and progress tracking.
"""

import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from confluence_markdown_exporter.config.config_manager import ConfigManager
from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.utils.progress_reporter import ProgressReporter
from confluence_markdown_exporter.utils.open_webui_logger import OpenWebUILogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchExporter:
    """Batch exporter for multiple Confluence spaces"""
    
    def __init__(self, config_path: str = None):
        """Initialize batch exporter"""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.results = []
        
        # Initialize Open-WebUI logger
        self.open_webui_logger = OpenWebUILogger("batch_export")
        
        # Initialize progress reporter
        self.progress_reporter = ProgressReporter(
            logger=self.open_webui_logger,
            progress_callback=self._progress_callback
        )
    
    def export_spaces(self, spaces: List[str], output_base_path: str) -> Dict[str, Any]:
        """Export multiple spaces
        
        Args:
            spaces: List of space keys to export
            output_base_path: Base output path
            
        Returns:
            Dictionary with export results
        """
        start_time = datetime.now()
        
        logger.info(f"Starting batch export of {len(spaces)} spaces")
        self.progress_reporter.start_operation_batch("space_export", len(spaces))
        
        results = {
            "start_time": start_time.isoformat(),
            "spaces": {},
            "summary": {
                "total_spaces": len(spaces),
                "successful_spaces": 0,
                "failed_spaces": 0,
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0
            }
        }
        
        # Export each space
        for i, space_key in enumerate(spaces, 1):
            try:
                logger.info(f"Exporting space {i}/{len(spaces)}: {space_key}")
                self.progress_reporter.report_item_start(space_key, i)
                
                # Create output directory
                output_path = Path(output_base_path) / space_key
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Export space
                space_result = self._export_single_space(space_key, str(output_path))
                
                if space_result["success"]:
                    self.progress_reporter.report_item_success(space_key, "Export completed")
                    results["summary"]["successful_spaces"] += 1
                else:
                    self.progress_reporter.report_item_failure(space_key, space_result["error"])
                    results["summary"]["failed_spaces"] += 1
                
                # Update totals
                results["summary"]["total_files"] += space_result["total_files"]
                results["summary"]["successful_files"] += space_result["successful_files"]
                results["summary"]["failed_files"] += space_result["failed_files"]
                
                # Store space result
                results["spaces"][space_key] = space_result
                
            except Exception as e:
                logger.error(f"Unexpected error exporting space {space_key}: {e}")
                self.progress_reporter.report_item_failure(space_key, str(e))
                results["summary"]["failed_spaces"] += 1
                results["spaces"][space_key] = {
                    "success": False,
                    "error": str(e),
                    "total_files": 0,
                    "successful_files": 0,
                    "failed_files": 0
                }
        
        # Complete batch operation
        self.progress_reporter.report_batch_complete()
        
        end_time = datetime.now()
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # Calculate success rate
        if results["summary"]["total_spaces"] > 0:
            results["summary"]["space_success_rate"] = (
                results["summary"]["successful_spaces"] / 
                results["summary"]["total_spaces"] * 100
            )
        
        if results["summary"]["total_files"] > 0:
            results["summary"]["file_success_rate"] = (
                results["summary"]["successful_files"] / 
                results["summary"]["total_files"] * 100
            )
        
        # Log final summary
        self._log_final_summary(results)
        
        return results
    
    def _export_single_space(self, space_key: str, output_path: str) -> Dict[str, Any]:
        """Export a single space"""
        try:
            # Initialize exporter (you would implement this based on your setup)
            exporter = self._get_exporter()
            
            # Get space content
            pages = self._get_space_pages(space_key)
            attachments = self._get_space_attachments(space_key)
            
            # Export
            summary = exporter.export_space(space_key, output_path, pages, attachments)
            
            return {
                "success": summary.success_rate > 90,  # Consider >90% as success
                "total_files": summary.total_files,
                "successful_files": summary.total_successful,
                "failed_files": summary.total_failed,
                "success_rate": summary.success_rate,
                "duration_seconds": summary.duration,
                "knowledge_base_id": summary.knowledge_base_id,
                "errors": summary.errors
            }
            
        except Exception as e:
            logger.error(f"Error exporting space {space_key}: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0
            }
    
    def _get_exporter(self) -> OpenWebUIExporter:
        """Get configured exporter"""
        # Implement based on your configuration
        pass
    
    def _get_space_pages(self, space_key: str) -> List[Dict[str, Any]]:
        """Get pages for space"""
        # Implement based on your existing logic
        return []
    
    def _get_space_attachments(self, space_key: str) -> List[Dict[str, Any]]:
        """Get attachments for space"""
        # Implement based on your existing logic
        return []
    
    def _progress_callback(self, status):
        """Progress callback for reporting"""
        message = self.progress_reporter.format_progress_message(status)
        logger.info(message)
    
    def _log_final_summary(self, results: Dict[str, Any]):
        """Log final summary"""
        summary = results["summary"]
        
        logger.info("=== Batch Export Summary ===")
        logger.info(f"Total spaces: {summary['total_spaces']}")
        logger.info(f"Successful spaces: {summary['successful_spaces']}")
        logger.info(f"Failed spaces: {summary['failed_spaces']}")
        logger.info(f"Space success rate: {summary.get('space_success_rate', 0):.1f}%")
        logger.info(f"Total files: {summary['total_files']}")
        logger.info(f"Successful files: {summary['successful_files']}")
        logger.info(f"Failed files: {summary['failed_files']}")
        logger.info(f"File success rate: {summary.get('file_success_rate', 0):.1f}%")
        logger.info(f"Duration: {results['duration_seconds']:.2f} seconds")
        
        # Log failed spaces
        failed_spaces = [
            space for space, result in results["spaces"].items() 
            if not result["success"]
        ]
        
        if failed_spaces:
            logger.warning(f"Failed spaces: {', '.join(failed_spaces)}")
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save results to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    """Main function"""
    # Configuration
    spaces_to_export = [
        "DOCS",
        "ENGINEERING", 
        "PRODUCT",
        "MARKETING"
    ]
    
    output_base_path = "./batch_exports"
    results_file = f"batch_export_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Create output directory
    Path(output_base_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize and run batch exporter
    try:
        batch_exporter = BatchExporter()
        results = batch_exporter.export_spaces(spaces_to_export, output_base_path)
        
        # Save results
        batch_exporter.save_results(results, results_file)
        
        # Exit with appropriate code
        success_rate = results["summary"].get("space_success_rate", 0)
        exit(0 if success_rate > 90 else 1)
        
    except Exception as e:
        logger.error(f"Batch export failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
```

## Deliverables

1. **Updated Documentation** 
   - Enhanced README with Open-WebUI integration guide
   - Comprehensive configuration documentation
   - Detailed troubleshooting guide
   - Updated changelog

2. **Practical Examples**
   - Basic export script
   - Advanced configuration templates
   - CI/CD workflow examples
   - Batch processing scripts

3. **Templates and Guides**
   - Environment-specific configurations
   - Custom metadata templates
   - Integration examples
   - Best practices documentation

## Success Criteria

- [ ] Documentation is comprehensive and easy to follow
- [ ] Examples work out-of-the-box with minimal configuration
- [ ] Configuration templates cover common use cases
- [ ] Troubleshooting guide addresses common issues
- [ ] CI/CD examples are production-ready
- [ ] All code examples are tested and functional
- [ ] Documentation includes security best practices
- [ ] Migration guides help users upgrade smoothly
- [ ] Performance optimization tips are included
- [ ] Community contribution guidelines are clear
