#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ankLIENT Codespace Setup Script
# Runs automatically after Codespace is created (postCreateCommand)
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "=============================="
echo "  ankLIENT Cloud Setup"
echo "=============================="

# ── 1. System dependencies ────────────────────────────────────────────────────
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    chromium \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    unzip \
    curl

echo "[1/6] Done."

# ── 2. Python dependencies ────────────────────────────────────────────────────
echo "[2/6] Installing Python dependencies..."
pip install --quiet -r requirements.txt
echo "[2/6] Done."

# ── 3. Create ankLIENT config directory ──────────────────────────────────────
echo "[3/6] Setting up config directory..."
mkdir -p ~/.anklient/chrome-profile
mkdir -p ~/.anklient

# ── 4. Write cloud config.json ────────────────────────────────────────────────
echo "[4/6] Writing cloud config.json..."
cat > ~/.anklient/config.json << 'CONFIG'
{
    "chrome": {
        "chrome_path": "/usr/bin/chromium",
        "user_data_dir": "/home/vscode/.anklient/chrome-profile",
        "cdp_port": 9222,
        "headless": true,
        "restart_on_crash": true,
        "extra_args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-setuid-sandbox",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding"
        ]
    },
    "server": {
        "port": 8080,
        "host": "0.0.0.0",
        "api_keys": [],
        "request_timeout": 120
    },
    "chatgpt": {
        "default_model": "auto",
        "tab_mode": "owned",
        "parallel_tabs": false
    },
    "log": {
        "level": "INFO"
    }
}
CONFIG
echo "[4/6] Done."

# ── 5. Make scripts executable ────────────────────────────────────────────────
echo "[5/6] Making scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true
echo "[5/6] Done."

# ── 6. Final summary ─────────────────────────────────────────────────────────
echo "[6/6] Setup complete!"
echo ""
echo "=============================="
echo "  Next Steps:"
echo "=============================="
echo ""
echo "  STEP 1 - One-time ChatGPT login:"
echo "    bash scripts/login.sh"
echo "    → Opens noVNC in browser"
echo "    → Log into ChatGPT manually"
echo "    → Run: bash scripts/save-login.sh"
echo ""
echo "  STEP 2 - Start ankLIENT daemon:"
echo "    bash scripts/start.sh"
echo ""
echo "  STEP 3 - Test from anywhere:"
echo "    curl https://<codespace-url>-8080.app.github.dev/health"
echo ""
echo "=============================="
