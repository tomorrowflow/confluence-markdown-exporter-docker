# Phase D: Docker Compose & Testing

## Objective
Create production-ready Docker Compose configuration, implement volume mounting, and establish comprehensive testing procedures for the complete confluence export automation.

## Prerequisites
- Phases A, B, and C completed successfully
- Cron integration working
- Export functionality tested

## Files to Create

### 1. `docker-compose.yml`

**Action**: Create main Docker Compose file for production deployment.

**Location**: `./docker-compose.yml`

**Code to Add**:

```yaml
version: '3.8'

services:
  confluence-exporter:
    build: .
    image: confluence-exporter:latest
    container_name: ${CONTAINER_NAME:-confluence-exporter}
    restart: unless-stopped
    
    environment:
      # Required Confluence configuration
      - CONFLUENCE_URL=${CONFLUENCE_URL}
      - CONFLUENCE_USERNAME=${CONFLUENCE_USERNAME}
      - CONFLUENCE_API_TOKEN=${CONFLUENCE_API_TOKEN}
      
      # Export configuration
      - CQL_QUERY=${CQL_QUERY:-space = MFS}
      - CRON_SCHEDULE=${CRON_SCHEDULE:-0 2 * * *}
      - EXPORT_PATH=${EXPORT_PATH:-/app/exports}
      - MAX_RESULTS=${MAX_RESULTS:-100}
      
      # Container configuration
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - CONTAINER_NAME=${CONTAINER_NAME:-confluence-exporter}
    
    volumes:
      # Export directory - persist exports outside container
      - ./exports:/app/exports
      
      # Log directory - persist logs outside container
      - ./logs:/var/log/confluence-exporter
      
      # Optional: Custom configuration
      # - ./config:/root/.config/confluence-markdown-exporter
    
    # Health check
    healthcheck:
      test: ["/app/docker/healthcheck.sh"]
      interval: 5m
      timeout: 30s
      retries: 3
      start_period: 1m
    
    # Resource limits (optional)
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

  # Optional: Log monitoring with simple web interface
  log-viewer:
    image: nginx:alpine
    container_name: ${CONTAINER_NAME:-confluence-exporter}-logs
    restart: unless-stopped
    profiles:
      - monitoring
    
    ports:
      - "8080:80"
    
    volumes:
      - ./logs:/var/log/confluence-exporter:ro
      - ./docker/nginx-logs.conf:/etc/nginx/conf.d/default.conf:ro
    
    depends_on:
      - confluence-exporter

volumes:
  exports:
    driver: local
  logs:
    driver: local
```

### 2. `docker-compose.dev.yml`

**Action**: Create development/testing Docker Compose override.

**Location**: `./docker-compose.dev.yml`

**Code to Add**:

```yaml
version: '3.8'

services:
  confluence-exporter:
    # Override for development
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    
    environment:
      - LOG_LEVEL=DEBUG
      - CRON_SCHEDULE=*/2 * * * *  # Every 2 minutes for testing
      - MAX_RESULTS=5  # Limit results for testing
    
    volumes:
      # Mount source code for development
      - .:/app
      - ./dev-exports:/app/exports
      - ./dev-logs:/var/log/confluence-exporter
    
    # Override health check for faster feedback
    healthcheck:
      interval: 30s
      timeout: 10s
      retries: 2
      start_period: 10s

  # Development log viewer - always enabled
  log-viewer:
    profiles: []  # Remove profile restriction for dev
    ports:
      - "8081:80"  # Different port for dev
```

### 3. `docker/nginx-logs.conf`

**Action**: Create nginx configuration for log viewing.

**Location**: `./docker/nginx-logs.conf`

