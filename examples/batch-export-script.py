"""Batch Export Script for Multiple Spaces

This script demonstrates how to export multiple Confluence spaces
to Open-WebUI with proper error handling and progress tracking.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from confluence_markdown_exporter.config.config_manager import ConfigManager
from confluence_markdown_exporter.exporters.open_webui_exporter import OpenWebUIExporter
from confluence_markdown_exporter.utils.open_webui_logger import OpenWebUILogger
from confluence_markdown_exporter.utils.progress_reporter import ProgressReporter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            logger=self.open_webui_logger, progress_callback=self._progress_callback
        )

    def export_spaces(self, spaces: list[str], output_base_path: str) -> dict[str, Any]:
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
                "failed_files": 0,
            },
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
                    "failed_files": 0,
                }

        # Complete batch operation
        self.progress_reporter.report_batch_complete()

        end_time = datetime.now()
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = (end_time - start_time).total_seconds()

        # Calculate success rate
        if results["summary"]["total_spaces"] > 0:
            results["summary"]["space_success_rate"] = (
                results["summary"]["successful_spaces"] / results["summary"]["total_spaces"] * 100
            )

        if results["summary"]["total_files"] > 0:
            results["summary"]["file_success_rate"] = (
                results["summary"]["successful_files"] / results["summary"]["total_files"] * 100
            )

        # Log final summary
        self._log_final_summary(results)

        return results

    def _export_single_space(self, space_key: str, output_path: str) -> dict[str, Any]:
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
                "errors": summary.errors,
            }

        except Exception as e:
            logger.error(f"Error exporting space {space_key}: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
            }

    def _get_exporter(self) -> OpenWebUIExporter:
        """Get configured exporter"""
        # Implement based on your configuration

    def _get_space_pages(self, space_key: str) -> list[dict[str, Any]]:
        """Get pages for space"""
        # Implement based on your existing logic
        return []

    def _get_space_attachments(self, space_key: str) -> list[dict[str, Any]]:
        """Get attachments for space"""
        # Implement based on your existing logic
        return []

    def _progress_callback(self, status):
        """Progress callback for reporting"""
        message = self.progress_reporter.format_progress_message(status)
        logger.info(message)

    def _log_final_summary(self, results: dict[str, Any]):
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
            space for space, result in results["spaces"].items() if not result["success"]
        ]

        if failed_spaces:
            logger.warning(f"Failed spaces: {', '.join(failed_spaces)}")

    def save_results(self, results: dict[str, Any], output_file: str):
        """Save results to file"""
        try:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


def main():
    """Main function"""
    # Configuration
    spaces_to_export = ["DOCS", "ENGINEERING", "PRODUCT", "MARKETING"]

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
