# Phase C: Cron Integration

## Objective
Implement cron job generation from environment variables, create the export script, and set up comprehensive logging for scheduled exports.

## Prerequisites
- Phase A and B completed successfully
- Environment configuration working
- Confluence connection tested and validated

## Files to Create/Modify

### 1. Update `docker/entrypoint.sh`

**Action**: Add cron configuration generation to the entrypoint script.

**Location**: `./docker/entrypoint.sh`

**Code to Add** (append before the final `main` function):

```bash
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
```

**Update the `main` function** to include the new setup functions:

```bash
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
```

### 2. Create `docker/export-runner.sh`

**Action**: Create the main export script that will be executed by cron.

**Location**: `./docker/export-runner.sh`

**Code to Add**:

```bash
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
        ln -s "${timestamped_export_path}" "${latest_link}"
        export_log "INFO" "✅ Latest export symlink updated: ${latest_link}"
        
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
```

### 3. Update `docker/supervisord.conf`

**Action**: Update supervisor configuration to include rsyslog for better logging.

**Location**: `./docker/supervisord.conf`

**Code to Replace**:

```ini
[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
user=root
loglevel=info

[program:rsyslog]
command=/usr/sbin/rsyslogd -n
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/rsyslog.err.log
stdout_logfile=/var/log/supervisor/rsyslog.out.log
user=root
priority=1

[program:cron]
command=/usr/sbin/cron -f
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/cron.err.log
stdout_logfile=/var/log/supervisor/cron.out.log
user=root
priority=2

[program:confluence-exporter-healthcheck]
command=/app/docker/healthcheck.sh
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/healthcheck.err.log
stdout_logfile=/var/log/supervisor/healthcheck.out.log
user=root
priority=3
```

### 4. Update `Dockerfile`

**Action**: Add rsyslog and make export script executable.

**Location**: `./Dockerfile`

**Code to Update** (replace the system dependencies section):

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    supervisor \
    rsyslog \
    logrotate \
    && rm -rf /var/lib/apt/lists/*
```

**Add after copying application** (before the final ENTRYPOINT):

```dockerfile
# Make scripts executable
RUN chmod +x docker/export-runner.sh docker/healthcheck.sh
```

### 5. Create `docker/test-export.sh`

**Action**: Create manual test script for export functionality.

**Location**: `./docker/test-export.sh`

**Code to Add**:

```bash
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
```

## Testing Phase C

### 1. Build Updated Docker Image

```bash
# Build image with cron integration
docker build -t confluence-exporter:cron .

# Verify scripts are executable
docker run --rm confluence-exporter:cron ls -la /app/docker/
```

### 2. Test Export Script Manually

```bash
# Test with minimal valid environment
docker run --rm \
  -e CONFLUENCE_URL=https://test.atlassian.net \
  -e CONFLUENCE_USERNAME=test@example.com \
  -e CONFLUENCE_API_TOKEN=test-token \
  -e CQL_QUERY="type = page" \
  -e EXPORT_PATH=/app/exports \
  -e MAX_RESULTS=5 \
  confluence-exporter:cron \
  /app/docker/test-export.sh
```

### 3. Test Cron Job Generation

```bash
# Start container and check cron installation
docker run -d --name test-cron \
  -e CONFLUENCE_URL=https://test.atlassian.net \
  -e CONFLUENCE_USERNAME=test@example.com \
  -e CONFLUENCE_API_TOKEN=test-token \
  -e CQL_QUERY="space = MFS" \
  -e CRON_SCHEDULE="*/5 * * * *" \
  confluence-exporter:cron

# Check if cron job is installed
sleep 10
docker exec test-cron crontab -l

# Check logs
docker logs test-cron

# Cleanup
docker stop test-cron
docker rm test-cron
```

### 4. Test Different Cron Schedules

Create `test_phase_c.py`:

```python
import subprocess
import time
import tempfile
import os

