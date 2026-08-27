#!/usr/bin/env bash

set -e

echo "Uninstalling ChatGPT Local..."

# 1. Remove global symlink
if [ -L "/usr/local/bin/gpt" ]; then
    echo "Removing global 'gpt' command..."
    sudo rm /usr/local/bin/gpt
fi

# 2. Remove virtual env
if [ -d ".venv" ]; then
    echo "Removing virtual environment..."
    rm -rf .venv
fi

echo ""
echo "Uninstallation complete."
echo "Note: Your history and prompts in ~/.chatgpt-local were NOT deleted."
