"""Basic Open-WebUI Export Example

This example demonstrates how to export a Confluence space to Open-WebUI
using the Python API directly.
"""

import logging
from pathlib import Path

from confluence_markdown_exporter.clients.confluence_client import ConfluenceClient
from confluence_markdown_exporter.clients.open_webui_client import OpenWebUIClient
from confluence_markdown_exporter.config.config_manager import ConfigManager
from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.processors.attachment_filter import AttachmentFilter
from confluence_markdown_exporter.processors.metadata_enricher import MetadataEnricher

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
        confluence_client = ConfluenceClient(base_url=CONFLUENCE_URL, api_token=CONFLUENCE_TOKEN)

        # Open-WebUI client
        open_webui_client = OpenWebUIClient(base_url=OPENWEBUI_URL, api_key=OPENWEBUI_API_KEY)

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

        attachment_filter = AttachmentFilter(allowed_extensions="md,txt,pdf,docx,xlsx")

        metadata_enricher = MetadataEnricher()

        # Initialize exporter
        exporter = OpenWebUIExporter(
            open_webui_client=open_webui_client,
            confluence_client=confluence_client,
            attachment_filter=attachment_filter,
            metadata_enricher=metadata_enricher,
            use_batch_upload=True,
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
            space_key=SPACE_KEY, output_path=OUTPUT_PATH, pages=pages, attachments=attachments
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
