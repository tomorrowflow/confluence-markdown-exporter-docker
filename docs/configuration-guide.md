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
    "open_webui_attachment_extensions": "md,txt,pdf,docx,xlsx,pptx,jpg,png,gif,svg",
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
