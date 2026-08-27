#!/usr/bin/env bash

set -e

echo "Installing ChatGPT Local..."

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not found."
    exit 1
fi

# 2. Virtual environment
echo "Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# 3. Dependencies
echo "Installing dependencies..."
pip install playwright rich prompt_toolkit tomli
playwright install chromium

# 4. Create wrapper symlink
if [ -d "/usr/local/bin" ]; then
    echo "Creating global 'gpt' command..."
    sudo ln -sf "$(pwd)/chatgpt-local" /usr/local/bin/gpt
else
    echo "Please add $(pwd) to your PATH or alias gpt to chatgpt-local manually."
fi

echo ""
echo "Installation complete!"
echo "You can now run: gpt"
