# Phase E: Production Features (Optional)

## Objective
Add advanced production features including monitoring, alerting, backup automation, and cleanup processes for enterprise deployment.

## Prerequisites
- Phases A through D completed successfully
- Docker Compose working in production
- Basic deployment tested and functional

## Optional Features Overview

This phase is **completely optional** but provides enterprise-grade features for production environments:

1. **Advanced Health Monitoring**: Detailed health checks and metrics
2. **Backup Automation**: Automated backup of exports and configuration
3. **Cleanup Automation**: Automated cleanup of old exports
4. **Metrics Collection**: Export metrics and statistics
5. **Alert Integration**: Webhook notifications for failures
6. **Performance Monitoring**: Resource usage tracking

## Files to Create/Modify

### 1. Enhanced Health Check (`docker/healthcheck.sh`)

**Action**: Create comprehensive health monitoring.

**Location**: `./docker/healthcheck.sh`

**Code to Add**:

```bash
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
    if ! command -v confluence-markdown-exporter &> /dev/null; then
        echo "UNHEALTHY: confluence-markdown-exporter not found"
        return 1
    fi
    
    # Check configuration exists
    if [[ ! -f /root/.config/confluence-markdown-exporter/config.json ]]; then
        echo "UNHEALTHY: Configuration file missing"
        return 1
    fi
    
    return 0
}

check_cron_status() {
    # Check if cron is running
    if ! pgrep cron > /dev/null; then
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
```

### 2. Metrics Collection (`docker/metrics-collector.sh`)

**Action**: Create metrics collection for monitoring.

**Location**: `./docker/metrics-collector.sh`

**Code to Add**:

```bash
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
```

### 3. Backup Automation (`docker/backup.sh`)

**Action**: Create automated backup functionality.

**Location**: `./docker/backup.sh`

**Code to Add**:

```bash
#!/bin/bash

# Automated backup for Confluence Markdown Exporter
# Creates compressed backups of exports and configuration

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
EXPORT_DIR="${EXPORT_DIR:-/app/exports}"
CONFIG_DIR="/root/.config/confluence-markdown-exporter"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BACKUP: $*"
}

create_backup() {
    log "🔄 Starting backup process..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    local backup_name="confluence-exporter-backup-${BACKUP_TIMESTAMP}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    # Create temporary backup directory
    mkdir -p "$backup_path"
    
    # Backup exports
    if [[ -d "$EXPORT_DIR" ]] && [[ -n "$(ls -A "$EXPORT_DIR" 2>/dev/null)" ]]; then
        log "📄 Backing up exports..."
        cp -r "$EXPORT_DIR" "$backup_path/exports"
        
        local export_count=$(find "$backup_path/exports" -name "*.md" -type f | wc -l)
        log "   Backed up $export_count markdown files"
    else
        log "ℹ️  No exports to backup"
        mkdir -p "$backup_path/exports"
    fi
    
    # Backup configuration
    if [[ -d "$CONFIG_DIR" ]]; then
        log "⚙️  Backing up configuration..."
        cp -r "$CONFIG_DIR" "$backup_path/config"
    else
        log "ℹ️  No configuration to backup"
        mkdir -p "$backup_path/config"
    fi
    
    # Backup logs (recent only)
    local log_dir="/var/log/confluence-exporter"
    if [[ -d "$log_dir" ]]; then
        log "📝 Backing up recent logs..."
        mkdir -p "$backup_path/logs"
        
        # Only backup logs from last 7 days
        find "$log_dir" -name "*.log" -mtime -7 -exec cp {} "$backup_path/logs/" \;
    fi
    
    # Create metadata
    cat > "$backup_path/metadata.json" << EOF
{
    "backup_timestamp": "$BACKUP_TIMESTAMP",
    "backup_date": "$(date -Iseconds)",
    "container_name": "${CONTAINER_NAME:-unknown}",
    "confluence_url": "${CONFLUENCE_URL:-unknown}",
    "cql_query": "${CQL_QUERY:-unknown}",
    "export_count": $(find "$backup_path/exports" -name "*.md" -type f 2>/dev/null | wc -l),
    "backup_size_bytes": $(du -sb "$backup_path" | cut -f1)
}
EOF

    # Compress backup
    log "🗜️  Compressing backup..."
    cd "$BACKUP_DIR"
    tar -czf "${backup_name}.tar.gz" "$backup_name"
    rm -rf "$backup_name"
    
    local backup_size=$(du -sh "${backup_name}.tar.gz" | cut -f1)
    log "✅ Backup completed: ${backup_name}.tar.gz (${backup_size})"
    
    return 0
}

cleanup_old_backups() {
    log "🧹 Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
    
    local deleted_count=0
    while IFS= read -r -d '' backup_file; do
        rm -f "$backup_file"
        ((deleted_count++))
        log "   Deleted: $(basename "$backup_file")"
    done < <(find "$BACKUP_DIR" -name "confluence-exporter-backup-*.tar.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [[ $deleted_count -eq 0 ]]; then
        log "ℹ️  No old backups to clean up"
    else
        log "✅ Cleaned up $deleted_count old backup(s)"
    fi
}

# Main execution
main() {
    log "🗄️  Starting Confluence Exporter Backup"
    
    create_backup
    cleanup_old_backups
    
    log "🎉 Backup process completed successfully"
}

main "$@"
```