**Code to Add**:

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /var/log/confluence-exporter;
    index index.html;
    
    # Enable directory browsing
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Serve log files with proper content type
    location ~ \.log$ {
        add_header Content-Type text/plain;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
```

### 4. `.env.production`

**Action**: Create production environment template.

**Location**: `./.env.production`

**Code to Add**:

```bash
# Production Environment Configuration for Confluence Markdown Exporter
# Copy this file to .env and configure your production values

# ============================================================================
# REQUIRED PRODUCTION CONFIGURATION
# ============================================================================

# Confluence instance URL
CONFLUENCE_URL=https://your-company.atlassian.net

# Confluence credentials (use API token, not password)
CONFLUENCE_USERNAME=your-service-account@company.com
CONFLUENCE_API_TOKEN=your-production-api-token

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

# CQL query for production exports
# Examples for production use:
#   space = DOCS                                           # All DOCS space pages
#   space in (DOCS, API, GUIDES)                          # Multiple spaces
#   space = DOCS AND lastModified >= startOfWeek()        # Recent updates only
#   label = publish AND space in (DOCS, API)              # Published content only
CQL_QUERY=space = MFS

# Production cron schedule
# Examples:
#   0 2 * * *        # Daily at 2 AM (recommended)
#   0 2 * * 1        # Weekly on Monday at 2 AM
#   0 1,13 * * *     # Twice daily at 1 AM and 1 PM
#   0 2 1 * *        # Monthly on the 1st at 2 AM
CRON_SCHEDULE=0 2 * * *

# Maximum pages to export (set appropriate limit for your use case)
MAX_RESULTS=500

# ============================================================================
# OPERATIONAL CONFIGURATION
# ============================================================================

# Container name for identification
CONTAINER_NAME=confluence-exporter-prod

# Logging level for production
LOG_LEVEL=INFO

# Export and log paths (relative to docker-compose.yml location)
EXPORT_PATH=/app/exports

# ============================================================================
# OPTIONAL CONFIGURATION
# ============================================================================

# Uncomment to enable log monitoring web interface
# COMPOSE_PROFILES=monitoring

# Uncomment to customize resource limits in docker-compose.yml
# MEMORY_LIMIT=1G
# CPU_LIMIT=1.0
```

### 5. `scripts/deploy.sh`

**Action**: Create deployment script for production.

**Location**: `./scripts/deploy.sh`

**Code to Add**:

```bash
#!/bin/bash

# Production deployment script for Confluence Markdown Exporter
# Usage: ./scripts/deploy.sh [environment]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    esac
}

# Validate environment
validate_environment() {
    log INFO "🔍 Validating deployment environment: ${ENVIRONMENT}"
    
    # Check if .env file exists
    local env_file="${PROJECT_DIR}/.env"
    if [[ ! -f "$env_file" ]]; then
        log ERROR ".env file not found: $env_file"
        log ERROR "Copy .env.example or .env.production to .env and configure your settings"
        exit 1
    fi
    
    # Source environment file
    source "$env_file"
    
    # Check required variables
    local required_vars=("CONFLUENCE_URL" "CONFLUENCE_USERNAME" "CONFLUENCE_API_TOKEN")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -ne 0 ]]; then
        log ERROR "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log ERROR "  - $var"
        done
        exit 1
    fi
    
    log INFO "✅ Environment validation passed"
}

# Pre-deployment checks
pre_deployment_checks() {
    log INFO "🔧 Running pre-deployment checks..."
    
    # Check Docker is available
    if ! command -v docker &> /dev/null; then
        log ERROR "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        log ERROR "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to Docker daemon
    if ! docker info &> /dev/null; then
        log ERROR "Cannot connect to Docker daemon"
        exit 1
    fi
    
    log INFO "✅ Pre-deployment checks passed"
}

