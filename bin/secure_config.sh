#!/bin/bash
# Secure configuration file by setting proper permissions

CONFIG_PATH=$(python3 -c "
from confluence_markdown_exporter.utils.app_data_store import get_app_config_path
print(get_app_config_path())
")

# Ensure only the user can read/write the config file
chmod 600 "$CONFIG_PATH"

# Ensure the directory is only accessible to the user
chmod 700 "$(dirname "$CONFIG_PATH")"

echo "Configuration file secured with proper permissions."