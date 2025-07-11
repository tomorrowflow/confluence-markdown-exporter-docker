# Open-WebUI Integration - Main Implementation Prompt

## Project Overview

You are implementing Open-WebUI knowledge base integration for the confluence-markdown-exporter project. This integration allows users to export Confluence content directly to Open-WebUI knowledge bases with enriched metadata and intelligent file filtering.

## Repository Context

This is a Python package that exports Confluence pages to Markdown format. You're extending it to also export to Open-WebUI knowledge bases.

## Implementation Strategy

This implementation is divided into 7 phases, each building upon the previous ones:

1. **Phase 1**: Configuration Extension (3-5 days)
2. **Phase 2**: Open-WebUI API Client (5-7 days)  
3. **Phase 3**: Metadata Enrichment (4-6 days)
4. **Phase 4**: File Processing and Export Logic (6-8 days)
5. **Phase 5**: Error Handling and Logging (3-4 days)
6. **Phase 6**: Documentation and Final Integration (4-5 days)
7. **Phase 7**: Testing and Quality Assurance (5-7 days)

## Execution Instructions

1. **Start with Phase 1** and complete each phase sequentially
2. **Each phase has dependencies** on previous phases - do not skip ahead
3. **Test thoroughly** after each phase before proceeding
4. **Maintain backward compatibility** with existing functionality
5. **Follow existing code conventions** in the repository

## Key Integration Points

### Configuration System
- Extend existing JSON-based configuration
- Add Open-WebUI authentication (URL, API key)
- Add export control settings (file extensions, batch mode)
- Maintain backward compatibility

### Export Workflow
- Integrate with existing markdown export pipeline
- Add conditional Open-WebUI export after markdown generation
- Preserve existing CLI commands and functionality
- Add new CLI commands for Open-WebUI specific operations

### File Structure Extensions
```
confluence_markdown_exporter/
├── clients/
│   └── open_webui_client.py          # New: Open-WebUI API client
├── config/
│   ├── config_schema.py              # Extend: Add Open-WebUI fields
│   └── config_manager.py             # Extend: Add menu options
├── processors/
│   ├── attachment_filter.py          # New: File filtering
│   └── metadata_enricher.py          # New: Metadata enrichment
├── exporters/
│   └── open_webui_exporter.py        # New: Main export logic
├── models/
│   └── open_webui_models.py          # New: API response models
├── utils/
│   ├── open_webui_logger.py          # New: Structured logging
│   └── progress_reporter.py          # New: Progress tracking
└── validators/
    ├── open_webui_validator.py       # New: Connection validation
    └── export_validator.py           # New: Export validation
```

## Expected Functionality

### Configuration
```bash
# Interactive configuration
python -m confluence_markdown_exporter.main config
# Navigate to: Authentication > Open-WebUI
# Navigate to: Export Settings > Open-WebUI Export
```

### Export Operations
```bash
# Export space with Open-WebUI integration
confluence-markdown-exporter space MYSPACE ./output/

# Test Open-WebUI connection
confluence-markdown-exporter test-connection
```

### Knowledge Base Features
- **Automatic Creation**: Knowledge bases named after Confluence spaces
- **Metadata Enrichment**: Comprehensive frontmatter with Confluence metadata
- **File Filtering**: Configurable file extension filtering
- **Batch Processing**: Efficient bulk uploads
- **Progress Tracking**: Real-time status updates
- **Error Recovery**: Graceful failure handling

## Quality Standards

- **Test Coverage**: Aim for >90% coverage on new code
- **Error Handling**: Comprehensive error messages with actionable solutions
- **Performance**: Single page export <5s, batch operations >10 files/s
- **Documentation**: Every new function needs docstrings
- **Backward Compatibility**: Existing functionality must continue working

## Next Steps

1. **Clone the repository** and explore the existing codebase
2. **Set up development environment** with existing venv and dependencies
3. **Execute Phase 1** using the provided prompt
4. **Proceed sequentially** through each phase
5. **Test thoroughly** at each stage

## Support Resources

- **Repository**: https://github.com/tomorrowflow/confluence-markdown-exporter-docker
- **Open-WebUI API**: Reference the provided OpenAPI specification
- **Confluence API**: Reference the provided OpenAPI specification
- **Implementation Guide**: Use the detailed phase implementations as reference

## Success Criteria

✅ All existing functionality continues to work  
✅ New Open-WebUI export functionality works as specified  
✅ Configuration system is extended properly  
✅ Error handling is comprehensive  
✅ Performance meets specified benchmarks  
✅ Documentation is complete and accurate  
✅ Test coverage exceeds 90%  

Begin with Phase 1 when ready to start implementation.
