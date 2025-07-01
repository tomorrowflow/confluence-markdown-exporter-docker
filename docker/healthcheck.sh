#!/bin/bash

# Advanced health check with detailed diagnostics
# Reports on multiple aspects of container health

set -e

# Health check configuration
HEALTH_LOG="/var/log/confluence-exporter/health.log"
MAX_LOG_AGE_HOURS=24
MAX_EXPORT_AGE_HOURS=48

log_health() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] HEALTH: $*" | tee -a "$HEALTH_LOG"
}

check_basic_functionality() {
    # Check confluence-markdown-exporter is available
    python -m confluence_markdown_exporter.main --help
    if ! command -v python -m confluence_markdown_exporter.main --help &> /dev/null; then
        echo "UNHEALTHY: confluence-markdown-exporter not found"
        return 1
    fi

    # Check configuration exists
    ls /root/.config/confluence-markdown-exporter/
    if [[ ! -f /root/.config/confluence-markdown-exporter/config.json ]]; then
        echo "UNHEALTHY: Configuration file missing"
        return 1
    fi

    return 0
}

check_cron_status() {
    # Check if cron is running
    if ! pidof cron > /dev/null; then
        echo "UNHEALTHY: Cron daemon not running"
        return 1
    fi

    # Check if crontab is installed
    if ! crontab -l > /dev/null 2>&1; then
        echo "UNHEALTHY: No crontab installed"
        return 1
    fi

    return 0
}

check_recent_activity() {
    local export_dir="/app/exports"
    local current_time=$(date +%s)
    local max_age_seconds=$((MAX_EXPORT_AGE_HOURS * 3600))

    # Check if any exports exist
    if [[ ! -d "$export_dir" ]] || [[ -z "$(ls -A "$export_dir" 2>/dev/null)" ]]; then
        echo "WARNING: No exports found (may be normal for new container)"
        return 0
    fi

    # Find most recent export
    local latest_export=$(find "$export_dir" -type d -name "*-*-*_*-*-*" | sort | tail -1)

    if [[ -n "$latest_export" ]]; then
        local export_time=$(stat -c %Y "$latest_export" 2>/dev/null || echo 0)
        local age_seconds=$((current_time - export_time))

        if [[ $age_seconds -gt $max_age_seconds ]]; then
            echo "WARNING: Latest export is $((age_seconds / 3600)) hours old"
            return 0
        fi
    fi

    return 0
}

check_log_health() {
    local log_dir="/var/log/confluence-exporter"
    local current_time=$(date +%s)
    local max_age_seconds=$((MAX_LOG_AGE_HOURS * 3600))

    # Check for recent log activity
    if [[ -f "$log_dir/export.log" ]]; then
        local log_time=$(stat -c %Y "$log_dir/export.log" 2>/dev/null || echo 0)
        local age_seconds=$((current_time - log_time))

        if [[ $age_seconds -gt $max_age_seconds ]]; then
            echo "WARNING: Export log hasn't been updated in $((age_seconds / 3600)) hours"
        fi
    fi

    return 0
}

check_disk_space() {
    # Check available disk space in export directory
    local export_dir="/app/exports"
    local available_space=$(df "$export_dir" | awk 'NR==2 {print $4}')
    local available_mb=$((available_space / 1024))

    if [[ $available_mb -lt 100 ]]; then
        echo "WARNING: Low disk space: ${available_mb}MB available"
    fi

    return 0
}

generate_health_report() {
    log_health "=== Health Check Report ==="

    # Basic functionality
    if check_basic_functionality; then
        log_health "✅ Basic functionality: OK"
    else
        log_health "❌ Basic functionality: FAILED"
        return 1
    fi

    # Cron status
    if check_cron_status; then
        log_health "✅ Cron status: OK"
    else
        log_health "❌ Cron status: FAILED"
        return 1
    fi

    # Recent activity (warnings don't fail health check)
    check_recent_activity

    # Log health (warnings don't fail health check)
    check_log_health

    # Disk space (warnings don't fail health check)
    check_disk_space

    # System metrics
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local memory_usage=$(free | awk '/^Mem:/{printf "%.1f", $3/$2 * 100.0}')

    log_health "📊 System metrics:"
    log_health "   Load average: $load_avg"
    log_health "   Memory usage: ${memory_usage}%"

    log_health "✅ Health check completed successfully"
    return 0
}

# Main execution
if generate_health_report; then
    echo "healthy"
    exit 0
else
    echo "unhealthy"
    exit 1
fi