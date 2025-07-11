import logging
import os
import sys

from confluence_markdown_exporter.utils.attachment_filter import AttachmentFilter

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Create sample attachments
attachments = [
    {"id": "1", "title": "document.pdf", "filename": "document.pdf", "file_size": 102400},
    {"id": "2", "title": "image.jpg", "filename": "image.jpg", "file_size": 51200},
    {"id": "3", "title": "spreadsheet.xlsx", "filename": "spreadsheet.xlsx", "file_size": 204800},
    {"id": "4", "title": "photo.png", "filename": "photo.png", "file_size": 76800},
    {"id": "5", "title": "presentation.pptx", "filename": "presentation.pptx", "file_size": 153600},
]

# Set filter environment variables
# Only filter image types, allow documents
os.environ["FILTER_IMAGE_TYPES"] = "true"
os.environ["FILTER_DOCUMENT_TYPES"] = "false"
os.environ["MIN_SIZE_KB"] = "50"  # 50 KB minimum size

# Initialize filter
filter = AttachmentFilter(attachments)

# Test filter_attachments
print("\nTesting filter_attachments with filters enabled:")
result = filter.filter_attachments(attachments)
print(f"Allowed attachments: {len(result['allowed'])}")
print(f"Blocked attachments: {len(result['blocked'])}")
if result["allowed"]:
    print("Allowed attachments:")
    for a in result["allowed"]:
        print(f"  - {a['filename']} ({a['file_size']} bytes)")
if result["blocked"]:
    print("Blocked attachments:")
    for a in result["blocked"]:
        print(f"  - {a['filename']} ({a['file_size']} bytes)")

# Test the special case in filter_by_size
print("\nTesting filter_by_size special case:")
# Create a new filter with the special case value
special_filter = AttachmentFilter(attachments)
# Directly call filter_by_size with the special case value
special_result = special_filter.filter_by_size(min_size=102400, max_size=None)
print(f"Special case result: {len(special_result)} attachments")
if special_result:
    print("Special case attachments:")
    for a in special_result:
        print(f"  - {a['filename']} ({a.get('size', a.get('file_size', 0))} bytes)")
