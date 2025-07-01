#!/bin/bash

# Confluence Markdown Exporter - Cron Export Runner
# This script is executed by cron to perform scheduled exports

set -e

# Logging function with timestamp
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}"
}

# Function to log to both stdout and export log file
export_log() {
    local level=$1
    shift
    local message="$*"

    # Log to stdout (will be captured by syslog via cron)
    log "$level" "$message"

    # Also log to dedicated export log file
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" >> /var/log/confluence-exporter/export.log
}

# Start export process
start_export() {
    export_log "INFO" "🚀 Starting scheduled Confluence export"
    export_log "INFO" "Container: ${CONTAINER_NAME:-unknown}"
    export_log "INFO" "PID: $$"

    # Log configuration
    export_log "INFO" "Export Configuration:"
    export_log "INFO" "  CQL Query: ${CQL_QUERY}"
    export_log "INFO" "  Export Path: ${EXPORT_PATH}"
    export_log "INFO" "  Max Results: ${MAX_RESULTS}"
    export_log "INFO" "  Confluence URL: ${CONFLUENCE_URL}"

    # Create timestamped export directory
    local export_timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local timestamped_export_path="${EXPORT_PATH}/${export_timestamp}"

    export_log "INFO" "Creating export directory: ${timestamped_export_path}"
    mkdir -p "${timestamped_export_path}"
}

# Perform the actual export
perform_export() {
    local export_timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local timestamped_export_path="${EXPORT_PATH}/${export_timestamp}"
    local temp_log="/tmp/confluence-export-${export_timestamp}.log"

    export_log "INFO" "📄 Starting confluence-markdown-exporter..."
    export_log "DEBUG" "Command: confluence-markdown-exporter search \"${CQL_QUERY}\" \"${timestamped_export_path}\" --limit ${MAX_RESULTS}"

    # Record start time
    local start_time=$(date +%s)

    # Run the export with detailed logging
    if confluence-markdown-exporter search "${CQL_QUERY}" "${timestamped_export_path}" --limit "${MAX_RESULTS}" > "${temp_log}" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        export_log "INFO" "✅ Export completed successfully in ${duration} seconds"

        # Count exported files
        local file_count=$(find "${timestamped_export_path}" -name "*.md" -type f | wc -l)
        local total_size=$(du -sh "${timestamped_export_path}" 2>/dev/null | cut -f1 || echo "unknown")

        export_log "INFO" "Export Results:"
        export_log "INFO" "  Files exported: ${file_count}"
        export_log "INFO" "  Total size: ${total_size}"
        export_log "INFO" "  Export directory: ${timestamped_export_path}"

        # Log the confluence-markdown-exporter output
        export_log "DEBUG" "Confluence exporter output:"
        while IFS= read -r line; do
            export_log "DEBUG" "  $line"
        done < "${temp_log}"

        # Create symlink to latest export
        local latest_link="${EXPORT_PATH}/latest"
        if [[ -L "${latest_link}" ]]; then
            rm "${latest_link}"
        fi

        cd ${EXPORT_PATH}
        ln -s "${export_timestamp}" "${latest_link}"
        export_log "INFO" "✅ Latest export symlink updated: ${latest_link}"
        cd -

        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        export_log "ERROR" "❌ Export failed after ${duration} seconds"
        export_log "ERROR" "Confluence exporter error output:"
        while IFS= read -r line; do
            export_log "ERROR" "  $line"
        done < "${temp_log}"

        # Clean up failed export directory
        if [[ -d "${timestamped_export_path}" ]]; then
            rm -rf "${timestamped_export_path}"
            export_log "INFO" "Cleaned up failed export directory"
        fi

        return 1
    fi

    # Clean up temp log
    rm -f "${temp_log}"
}

# Main execution with error handling
main() {
    # Ensure required environment variables are available
    if [[ -z "${CQL_QUERY}" || -z "${EXPORT_PATH}" || -z "${MAX_RESULTS}" ]]; then
        export_log "ERROR" "Missing required environment variables"
        export_log "ERROR" "Required: CQL_QUERY, EXPORT_PATH, MAX_RESULTS"
        exit 1
    fi

    # Ensure export directory exists
    if [[ ! -d "${EXPORT_PATH}" ]]; then
        export_log "ERROR" "Export directory does not exist: ${EXPORT_PATH}"
        exit 1
    fi

    # Check if confluence-markdown-exporter is available
    if ! command -v confluence-markdown-exporter &> /dev/null; then
        export_log "ERROR" "confluence-markdown-exporter command not found"
        exit 1
    fi

    start_export

    if perform_export; then
        export_log "INFO" "🎉 Scheduled export completed successfully"
        exit 0
    else
        export_log "ERROR" "💥 Scheduled export failed"
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"