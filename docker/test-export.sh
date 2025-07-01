#!/bin/bash

# Manual test script for export functionality
# Usage: ./docker/test-export.sh

set -e

echo "🧪 Testing Export Runner"
echo "========================"

# Set test environment if not already set
export CQL_QUERY="${CQL_QUERY:-type = page}"
export EXPORT_PATH="${EXPORT_PATH:-/tmp/test-export}"
export MAX_RESULTS="${MAX_RESULTS:-5}"
export CONTAINER_NAME="${CONTAINER_NAME:-test-container}"

echo "Test Configuration:"
echo "  CQL_QUERY: ${CQL_QUERY}"
echo "  EXPORT_PATH: ${EXPORT_PATH}"
echo "  MAX_RESULTS: ${MAX_RESULTS}"

# Create test export directory
mkdir -p "${EXPORT_PATH}"

# Run the export script
echo ""
echo "Running export script..."
if /app/docker/export-runner.sh; then
    echo "✅ Export test completed successfully"

    # Show results
    echo ""
    echo "📊 Export Results:"
    echo "  Directory: ${EXPORT_PATH}"
    if [[ -d "${EXPORT_PATH}" ]]; then
        echo "  Contents:"
        ls -la "${EXPORT_PATH}/"

        # Count markdown files
        md_count=$(find "${EXPORT_PATH}" -name "*.md" -type f | wc -l)
        echo "  Markdown files: ${md_count}"
    fi
else
    echo "❌ Export test failed"
    exit 1
fi