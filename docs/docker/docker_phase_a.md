# Phase A: Docker Foundation

## Objective
Create the foundational Docker container with Python, supervisor, and cron daemon to run the confluence markdown exporter on a schedule.

## Prerequisites
- Confluence markdown exporter with CQL search functionality working
- Docker installed and running
- Basic familiarity with Dockerfile syntax

## Files to Create

### 1. `Dockerfile`

**Action**: Create new file in project root.

**Location**: `./Dockerfile`

**Code to Add**:

```dockerfile
# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Install the confluence markdown exporter in development mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/exports \
    /var/log/supervisor \
    /var/log/confluence-exporter

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port for health checks (optional)
EXPOSE 8080

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
```

### 2. `docker/supervisord.conf`

**Action**: Create supervisor configuration file.

**Location**: `./docker/supervisord.conf`

**Code to Add**:

```ini
[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
user=root

[program:cron]
command=/usr/sbin/cron -f
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/cron.err.log
stdout_logfile=/var/log/supervisor/cron.out.log
user=root

[program:confluence-exporter-healthcheck]
command=/app/docker/healthcheck.sh
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/healthcheck.err.log
stdout_logfile=/var/log/supervisor/healthcheck.out.log
user=root
```

### 3. `docker/entrypoint.sh`

**Action**: Create the main entrypoint script.

**Location**: `./docker/entrypoint.sh`

**Code to Add**:

```bash
#!/bin/bash
set -e

echo "🐳 Starting Confluence Markdown Exporter Docker Container"
echo "=================================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Phase A: Docker Foundation - Entrypoint Started"

# Create export directory if it doesn't exist
mkdir -p /app/exports

# Verify confluence-markdown-exporter is installed
if ! command -v confluence-markdown-exporter &> /dev/null; then
    log "ERROR: confluence-markdown-exporter not found"
    exit 1
fi

log "✅ Confluence Markdown Exporter found: $(which confluence-markdown-exporter)"

# Test basic functionality
log "🧪 Testing basic functionality..."
if confluence-markdown-exporter --help > /dev/null 2>&1; then
    log "✅ Basic functionality test passed"
else
    log "❌ Basic functionality test failed"
    exit 1
fi

log "🚀 Starting supervisor..."

# Start supervisor (this will start cron and other services)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
```

### 4. `docker/healthcheck.sh`

**Action**: Create simple health check script.

**Location**: `./docker/healthcheck.sh`

**Code to Add**:

```bash
#!/bin/bash

# Simple health check - verify confluence-markdown-exporter is accessible
if command -v confluence-markdown-exporter &> /dev/null; then
    echo "healthy"
    exit 0
else
    echo "unhealthy"
    exit 1
fi
```

## Testing Phase A

### 1. Verify Docker Foundation Files
```bash
# Check all files are created
ls -la Dockerfile
ls -la docker/supervisord.conf
ls -la docker/entrypoint.sh
ls -la docker/healthcheck.sh

# Verify permissions
chmod +x docker/entrypoint.sh
chmod +x docker/healthcheck.sh
```

### 2. Build Base Docker Image
```bash
# Build the Docker image
docker build -t confluence-exporter:foundation .

# Check build success
docker images | grep confluence-exporter
```

### 3. Test Basic Container Functionality
```bash
# Run container in test mode (will exit after entrypoint completes)
docker run --rm confluence-exporter:foundation

# Expected output should show:
# - Container starting
# - Confluence exporter found
# - Basic functionality test passed
# - Supervisor starting
```

### 4. Test Container with Shell Access
```bash
# Run container with shell to inspect
docker run -it --rm confluence-exporter:foundation bash

# Inside container, test:
which confluence-markdown-exporter
confluence-markdown-exporter --help
ls -la /app/exports
ps aux | grep supervisor
```

## Integration Test Script

Create `test_phase_a.py`:

```python
import subprocess
import time
import sys

def run_command(cmd, timeout=30):
    """Run command and return success status."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, 
            text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_docker_foundation():
    """Test Phase A - Docker Foundation."""
    
    print("🧪 Testing Phase A: Docker Foundation")
    print("=" * 50)
    
    tests = [
        ("Build Docker image", "docker build -t confluence-exporter:foundation ."),
        ("Verify image exists", "docker images confluence-exporter:foundation"),
        ("Test basic container run", "docker run --rm --name test-foundation confluence-exporter:foundation echo 'Container test'"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, command in tests:
        print(f"\n🔄 Running: {test_name}")
        success, stdout, stderr = run_command(command)
        
        if success:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            print(f"   Error: {stderr}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    success = test_docker_foundation()
    sys.exit(0 if success else 1)
```

Run: `python test_phase_a.py`

## Expected Results After Phase A

1. ✅ Docker image builds successfully
2. ✅ Container starts without errors
3. ✅ Supervisor runs and manages processes
4. ✅ Cron daemon starts (visible in `ps aux`)
5. ✅ Confluence markdown exporter is accessible
6. ✅ Basic health check works
7. ✅ Log directories are created
8. ✅ Export directory exists

## Directory Structure After Phase A

```
confluence-markdown-exporter-docker/
├── Dockerfile
├── docker/
│   ├── supervisord.conf
│   ├── entrypoint.sh
│   └── healthcheck.sh
├── confluence_markdown_exporter/
│   └── (existing code)
├── requirements.txt
├── test_phase_a.py
└── (other existing files)
```

## Troubleshooting Phase A

### Common Issues

**Issue**: Docker build fails with permission errors  
**Solution**: 
```bash
# Check file permissions
ls -la docker/
chmod +x docker/entrypoint.sh docker/healthcheck.sh
```

**Issue**: Confluence exporter not found in container  
**Solution**: 
```bash
# Verify pip install worked
docker run -it --rm confluence-exporter:foundation bash
pip list | grep confluence
```

**Issue**: Supervisor fails to start  
**Solution**: 
```bash
# Check supervisor config syntax
docker run -it --rm confluence-exporter:foundation bash
supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
```

**Issue**: Container exits immediately  
**Solution**: 
```bash
# Run with bash to debug
docker run -it --rm confluence-exporter:foundation bash
# Check entrypoint script manually
bash -x /entrypoint.sh
```

## Next Steps

Once Phase A is complete and all tests pass:
1. Docker foundation is solid
2. Container can run the confluence exporter
3. Supervisor and cron are operational
4. Ready to proceed to Phase B for environment configuration

Phase A establishes the basic container infrastructure needed for the cron-based export service.