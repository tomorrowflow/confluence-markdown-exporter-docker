#!/bin/bash

# Metrics collector for Confluence Markdown Exporter
# Collects and exports metrics in Prometheus format

METRICS_FILE="/var/log/confluence-exporter/metrics.txt"
EXPORT_DIR="/app/exports"

collect_metrics() {
    local timestamp=$(date +%s)

    cat > "$METRICS_FILE" << EOF
# HELP confluence_exporter_exports_total Total number of export directories
# TYPE confluence_exporter_exports_total counter
confluence_exporter_exports_total $(find "$EXPORT_DIR" -type d -name "*-*-*_*-*-*" | wc -l)

# HELP confluence_exporter_latest_export_timestamp Timestamp of latest export
# TYPE confluence_exporter_latest_export_timestamp gauge
confluence_exporter_latest_export_timestamp $(find "$EXPORT_DIR" -type d -name "*-*-*_*-*-*" -exec stat -c %Y {} \; | sort -n | tail -1 || echo 0)

# HELP confluence_exporter_export_files_total Total number of exported markdown files
# TYPE confluence_exporter_export_files_total counter
confluence_exporter_export_files_total $(find "$EXPORT_DIR" -name "*.md" -type f | wc -l)

# HELP confluence_exporter_export_size_bytes Total size of exports in bytes
# TYPE confluence_exporter_export_size_bytes gauge
confluence_exporter_export_size_bytes $(du -sb "$EXPORT_DIR" 2>/dev/null | cut -f1 || echo 0)

# HELP confluence_exporter_container_uptime_seconds Container uptime in seconds
# TYPE confluence_exporter_container_uptime_seconds gauge
confluence_exporter_container_uptime_seconds $(awk '{print int($1)}' /proc/uptime)

# HELP confluence_exporter_memory_usage_bytes Memory usage in bytes
# TYPE confluence_exporter_memory_usage_bytes gauge
confluence_exporter_memory_usage_bytes $(awk '/^MemTotal:/{total=$2} /^MemAvailable:/{available=$2} END{print (total-available)*1024}' /proc/meminfo)

# HELP confluence_exporter_last_check_timestamp Timestamp of last metrics collection
# TYPE confluence_exporter_last_check_timestamp gauge
confluence_exporter_last_check_timestamp $timestamp
EOF

    echo "Metrics collected at $(date)"
}

# Run metrics collection
collect_metrics