# Phase B: Environment Configuration

## Objective
Implement comprehensive environment variable configuration for Confluence credentials, cron scheduling, and export parameters.

## Prerequisites
- Phase A completed successfully
- Docker foundation container builds and runs
- Understanding of confluence-markdown-exporter config system

## Environment Variable Schema

### Required Variables
| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `CONFLUENCE_URL` | Confluence instance URL | `https://company.atlassian.net` | None |
| `CONFLUENCE_USERNAME` | Username or email | `user@company.com` | None |
| `CONFLUENCE_API_TOKEN` | API token or password | `ATAxxxxxxx` | None |
| `CQL_QUERY` | Search query for export | `space = MFS` | `type = page` |
| `CRON_SCHEDULE` | Cron schedule expression | `0 2 * * *` | `0 2 * * *` |

### Optional Variables
| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `EXPORT_PATH` | Output directory inside container | `/app/exports` | `/app/exports` |
| `MAX_RESULTS` | Maximum pages to export | `500` | `100` |
| `LOG_LEVEL` | Logging level | `DEBUG` | `INFO` |
| `CONTAINER_NAME` | Container identification | `docs-exporter` | `confluence-exporter` |

## Files to Modify/Create

### 1. Update `docker/entrypoint.sh`

**Action**: Replace the existing entrypoint script with comprehensive environment handling.

**Location**: `./docker/entrypoint.sh`

**Code to Replace**:

```bash
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
    local missing_vars=()
    
    if [[ -z "${CONFLUENCE_URL}" ]]; then
        missing_vars+=("CONFLUENCE_URL")
    fi
    
    if [[ -z "${CONFLUENCE_USERNAME}" ]]; then
        missing_vars+=("CONFLUENCE_USERNAME")
    fi
    
    if [[ -z "${CONFLUENCE_API_TOKEN}" ]]; then
        missing_vars+=("CONFLUENCE_API_TOKEN")
    fi
    
    if [[ ${#missing_vars[@]} -ne 0 ]]; then
        log ERROR "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log ERROR "  - ${var}"
        done
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
    # Basic validation - check if it has 5 parts
    local cron_parts=(${CRON_SCHEDULE})
    if [[ ${#cron_parts[@]} -ne 5 ]]; then
        log ERROR "CRON_SCHEDULE must have 5 parts (minute hour day month weekday)"
        log ERROR "Current value: '${CRON_SCHEDULE}'"
        log ERROR "Example: '0 2 * * *' (daily at 2 AM)"
        exit 1
    fi
    
    log INFO "✅ Cron schedule validated: ${CRON_SCHEDULE}"
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
    
    log INFO "✅ Environment configuration completed successfully"
    log INFO "Configuration Summary:"
    log INFO "  Confluence URL: ${CONFLUENCE_URL}"
    log INFO "  Username: ${CONFLUENCE_USERNAME}"
    log INFO "  CQL Query: ${CQL_QUERY}"
    log INFO "  Cron Schedule: ${CRON_SCHEDULE}"
    log INFO "  Export Path: ${EXPORT_PATH}"
    log INFO "  Max Results: ${MAX_RESULTS}"
    
    # Continue to Phase C (will be implemented later)
    log INFO "🚀 Starting supervisor..."
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
}

# Execute main function
main "$@"
```

### 2. Create `.env.example`

**Action**: Create example environment file for documentation.

**Location**: `./.env.example`

**Code to Add**:

```bash
# Confluence Markdown Exporter - Docker Environment Configuration
# Copy this file to .env and configure your values

# ============================================================================
# REQUIRED CONFIGURATION
# ============================================================================

# Confluence instance URL (include https://)
CONFLUENCE_URL=https://your-company.atlassian.net

# Confluence credentials
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token-here

# ============================================================================
# SEARCH AND SCHEDULING CONFIGURATION  
# ============================================================================

# CQL query for finding pages to export
# Examples:
#   space = MFS                                    # All pages in MFS space
#   space = DOCS AND lastModified >= startOfWeek() # Recent pages in DOCS
#   creator = jsmith AND label = important         # Important pages by jsmith
CQL_QUERY=space = MFS

# Cron schedule for exports (minute hour day month weekday)
# Examples:
#   0 2 * * *     # Daily at 2 AM
#   0 14 * * 1    # Weekly on Monday at 2 PM  
#   */6 * * * *   # Every 6 hours
#   0 9,17 * * 1-5 # Twice daily on weekdays
CRON_SCHEDULE=0 2 * * *

# ============================================================================
# OPTIONAL CONFIGURATION
# ============================================================================

# Export directory inside container
EXPORT_PATH=/app/exports

# Maximum number of pages to export per run
MAX_RESULTS=100

# Logging level (DEBUG, INFO, WARN, ERROR)
LOG_LEVEL=INFO

# Container name for identification in logs
CONTAINER_NAME=confluence-exporter
```

