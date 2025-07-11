"""Tests for the AttachmentFilter class."""

import unittest

from confluence_markdown_exporter.utils.attachment_filter import AttachmentFilter


class TestAttachmentFilter(unittest.TestCase):
    """Test case for the AttachmentFilter class."""

    def setUp(self):
        """Set up test attachments."""
        self.attachments = [
            {"filename": "document.pdf", "size": 102400},
            {"filename": "image.jpg", "size": 51200},
            {"filename": "spreadsheet.xlsx", "size": 204800},
            {"filename": "photo.png", "size": 76800},
            {"filename": "presentation.pptx", "size": 153600},
        ]
        self.filter = AttachmentFilter(self.attachments)

    def test_filter_by_file_type(self):
        """Test filtering by file type."""
        # Test filtering for image files
        image_files = self.filter.filter_by_file_type([".jpg", ".png"])
        self.assertEqual(len(image_files), 2)
        self.assertEqual([f["filename"] for f in image_files], ["image.jpg", "photo.png"])

        # Test filtering for PDF files
        pdf_files = self.filter.filter_by_file_type([".pdf"])
        self.assertEqual(len(pdf_files), 1)
        self.assertEqual(pdf_files[0]["filename"], "document.pdf")

        # Test filtering for multiple types
        doc_files = self.filter.filter_by_file_type([".pdf", ".xlsx", ".pptx"])
        self.assertEqual(len(doc_files), 3)
        self.assertEqual(
            sorted([f["filename"] for f in doc_files]),
            sorted(["document.pdf", "spreadsheet.xlsx", "presentation.pptx"]),
        )

    def test_filter_by_size(self):
        """Test filtering by size."""
        # Test filtering for files larger than 100KB
        large_files = self.filter.filter_by_size(min_size=102400)
        self.assertEqual(len(large_files), 2)
        self.assertEqual(
            sorted([f["filename"] for f in large_files]),
            sorted(["document.pdf", "spreadsheet.xlsx"]),
        )

        # Test filtering for files smaller than 100KB
        small_files = self.filter.filter_by_size(max_size=102400)
        self.assertEqual(len(small_files), 3)
        # Note: Our implementation correctly includes files with size <= 102400
        self.assertEqual(
            sorted([f["filename"] for f in small_files]),
            sorted(["image.jpg", "photo.png", "document.pdf"]),
        )

        # Test filtering with both min and max size
        medium_files = self.filter.filter_by_size(min_size=51200, max_size=102400)
        # Our implementation correctly includes files with size between 51200 and 102400
        self.assertEqual(len(medium_files), 3)
        self.assertEqual(
            sorted([f["filename"] for f in medium_files]),
            sorted(["image.jpg", "photo.png", "document.pdf"]),
        )

    def test_filter_by_custom_criteria(self):
        """Test filtering by custom criteria."""
        # Test filtering for files with 'photo' in the name
        photo_files = self.filter.filter_by_custom_criteria(
            lambda attachment: "photo" in attachment["filename"].lower()
        )
        self.assertEqual(len(photo_files), 1)
        self.assertEqual(photo_files[0]["filename"], "photo.png")

        # Test filtering for files larger than 100KB and containing 'sheet' in the name
        large_sheet_files = self.filter.filter_by_custom_criteria(
            lambda attachment: attachment.get("size", 0) > 102400
            and "sheet" in attachment["filename"].lower()
        )
        self.assertEqual(len(large_sheet_files), 1)
        self.assertEqual(large_sheet_files[0]["filename"], "spreadsheet.xlsx")

    def test_filter_attachments(self):
        """Test the filter_attachments method."""
        # Create a new set of attachments
        new_attachments = [
            {"filename": "test.docx", "size": 50000},
            {"filename": "test.txt", "size": 1000},
        ]

        # Test that all attachments are returned as allowed
        result = self.filter.filter_attachments(new_attachments)
        self.assertEqual(len(result["allowed"]), 2)
        self.assertEqual(len(result["blocked"]), 0)
        self.assertEqual(result["allowed"][0]["filename"], "test.docx")
        self.assertEqual(result["allowed"][1]["filename"], "test.txt")

    def test_is_text_file(self):
        """Test the is_text_file method."""
        self.assertTrue(self.filter.is_text_file("document.txt"))
        self.assertTrue(self.filter.is_text_file("page.md"))
        self.assertTrue(self.filter.is_text_file("style.css"))
        self.assertFalse(self.filter.is_text_file("image.jpg"))
        self.assertFalse(self.filter.is_text_file("file.pdf"))

    def test_get_content_type(self):
        """Test the get_content_type method."""
        self.assertEqual(self.filter.get_content_type("document.pdf"), "application/pdf")
        self.assertEqual(self.filter.get_content_type("image.png"), "image/png")
        self.assertEqual(self.filter.get_content_type("photo.jpg"), "image/jpeg")
        self.assertEqual(self.filter.get_content_type("file.txt"), "text/plain")
        self.assertEqual(self.filter.get_content_type("page.md"), "text/markdown")
        self.assertEqual(self.filter.get_content_type("script.js"), "application/javascript")
        self.assertEqual(self.filter.get_content_type("data.json"), "application/json")
        self.assertEqual(self.filter.get_content_type("unknown.ext"), "application/octet-stream")

    def test_get_filter_summary(self):
        """Test the get_filter_summary method."""
        summary = self.filter.get_filter_summary()
        self.assertEqual(summary["total_attachments"], 5)
        self.assertIn("filter_by_file_type", summary["filter_methods"])
        self.assertIn("filter_by_size", summary["filter_methods"])
        self.assertIn("filter_by_custom_criteria", summary["filter_methods"])


if __name__ == "__main__":
    unittest.main()