### 4. Enhanced Docker Compose (`docker-compose.prod.yml`)

**Action**: Create production-focused compose override.

**Location**: `./docker-compose.prod.yml`

**Code to Add**:

```yaml
version: '3.8'

services:
  confluence-exporter:
    # Production overrides
    restart: always
    
    # Use advanced health check
    healthcheck:
      test: ["/app/docker/healthcheck.sh"]
      interval: 10m
      timeout: 1m
      retries: 3
      start_period: 2m
    
    # Additional volumes for production features
    volumes:
      - ./exports:/app/exports
      - ./logs:/var/log/confluence-exporter
      - ./backups:/app/backups
      - ./metrics:/app/metrics
    
    # Environment for production features
    environment:
      - BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
      - METRICS_COLLECTION_ENABLED=${METRICS_COLLECTION_ENABLED:-true}
      - WEBHOOK_URL=${WEBHOOK_URL:-}
    
    # Resource limits for production
    deploy:
      resources:
        limits:
          memory: ${MEMORY_LIMIT:-1G}
          cpus: '${CPU_LIMIT:-1.0}'
        reservations:
          memory: 512M
          cpus: '0.5'

  # Metrics exporter (optional)
  metrics-exporter:
    image: nginx:alpine
    container_name: ${CONTAINER_NAME:-confluence-exporter}-metrics
    restart: unless-stopped
    profiles:
      - metrics
    
    ports:
      - "${METRICS_PORT:-9090}:80"
    
    volumes:
      - ./metrics:/usr/share/nginx/html:ro
      - ./docker/nginx-metrics.conf:/etc/nginx/conf.d/default.conf:ro
    
    depends_on:
      - confluence-exporter

  # Backup service (optional)
  backup-service:
    build: .
    container_name: ${CONTAINER_NAME:-confluence-exporter}-backup
    restart: "no"
    profiles:
      - backup
    
    environment:
      - BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
    
    volumes:
      - ./exports:/app/exports:ro
      - ./logs:/var/log/confluence-exporter:ro
      - ./backups:/app/backups
    
    command: ["/app/docker/backup.sh"]
    
    depends_on:
      - confluence-exporter

volumes:
  backups:
    driver: local
  metrics:
    driver: local
```

### 5. Alert Integration (`docker/alert-webhook.sh`)

**Action**: Create webhook alerting for failures.

**Location**: `./docker/alert-webhook.sh`

**Code to Add**:

