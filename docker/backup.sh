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