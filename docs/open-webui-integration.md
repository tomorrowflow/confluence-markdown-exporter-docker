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
