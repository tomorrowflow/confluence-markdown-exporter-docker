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