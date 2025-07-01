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