### 3. Create `docker/config-validator.sh`

**Action**: Create standalone configuration validator.

**Location**: `./docker/config-validator.sh`

**Code to Add**:

```bash
#!/bin/bash

# Configuration validator for Confluence Markdown Exporter
# Can be run independently to validate environment before container start

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

validate_config() {
    local errors=0
    
    echo "🔍 Validating Confluence Markdown Exporter Configuration"
    echo "======================================================="
    
    # Check required variables
    echo -e "\n📋 Required Variables:"
    
    if [[ -n "${CONFLUENCE_URL}" ]]; then
        if [[ "${CONFLUENCE_URL}" =~ ^https?:// ]]; then
            echo -e "  ✅ CONFLUENCE_URL: ${GREEN}${CONFLUENCE_URL}${NC}"
        else
            echo -e "  ❌ CONFLUENCE_URL: ${RED}Must start with http:// or https://${NC}"
            ((errors++))
        fi
    else
        echo -e "  ❌ CONFLUENCE_URL: ${RED}Not set${NC}"
        ((errors++))
    fi
    
    if [[ -n "${CONFLUENCE_USERNAME}" ]]; then
        echo -e "  ✅ CONFLUENCE_USERNAME: ${GREEN}${CONFLUENCE_USERNAME}${NC}"
    else
        echo -e "  ❌ CONFLUENCE_USERNAME: ${RED}Not set${NC}"
        ((errors++))
    fi
    
    if [[ -n "${CONFLUENCE_API_TOKEN}" ]]; then
        echo -e "  ✅ CONFLUENCE_API_TOKEN: ${GREEN}[HIDDEN]${NC}"
    else
        echo -e "  ❌ CONFLUENCE_API_TOKEN: ${RED}Not set${NC}"
        ((errors++))
    fi
    
    # Check optional variables with defaults
    echo -e "\n⚙️  Optional Variables:"
    echo -e "  📝 CQL_QUERY: ${YELLOW}${CQL_QUERY:-"type = page"}${NC}"
    echo -e "  ⏰ CRON_SCHEDULE: ${YELLOW}${CRON_SCHEDULE:-"0 2 * * *"}${NC}"
    echo -e "  📁 EXPORT_PATH: ${YELLOW}${EXPORT_PATH:-"/app/exports"}${NC}"
    echo -e "  🔢 MAX_RESULTS: ${YELLOW}${MAX_RESULTS:-"100"}${NC}"
    echo -e "  📊 LOG_LEVEL: ${YELLOW}${LOG_LEVEL:-"INFO"}${NC}"
    
    # Validate cron schedule format
    local cron_schedule="${CRON_SCHEDULE:-"0 2 * * *"}"
    local cron_parts=(${cron_schedule})
    if [[ ${#cron_parts[@]} -eq 5 ]]; then
        echo -e "  ✅ Cron format: ${GREEN}Valid (5 parts)${NC}"
    else
        echo -e "  ❌ Cron format: ${RED}Invalid (need 5 parts: minute hour day month weekday)${NC}"
        ((errors++))
    fi
    
    echo -e "\n📊 Validation Summary:"
    if [[ $errors -eq 0 ]]; then
        echo -e "  ${GREEN}✅ Configuration is valid!${NC}"
        echo -e "  ${GREEN}Ready to start Confluence Markdown Exporter${NC}"
        return 0
    else
        echo -e "  ${RED}❌ Found $errors configuration errors${NC}"
        echo -e "  ${RED}Please fix the errors above before starting${NC}"
        return 1
    fi
}

# Run validation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    validate_config
fi
```

