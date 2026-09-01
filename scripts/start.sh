#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — Start ankLIENT daemon in headless cloud mode
# Requires: login.sh to have been run at least once first
# ─────────────────────────────────────────────────────────────────────────────

set -e

PROFILE_DIR="$HOME/.anklient/chrome-profile"
CDP_PORT=9222
API_PORT=8080

echo "=============================="
echo "  ankLIENT Cloud Daemon"
echo "=============================="
echo ""

# ── Check profile exists ──────────────────────────────────────────────────────
if [ ! -d "$PROFILE_DIR" ] || [ -z "$(ls -A $PROFILE_DIR 2>/dev/null)" ]; then
    echo "ERROR: No Chrome profile found."
    echo "Run login.sh first to authenticate ChatGPT."
    echo ""
    echo "  bash scripts/login.sh"
    exit 1
fi

# ── Kill any old Chrome/daemon ────────────────────────────────────────────────
echo "Cleaning up old processes..."
pkill -f "chromium.*remote-debugging-port=$CDP_PORT" 2>/dev/null || true
pkill -f "anklient" 2>/dev/null || true
sleep 1

# ── Start headless Chrome ─────────────────────────────────────────────────────
echo "Starting headless Chrome on CDP port $CDP_PORT..."
chromium \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-setuid-sandbox \
    --remote-debugging-port=$CDP_PORT \
    --remote-debugging-address=127.0.0.1 \
    --user-data-dir="$PROFILE_DIR" \
    --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.7922.173 Safari/537.36" \
    --disable-blink-features=AutomationControlled \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    "https://chatgpt.com" > /tmp/chrome.log 2>&1 &

CHROME_PID=$!
echo "Chrome PID: $CHROME_PID"

# ── Wait for Chrome CDP to be ready ──────────────────────────────────────────
echo "Waiting for Chrome to be ready..."
for i in $(seq 1 15); do
    if curl -s "http://127.0.0.1:$CDP_PORT/json/version" > /dev/null 2>&1; then
        echo "Chrome CDP ready."
        break
    fi
    sleep 1
done

# ── Start ankLIENT daemon ─────────────────────────────────────────────────────
echo ""
echo "Starting ankLIENT API daemon on port $API_PORT..."
echo ""

# Activate venv if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

python -m anklient.engine \
    --cdp-port $CDP_PORT \
    --port $API_PORT

