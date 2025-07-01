#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp and color
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        ERROR)   echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" ;;
        WARN)    echo -e "${YELLOW}[${timestamp}] WARN:  ${message}${NC}" ;;
        INFO)    echo -e "${GREEN}[${timestamp}] INFO:  ${message}${NC}" ;;
        DEBUG)   echo -e "${BLUE}[${timestamp}] DEBUG: ${message}${NC}" ;;
        *)       echo -e "[${timestamp}] ${message}" ;;
    esac
}

log INFO "🐳 Starting Confluence Markdown Exporter Docker Container"
log INFO "Phase B: Environment Configuration"
echo "=================================================="

# Set defaults for optional variables
export EXPORT_PATH=${EXPORT_PATH:-"/app/exports"}
export MAX_RESULTS=${MAX_RESULTS:-"100"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
export CONTAINER_NAME=${CONTAINER_NAME:-"confluence-exporter"}
export CRON_SCHEDULE=${CRON_SCHEDULE:-"0 2 * * *"}
export CQL_QUERY=${CQL_QUERY:-"type = page"}

log INFO "Container: ${CONTAINER_NAME}"
log INFO "Log Level: ${LOG_LEVEL}"

# Validate required environment variables
validate_env() {
    local missing_vars=""
    local has_missing=false

    if [[ -z "${CONFLUENCE_URL}" ]]; then
        missing_vars="${missing_vars}CONFLUENCE_URL "
        has_missing=true
    fi

    if [[ -z "${CONFLUENCE_USERNAME}" ]]; then
        missing_vars="${missing_vars}CONFLUENCE_USERNAME "
        has_missing=true
    fi

    if [[ -z "${CONFLUENCE_API_TOKEN}" ]]; then
        missing_vars="${missing_vars}CONFLUENCE_API_TOKEN "
        has_missing=true
    fi

    if [ "$has_missing" = true ]; then
        log ERROR "Missing required environment variables:"
        # Split missing_vars by space and iterate
        local old_ifs="$IFS"
        IFS=' '
        for var in $missing_vars; do
            if [ -n "$var" ]; then
                log ERROR "  - ${var}"
            fi
        done
        IFS="$old_ifs"
        log ERROR "Please set all required environment variables and restart the container."
        exit 1
    fi

    log INFO "✅ All required environment variables are set"
}

# Validate confluence URL format
validate_confluence_url() {
    if [[ ! "${CONFLUENCE_URL}" =~ ^https?:// ]]; then
        log ERROR "CONFLUENCE_URL must start with http:// or https://"
        log ERROR "Current value: ${CONFLUENCE_URL}"
        exit 1
    fi

    # Remove trailing slash if present
    export CONFLUENCE_URL="${CONFLUENCE_URL%/}"
    log INFO "✅ Confluence URL validated: ${CONFLUENCE_URL}"
}

# Validate cron schedule format
validate_cron_schedule() {
    # Basic validation - check if it has 5 parts using awk
    local field_count=$(echo "$CRON_SCHEDULE" | awk '{print NF}')
    if [ "$field_count" -ne 5 ]; then
        log ERROR "CRON_SCHEDULE must have 5 parts (minute hour day month weekday)"
        log ERROR "Current value: '${CRON_SCHEDULE}'"
        log ERROR "Example: '0 2 * * *' (daily at 2 AM)"
        exit 1
    fi

    # Extract weekday part using awk
    local weekday=$(echo "$CRON_SCHEDULE" | awk '{print $5}')
    if [[ ! "$weekday" =~ ^(\*|[0-7](,[0-7])*|[0-7])$ ]]; then
        log ERROR "Invalid weekday specification in CRON_SCHEDULE"
        log ERROR "Current value: '${CRON_SCHEDULE}'"
        log ERROR "Weekday must be * or 0-7 (0=Sunday, 7=Saturday) or comma-separated list"
        exit 1
    fi

    log INFO "✅ Cron schedule validated: ${CRON_SCHEDULE}"
}

# Generate cron configuration
setup_cron_job() {
    log INFO "⏰ Setting up cron job..."

    # Create the export script path
    local export_script="/app/docker/export-runner.sh"

    # Verify export script exists and is executable
    if [[ ! -x "${export_script}" ]]; then
        log ERROR "Export script not found or not executable: ${export_script}"
        exit 1
    fi

    # Generate crontab entry
    local cron_command="${export_script} 2>&1 | /usr/bin/logger -t confluence-exporter"
    local crontab_entry="${CRON_SCHEDULE} ${cron_command}"

    log INFO "Cron job configuration:"
    log INFO "  Schedule: ${CRON_SCHEDULE}"
    log INFO "  Command: ${export_script}"
    log INFO "  Logging: via syslog (tag: confluence-exporter)"

    # Create crontab
    echo "${crontab_entry}" > /tmp/crontab.tmp

    # Install crontab
    crontab /tmp/crontab.tmp

    # Verify crontab installation
    if crontab -l > /dev/null 2>&1; then
        log INFO "✅ Cron job installed successfully"
        log DEBUG "Current crontab:"
        crontab -l | while read line; do
            log DEBUG "  ${line}"
        done
    else
        log ERROR "❌ Failed to install cron job"
        exit 1
    fi

    # Clean up temporary file
    rm -f /tmp/crontab.tmp
}

# Setup logging configuration
setup_logging() {
    log INFO "📝 Setting up logging configuration..."

    # Create log directory
    mkdir -p /var/log/confluence-exporter

    # Set up log rotation for confluence-exporter logs
    cat > /etc/logrotate.d/confluence-exporter << EOF
/var/log/confluence-exporter/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

    # Configure syslog to separate confluence-exporter logs
    cat >> /etc/rsyslog.conf << EOF

# Confluence Exporter logging
:programname, isequal, "confluence-exporter" /var/log/confluence-exporter/cron.log
& stop
EOF

    log INFO "✅ Logging configuration completed"
    log INFO "  Cron logs: /var/log/confluence-exporter/cron.log"
    log INFO "  Export logs: /var/log/confluence-exporter/export.log"
}

# Setup confluence-markdown-exporter configuration
setup_confluence_config() {
    log INFO "🔧 Setting up Confluence configuration..."

    # Use confluence-markdown-exporter's config command to set up credentials
    log DEBUG "Configuring Confluence URL..."
    echo | confluence-markdown-exporter config --jump-to auth.confluence.url 2>/dev/null || true

    # Create config directory
    mkdir -p /root/.config/confluence-markdown-exporter

    # Create configuration file directly (since interactive config is complex in Docker)
    cat > /root/.config/confluence-markdown-exporter/config.json << EOF
{
    "auth": {
        "confluence": {
            "url": "${CONFLUENCE_URL}",
            "username": "${CONFLUENCE_USERNAME}",
            "api_token": "${CONFLUENCE_API_TOKEN}"
        }
    },
    "export": {
        "output_path": "${EXPORT_PATH}"
    }
}
EOF

    log INFO "✅ Confluence configuration created"
    log DEBUG "Config file location: /root/.config/confluence-markdown-exporter/config.json"
}

# Test confluence connection
test_confluence_connection() {
    log INFO "🧪 Testing Confluence connection..."

    # Try a simple CQL query to test connection
    if confluence-markdown-exporter search "type = page" /tmp/test_connection --limit 1 > /tmp/connection_test.log 2>&1; then
        log INFO "✅ Confluence connection test successful"
        rm -rf /tmp/test_connection /tmp/connection_test.log
    else
        log ERROR "❌ Confluence connection test failed"
        log ERROR "Check your credentials and network connectivity"
        log ERROR "Connection test output:"
        cat /tmp/connection_test.log | while read line; do
            log ERROR "  $line"
        done
        exit 1
    fi
}

# Create export directory
setup_export_directory() {
    log INFO "📁 Setting up export directory: ${EXPORT_PATH}"

    mkdir -p "${EXPORT_PATH}"

    if [[ ! -w "${EXPORT_PATH}" ]]; then
        log ERROR "Export directory is not writable: ${EXPORT_PATH}"
        exit 1
    fi

    log INFO "✅ Export directory ready: ${EXPORT_PATH}"
}

# Main execution
main() {
    log INFO "Starting environment validation..."

    validate_env
    validate_confluence_url
    validate_cron_schedule
    setup_export_directory
    setup_confluence_config
    test_confluence_connection
    setup_logging
    setup_cron_job

    log INFO "✅ All configuration completed successfully"
    log INFO "Configuration Summary:"
    log INFO "  Confluence URL: ${CONFLUENCE_URL}"
    log INFO "  Username: ${CONFLUENCE_USERNAME}"
    log INFO "  CQL Query: ${CQL_QUERY}"
    log INFO "  Cron Schedule: ${CRON_SCHEDULE}"
    log INFO "  Export Path: ${EXPORT_PATH}"
    log INFO "  Max Results: ${MAX_RESULTS}"

    log INFO "🚀 Starting supervisor..."
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
}

# Execute main function
main "$@"