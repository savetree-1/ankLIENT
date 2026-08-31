#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# test-api.sh — Quick test to verify ankLIENT API is responding
# ─────────────────────────────────────────────────────────────────────────────

API_URL="${1:-http://localhost:8080}"

echo "=============================="
echo "  ankLIENT API Test"
echo "  Target: $API_URL"
echo "=============================="
echo ""

# ── Health check ──────────────────────────────────────────────────────────────
echo "[1] Health check..."
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
echo ""

# ── Models list ───────────────────────────────────────────────────────────────
echo "[2] Models list..."
curl -s "$API_URL/v1/models" | python3 -m json.tool 2>/dev/null
echo ""

# ── Simple chat ───────────────────────────────────────────────────────────────
echo "[3] Simple chat test..."
curl -s "$API_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Reply with only: ankLIENT cloud is working!"}],
        "stream": false
    }' | python3 -m json.tool 2>/dev/null
echo ""

echo "=============================="
echo "  Test complete!"
echo "=============================="
