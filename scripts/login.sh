#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# login.sh — One-time ChatGPT login via noVNC browser window
# Run this ONCE to authenticate ChatGPT in the cloud browser.
# After login, the session is saved to the persistent chrome-profile.
# ─────────────────────────────────────────────────────────────────────────────

set -e

PROFILE_DIR="$HOME/.anklient/chrome-profile"
DISPLAY_NUM=99
VNC_PORT=5900
NOVNC_PORT=6080
CDP_PORT=9222

echo "=============================="
echo "  ankLIENT One-Time Login"
echo "=============================="
echo ""

# ── Kill any existing processes ───────────────────────────────────────────────
echo "Cleaning up old processes..."
pkill -f "chromium" 2>/dev/null || true
pkill -f "Xvfb :$DISPLAY_NUM" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true
pkill -f "websockify" 2>/dev/null || true
sleep 1

# ── Start virtual display ─────────────────────────────────────────────────────
echo "Starting virtual display..."
Xvfb :$DISPLAY_NUM -screen 0 1280x800x24 &
XVFB_PID=$!
export DISPLAY=:$DISPLAY_NUM
sleep 2

# ── Start Chrome (visible, not headless) with persistent profile ──────────────
echo "Starting Chrome with persistent profile..."
chromium \
    --display=:$DISPLAY_NUM \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --remote-debugging-port=$CDP_PORT \
    --user-data-dir="$PROFILE_DIR" \
    --window-size=1280,800 \
    "https://chatgpt.com" &
CHROME_PID=$!
sleep 3

# ── Start VNC server ──────────────────────────────────────────────────────────
echo "Starting VNC server..."
x11vnc \
    -display :$DISPLAY_NUM \
    -nopw \
    -listen localhost \
    -rfbport $VNC_PORT \
    -forever \
    -quiet &
VNC_PID=$!
sleep 1

# ── Start noVNC (web-based VNC) ───────────────────────────────────────────────
echo "Starting noVNC on port $NOVNC_PORT..."
websockify \
    --web /usr/share/novnc \
    $NOVNC_PORT \
    localhost:$VNC_PORT &
NOVNC_PID=$!
sleep 2

# ── Print instructions ────────────────────────────────────────────────────────
echo ""
echo "=============================="
echo "  Browser is now running!"
echo "=============================="
echo ""
echo "  Open this in your browser:"
echo "  → Codespace will show port 6080 as a forwarded port"
echo "  → Click 'Open in Browser' for port 6080"
echo "  → OR manually open the noVNC URL from the Ports tab"
echo ""
echo "  In the browser window you will see Chrome open with ChatGPT."
echo "  LOG IN to ChatGPT manually."
echo ""
echo "  When login is complete, come back here and press ENTER."
echo ""
read -p "  Press ENTER after you have logged into ChatGPT..."

# ── Save session and shut down visible Chrome ─────────────────────────────────
echo ""
echo "Saving session and switching to headless mode..."
kill $CHROME_PID 2>/dev/null || true
kill $VNC_PID 2>/dev/null || true
kill $NOVNC_PID 2>/dev/null || true
kill $XVFB_PID 2>/dev/null || true
sleep 2

echo ""
echo "=============================="
echo "  Login saved successfully!"
echo "=============================="
echo ""
echo "  Your ChatGPT session is now stored in:"
echo "  $PROFILE_DIR"
echo ""
echo "  Now run: bash scripts/start.sh"
echo ""