## Testing Phase B

### 1. Create Test Environment File

Create `test.env`:

```bash
CONFLUENCE_URL=https://test.atlassian.net
CONFLUENCE_USERNAME=test@example.com
CONFLUENCE_API_TOKEN=test-token-123
CQL_QUERY=space = MFS
CRON_SCHEDULE=0 2 * * *
EXPORT_PATH=/app/exports
MAX_RESULTS=50
LOG_LEVEL=DEBUG
CONTAINER_NAME=test-exporter
```

### 2. Test Configuration Validator

```bash
# Make validator executable
chmod +x docker/config-validator.sh

# Test with valid config
source test.env
./docker/config-validator.sh

# Test with missing required vars
unset CONFLUENCE_URL
./docker/config-validator.sh  # Should show errors
```

### 3. Test Docker Container with Environment

```bash
# Build updated image
docker build -t confluence-exporter:env-config .

# Test with missing environment (should fail gracefully)
docker run --rm confluence-exporter:env-config

# Test with test environment
docker run --rm --env-file test.env confluence-exporter:env-config
```

### 4. Test Environment Variable Loading

Create `test_phase_b.py`:

```python
import subprocess
import tempfile
import os

def test_environment_configuration():
    """Test Phase B - Environment Configuration."""
    
    print("🧪 Testing Phase B: Environment Configuration")
    print("=" * 50)
    
    # Create test environment file
    test_env_content = """
CONFLUENCE_URL=https://test.atlassian.net
CONFLUENCE_USERNAME=test@example.com
CONFLUENCE_API_TOKEN=test-token-123
CQL_QUERY=space = MFS
CRON_SCHEDULE=0 2 * * *
EXPORT_PATH=/app/exports
MAX_RESULTS=50
LOG_LEVEL=DEBUG
CONTAINER_NAME=test-exporter
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(test_env_content)
        test_env_file = f.name
    
    try:
        tests = [
            ("Build image with env config", "docker build -t confluence-exporter:env-config ."),
            ("Test config validator", f"bash docker/config-validator.sh"),
            ("Test container with env file", f"docker run --rm --env-file {test_env_file} confluence-exporter:env-config echo 'Env test complete'"),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, command in tests:
            print(f"\n🔄 Running: {test_name}")
            
            if "config-validator" in command:
                # Source env file for validator test
                env = os.environ.copy()
                with open(test_env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env[key] = value
                
                result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"   Error: {result.stderr}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        
        return failed == 0
        
    finally:
        os.unlink(test_env_file)

if __name__ == "__main__":
    import sys
    success = test_environment_configuration()
    sys.exit(0 if success else 1)
```

Run: `python test_phase_b.py`

## Expected Results After Phase B

1. ✅ Environment variables are validated on container start
2. ✅ Required variables cause graceful failure with helpful messages
3. ✅ Confluence configuration is automatically set up
4. ✅ Connection to Confluence is tested before proceeding
5. ✅ Export directory is created and validated
6. ✅ Configuration validator works independently
7. ✅ Default values are applied for optional settings
8. ✅ Cron schedule format is validated

## Troubleshooting Phase B

### Common Issues

**Issue**: Container exits with "Missing required environment variables"  
**Solution**: 
```bash
# Check which variables are missing
docker run --rm confluence-exporter:env-config
# Set all required variables in .env file
```

**Issue**: Confluence connection test fails  
**Solution**: 
```bash
# Test credentials manually
confluence-markdown-exporter search "type = page" ./test --limit 1
# Check URL format and credentials
```

**Issue**: Configuration file not created  
**Solution**: 
```bash
# Check permissions and directory creation
docker run -it --rm --env-file .env confluence-exporter:env-config bash
ls -la /root/.config/confluence-markdown-exporter/
```

## Next Steps

Once Phase B is complete and all tests pass:
1. Environment configuration is robust and validated
2. Confluence credentials are properly set up
3. Container fails gracefully with helpful error messages
4. Ready to proceed to Phase C for cron integration

Phase B ensures reliable configuration management for the automated export service.