def test_cron_integration():
    """Test Phase C - Cron Integration."""
    
    print("🧪 Testing Phase C: Cron Integration")
    print("=" * 50)
    
    # Test different cron schedules
    test_schedules = [
        ("Daily at 2 AM", "0 2 * * *"),
        ("Every 6 hours", "0 */6 * * *"),
        ("Weekdays at 9 AM", "0 9 * * 1-5"),
        ("Every 5 minutes (test)", "*/5 * * * *")
    ]
    
    base_env = {
        "CONFLUENCE_URL": "https://test.atlassian.net",
        "CONFLUENCE_USERNAME": "test@example.com", 
        "CONFLUENCE_API_TOKEN": "test-token",
        "CQL_QUERY": "space = MFS",
        "EXPORT_PATH": "/app/exports",
        "MAX_RESULTS": "5"
    }
    
    passed = 0
    failed = 0
    
    for schedule_name, cron_schedule in test_schedules:
        print(f"\n🔄 Testing: {schedule_name} ({cron_schedule})")
        
        test_env = base_env.copy()
        test_env["CRON_SCHEDULE"] = cron_schedule
        test_env["CONTAINER_NAME"] = f"test-{schedule_name.lower().replace(' ', '-')}"
        
        # Create environment file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            for key, value in test_env.items():
                f.write(f"{key}={value}\n")
            env_file = f.name
        
        try:
            # Test container startup with this schedule
            cmd = f"docker run --rm --env-file {env_file} confluence-exporter:cron echo 'Schedule test complete'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ {schedule_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {schedule_name}: FAILED")
                print(f"   Error: {result.stderr}")
                failed += 1
                
        except subprocess.TimeoutExpired:
            print(f"❌ {schedule_name}: TIMEOUT")
            failed += 1
        finally:
            os.unlink(env_file)
    
    # Test export script functionality
    print(f"\n🔄 Testing export script...")
    try:
        cmd = "docker run --rm confluence-exporter:cron test -x /app/docker/export-runner.sh"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Export script executable: PASSED")
            passed += 1
        else:
            print(f"❌ Export script executable: FAILED")
            failed += 1
    except Exception as e:
        print(f"❌ Export script test: FAILED - {e}")
        failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = test_cron_integration()
    sys.exit(0 if success else 1)
```

Run: `python test_phase_c.py`

## Expected Results After Phase C

1. ✅ Cron job is automatically generated from CRON_SCHEDULE environment variable
2. ✅ Export script runs successfully when triggered
3. ✅ Timestamped export directories are created
4. ✅ Detailed logging to both syslog and dedicated log files
5. ✅ Latest export symlink is maintained
6. ✅ Failed exports are cleaned up automatically
7. ✅ Supervisor manages cron, rsyslog, and health check processes
8. ✅ Export results are properly logged and counted

## Log File Locations

After Phase C, logs will be available at:
- **Cron execution logs**: `/var/log/confluence-exporter/cron.log`
- **Export details**: `/var/log/confluence-exporter/export.log`
- **Supervisor logs**: `/var/log/supervisor/`
- **Container stdout**: `docker logs <container-name>`

## Troubleshooting Phase C

### Common Issues

**Issue**: Cron job not executing  
**Solution**: 
```bash
# Check cron status and logs
docker exec <container> service cron status
docker exec <container> tail -f /var/log/confluence-exporter/cron.log
```

**Issue**: Export script fails  
**Solution**: 
```bash
# Run export script manually
docker exec <container> /app/docker/export-runner.sh
# Check detailed logs
docker exec <container> cat /var/log/confluence-exporter/export.log
```

**Issue**: No log files created  
**Solution**: 
```bash
# Check rsyslog status
docker exec <container> service rsyslog status
# Check log directory permissions
docker exec <container> ls -la /var/log/confluence-exporter/
```

**Issue**: Supervisor processes not starting  
**Solution**: 
```bash
# Check supervisor status
docker exec <container> supervisorctl status
# Restart specific service
docker exec <container> supervisorctl restart cron
```

## Next Steps

Once Phase C is complete and all tests pass:
1. Cron-based export automation is functional
2. Comprehensive logging is in place
3. Export script handles success and failure scenarios
4. Ready to proceed to Phase D for Docker Compose and testing

Phase C establishes the core automation functionality for scheduled Confluence exports.
