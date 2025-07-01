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