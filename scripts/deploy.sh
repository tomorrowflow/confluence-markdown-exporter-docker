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