# Build and deploy
deploy() {
    log INFO "🚀 Starting deployment..."
    
    cd "$PROJECT_DIR"
    
    # Stop existing containers
    log INFO "Stopping existing containers..."
    docker-compose down || true
    
    # Build new image
    log INFO "Building Docker image..."
    docker-compose build --no-cache
    
    # Start services
    log INFO "Starting services..."
    if [[ "$ENVIRONMENT" == "development" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    else
        docker-compose up -d
    fi
    
    # Wait for health check
    log INFO "Waiting for services to become healthy..."
    local max_attempts=12
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose ps | grep -q "healthy\|Up"; then
            log INFO "✅ Services are running"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log ERROR "Services failed to start within timeout"
            log ERROR "Check logs: docker-compose logs"
            exit 1
        fi
        
        log INFO "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
        ((attempt++))
    done
}

# Post-deployment validation
post_deployment_validation() {
    log INFO "🧪 Running post-deployment validation..."
    
    # Check container status
    local container_status=$(docker-compose ps --services --filter "status=running" | wc -l)
    if [[ $container_status -eq 0 ]]; then
        log ERROR "No containers are running"
        exit 1
    fi
    
    # Check logs for errors
    log INFO "Checking recent logs for errors..."
    local error_count=$(docker-compose logs --tail=50 | grep -i error | wc -l)
    if [[ $error_count -gt 0 ]]; then
        log WARN "Found $error_count error messages in recent logs"
        log WARN "Review logs with: docker-compose logs"
    fi
    
    # Test cron job installation
    log INFO "Verifying cron job installation..."
    if docker-compose exec -T confluence-exporter crontab -l > /dev/null 2>&1; then
        log INFO "✅ Cron job is installed"
    else
        log ERROR "❌ Cron job is not installed"
        exit 1
    fi
    
    log INFO "✅ Post-deployment validation completed"
}

# Display deployment info
show_deployment_info() {
    log INFO "📊 Deployment Information"
    echo "=================================="
    
    source "${PROJECT_DIR}/.env"
    
    echo "Environment: $ENVIRONMENT"
    echo "Container Name: ${CONTAINER_NAME:-confluence-exporter}"
    echo "CQL Query: ${CQL_QUERY}"
    echo "Cron Schedule: ${CRON_SCHEDULE}"
    echo "Export Path: ./exports (host) -> ${EXPORT_PATH} (container)"
    echo "Logs Path: ./logs"
    
    if [[ "${COMPOSE_PROFILES:-}" == *"monitoring"* ]]; then
        echo "Log Viewer: http://localhost:8080"
    fi
    
    echo ""
    echo "Useful commands:"
    echo "  View logs:           docker-compose logs -f"
    echo "  Check status:        docker-compose ps"
    echo "  Stop services:       docker-compose down"
    echo "  Restart services:    docker-compose restart"
    echo "  Manual export:       docker-compose exec confluence-exporter /app/docker/export-runner.sh"
}

# Main execution
main() {
    log INFO "🐳 Confluence Markdown Exporter Deployment Script"
    log INFO "Environment: $ENVIRONMENT"
    
    validate_environment
    pre_deployment_checks
    deploy
    post_deployment_validation
    show_deployment_info
    
    log INFO "🎉 Deployment completed successfully!"
}

# Execute main function
main "$@"
```

### 6. `scripts/test-integration.sh`

**Action**: Create comprehensive integration test script.

**Location**: `./scripts/test-integration.sh`

**Code to Add**:

```bash
#!/bin/bash

# Integration testing script for Confluence Markdown Exporter Docker setup
# Usage: ./scripts/test-integration.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Test configuration
TEST_CONTAINER_NAME="confluence-exporter-integration-test"
TEST_EXPORT_DIR="$PROJECT_DIR/test-exports"
TEST_LOG_DIR="$PROJECT_DIR/test-logs"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local level=$1
    shift
    echo -e "[$(date '+%H:%M:%S')] [$level] $*"
}

cleanup() {
    log "INFO" "🧹 Cleaning up test environment..."
    docker-compose -p integration-test down -v --remove-orphans 2>/dev/null || true
    docker rm -f "$TEST_CONTAINER_NAME" 2>/dev/null || true
    rm -rf "$TEST_EXPORT_DIR" "$TEST_LOG_DIR"
}

# Trap cleanup on exit
trap cleanup EXIT

run_integration_tests() {
    log "INFO" "🧪 Starting Integration Tests"
    echo "=================================================="
    
    cd "$PROJECT_DIR"
    
    # Cleanup previous tests
    cleanup
    
    # Create test directories
    mkdir -p "$TEST_EXPORT_DIR" "$TEST_LOG_DIR"
    
    # Create test environment
    cat > .env.test << EOF
CONFLUENCE_URL=https://test.atlassian.net
CONFLUENCE_USERNAME=test@example.com
CONFLUENCE_API_TOKEN=test-token-12345
CQL_QUERY=type = page
CRON_SCHEDULE=*/1 * * * *
EXPORT_PATH=/app/exports
MAX_RESULTS=5
LOG_LEVEL=DEBUG
CONTAINER_NAME=$TEST_CONTAINER_NAME
EOF

    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Container Build
    log "INFO" "Test 1: Building Docker image..."
    if docker build -t confluence-exporter:integration-test . > /tmp/build.log 2>&1; then
        log "INFO" "✅ Docker image build: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Docker image build: FAILED"
        cat /tmp/build.log
        ((tests_failed++))
    fi
    
    # Test 2: Container Startup
    log "INFO" "Test 2: Testing container startup..."
    if docker run -d --name "$TEST_CONTAINER_NAME" --env-file .env.test \
        -v "$TEST_EXPORT_DIR:/app/exports" \
        -v "$TEST_LOG_DIR:/var/log/confluence-exporter" \
        confluence-exporter:integration-test > /dev/null 2>&1; then
        
        sleep 15  # Allow container to fully start
        
        if docker ps | grep -q "$TEST_CONTAINER_NAME"; then
            log "INFO" "✅ Container startup: PASSED"
            ((tests_passed++))
        else
            log "ERROR" "❌ Container startup: FAILED - Container not running"
            docker logs "$TEST_CONTAINER_NAME"
            ((tests_failed++))
        fi
    else
        log "ERROR" "❌ Container startup: FAILED - Could not start"
        ((tests_failed++))
    fi
    
    # Test 3: Environment Configuration
    log "INFO" "Test 3: Testing environment configuration..."
    if docker exec "$TEST_CONTAINER_NAME" printenv | grep -q "CONFLUENCE_URL=https://test.atlassian.net"; then
        log "INFO" "✅ Environment configuration: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Environment configuration: FAILED"
        ((tests_failed++))
    fi
    
    # Test 4: Cron Job Installation
    log "INFO" "Test 4: Testing cron job installation..."
    if docker exec "$TEST_CONTAINER_NAME" crontab -l | grep -q "export-runner.sh"; then
        log "INFO" "✅ Cron job installation: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Cron job installation: FAILED"
        docker exec "$TEST_CONTAINER_NAME" crontab -l || true
        ((tests_failed++))
    fi
    
    # Test 5: Script Executability
    log "INFO" "Test 5: Testing script executability..."
    if docker exec "$TEST_CONTAINER_NAME" test -x /app/docker/export-runner.sh; then
        log "INFO" "✅ Script executability: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Script executability: FAILED"
        ((tests_failed++))
    fi
    
    # Test 6: Log Directory Creation
    log "INFO" "Test 6: Testing log directory creation..."
    if docker exec "$TEST_CONTAINER_NAME" test -d /var/log/confluence-exporter; then
        log "INFO" "✅ Log directory creation: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Log directory creation: FAILED"
        ((tests_failed++))
    fi
    
    # Test 7: Export Directory Creation
    log "INFO" "Test 7: Testing export directory creation..."
    if docker exec "$TEST_CONTAINER_NAME" test -d /app/exports; then
        log "INFO" "✅ Export directory creation: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Export directory creation: FAILED"
        ((tests_failed++))
    fi
    
    # Test 8: Health Check
    log "INFO" "Test 8: Testing health check..."
    if docker exec "$TEST_CONTAINER_NAME" /app/docker/healthcheck.sh > /dev/null 2>&1; then
        log "INFO" "✅ Health check: PASSED"
        ((tests_passed++))
    else
        log "ERROR" "❌ Health check: FAILED"
        ((tests_failed++))
    fi
    
    # Test 9: Docker Compose (if real environment available)
    if [[ -f .env ]] && grep -q "atlassian.net" .env; then
        log "INFO" "Test 9: Testing Docker Compose with real environment..."
        if docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d > /dev/null 2>&1; then
            sleep 20
            if docker-compose ps | grep -q "Up"; then
                log "INFO" "✅ Docker Compose with real environment: PASSED"
                ((tests_passed++))
            else
                log "ERROR" "❌ Docker Compose with real environment: FAILED - Not running"
                docker-compose logs
                ((tests_failed++))
            fi
            docker-compose down > /dev/null 2>&1
        else
            log "ERROR" "❌ Docker Compose with real environment: FAILED - Startup error"
            ((tests_failed++))
        fi
    else
        log "INFO" "Test 9: Skipping Docker Compose test (no real environment configured)"
    fi
    
    # Show results
    echo ""
    echo "=================================================="
    log "INFO" "📊 Integration Test Results:"
    log "INFO" "  Tests Passed: $tests_passed"
    log "INFO" "  Tests Failed: $tests_failed"
    log "INFO" "  Total Tests:  $((tests_passed + tests_failed))"
    
    if [[ $tests_failed -eq 0 ]]; then
        log "INFO" "🎉 All integration tests passed!"
        return 0
    else
        log "ERROR" "💥 Some integration tests failed!"
        return 1
    fi
}

# Main execution
main() {
    log "INFO" "🚀 Confluence Markdown Exporter - Integration Testing"
    
    run_integration_tests
}

main "$@"
```

## Testing Phase D

### 1. Test Docker Compose Configuration

```bash
# Make scripts executable
chmod +x scripts/deploy.sh
chmod +x scripts/test-integration.sh

# Create test environment
cp .env.example .env.test
# Edit .env.test with test values

# Test development compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config
```

### 2. Run Integration Tests

```bash
# Run comprehensive integration tests
./scripts/test-integration.sh
```

### 3. Test Production Deployment

```bash
# Copy production template
cp .env.production .env
# Edit .env with your real Confluence credentials

# Run deployment script
./scripts/deploy.sh production
```

### 4. Test Volume Mounting

```bash
# Start with development compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Check volumes are mounted
docker-compose exec confluence-exporter ls -la /app/exports
docker-compose exec confluence-exporter ls -la /var/log/confluence-exporter

# Check host directories
ls -la exports/
ls -la logs/
```

### 5. Test Log Monitoring (Optional)

```bash
# Enable monitoring profile
echo "COMPOSE_PROFILES=monitoring" >> .env

# Start with monitoring
docker-compose up -d

# Access log viewer
curl http://localhost:8080
# Or open in browser: http://localhost:8080
```

## Expected Results After Phase D

1. ✅ Docker Compose starts all services successfully
2. ✅ Volume mounting works for exports and logs
3. ✅ Integration tests pass all checks
4. ✅ Production deployment script works
5. ✅ Log monitoring interface is accessible (if enabled)
6. ✅ Health checks work properly
7. ✅ Container restart policies function correctly
8. ✅ Resource limits are enforced

## Directory Structure After Phase D

```
confluence-markdown-exporter-docker/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .env.production
├── docker/
│   ├── nginx-logs.conf
│   ├── supervisord.conf
│   ├── entrypoint.sh
│   ├── export-runner.sh
│   └── healthcheck.sh
├── scripts/
│   ├── deploy.sh
│   └── test-integration.sh
├── exports/           # Created by compose (host directory)
├── logs/             # Created by compose (host directory) 
└── (existing files)
```

## Production Deployment

### Quick Start
```bash
# 1. Copy production environment template
cp .env.production .env

# 2. Configure your Confluence credentials
vim .env

# 3. Deploy
./scripts/deploy.sh production

# 4. Verify deployment
docker-compose ps
docker-compose logs -f
```

### Monitoring
```bash
# View real-time logs
docker-compose logs -f confluence-exporter

# Check export results
ls -la exports/

# Access log viewer (if monitoring enabled)
open http://localhost:8080
```

## Troubleshooting Phase D

### Common Issues

**Issue**: Docker Compose fails to start  
**Solution**: 
```bash
# Check configuration syntax
docker-compose config
# Check environment variables
docker-compose exec confluence-exporter printenv
```

**Issue**: Volumes not mounting  
**Solution**: 
```bash
# Check Docker daemon settings
docker info | grep "Docker Root Dir"
# Verify directory permissions
ls -la exports/ logs/
```

**Issue**: Integration tests fail  
**Solution**: 
```bash
# Run individual test components
docker build -t confluence-exporter:test .
docker run --rm confluence-exporter:test confluence-markdown-exporter --help
```

## Next Steps

Phase D completes the core Docker implementation. **Optional Phase E** adds production features like monitoring and cleanup automation, but Phase D provides a fully functional, production-ready confluence export automation system.

**You now have:**
- ✅ Complete Docker containerization
- ✅ Cron-based automation  
- ✅ Environment variable configuration
- ✅ Volume persistence
- ✅ Health monitoring
- ✅ Production deployment tools
- ✅ Comprehensive testing