```bash
#!/bin/bash

# Webhook alerting for Confluence Markdown Exporter
# Sends alerts to configured webhook URL

send_alert() {
    local alert_type="$1"
    local message="$2"
    local webhook_url="${WEBHOOK_URL:-}"
    
    if [[ -z "$webhook_url" ]]; then
        echo "No webhook URL configured, skipping alert"
        return 0
    fi
    
    local payload=$(cat << EOF
{
    "text": "Confluence Exporter Alert",
    "attachments": [
        {
            "color": "$([ "$alert_type" = "success" ] && echo "good" || echo "danger")",
            "fields": [
                {
                    "title": "Alert Type",
                    "value": "$alert_type",
                    "short": true
                },
                {
                    "title": "Container",
                    "value": "${CONTAINER_NAME:-confluence-exporter}",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                },
                {
                    "title": "Timestamp",
                    "value": "$(date -Iseconds)",
                    "short": true
                }
            ]
        }
    ]
}
EOF
)

    if curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$webhook_url"; then
        echo "Alert sent successfully"
    else
        echo "Failed to send alert"
    fi
}

# Usage examples:
# send_alert "error" "Export failed: Connection timeout"
# send_alert "success" "Daily export completed successfully"
# send_alert "warning" "Disk space low: 95% full"

"$@"
```

## Testing Phase E

### 1. Test Advanced Health Check

```bash
# Make scripts executable
chmod +x docker/healthcheck.sh
chmod +x docker/metrics-collector.sh
chmod +x docker/backup.sh
chmod +x docker/alert-webhook.sh

# Test advanced health check
docker run --rm -v $(pwd):/app confluence-exporter:latest /app/docker/healthcheck.sh
```

### 2. Test Metrics Collection

```bash
# Create metrics directory
mkdir -p metrics

# Run metrics collection
docker run --rm -v $(pwd)/metrics:/app/metrics confluence-exporter:latest /app/docker/metrics-collector.sh

# Check metrics file
cat metrics/metrics.txt
```

### 3. Test Backup Functionality

```bash
# Create backup directory
mkdir -p backups

# Test backup
docker run --rm \
  -v $(pwd)/exports:/app/exports:ro \
  -v $(pwd)/backups:/app/backups \
  -e BACKUP_RETENTION_DAYS=7 \
  confluence-exporter:latest /app/docker/backup.sh

# Check backup created
ls -la backups/
```

### 4. Test Production Compose

```bash
# Start with production features
COMPOSE_PROFILES=metrics,backup docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check all services
docker-compose ps

# Test metrics endpoint
curl http://localhost:9090
```

## Expected Results After Phase E

1. ✅ Advanced health monitoring with detailed diagnostics
2. ✅ Metrics collection in Prometheus format
3. ✅ Automated backup with configurable retention
4. ✅ Webhook alerting integration
5. ✅ Production-grade resource management
6. ✅ Optional monitoring and backup services
7. ✅ Enhanced logging and diagnostics

## Production Features Usage

### Enable Metrics Collection
```bash
echo "COMPOSE_PROFILES=metrics" >> .env
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Enable Backup Service
```bash
echo "COMPOSE_PROFILES=backup" >> .env
# Run backup manually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backup-service
```

### Configure Webhook Alerts
```bash
echo "WEBHOOK_URL=https://hooks.slack.com/your/webhook/url" >> .env
```

### Monitor with Advanced Health Checks
```bash
# View detailed health logs
docker exec confluence-exporter cat /var/log/confluence-exporter/health.log

# Get metrics
curl http://localhost:9090/metrics.txt
```

## Summary

**Phase E is completely optional** but provides enterprise-grade features:

- **Basic Setup (Phases A-D)**: Fully functional automated export system
- **Enhanced Setup (Phase E)**: Enterprise monitoring, backup, and alerting

Choose Phase E features based on your production requirements:
- **Metrics**: For monitoring and observability
- **Backup**: For data protection and disaster recovery  
- **Alerts**: For proactive issue notification
- **Advanced Health**: For detailed system diagnostics

The Docker implementation is now **production-ready** with optional enterprise features for advanced use cases.
