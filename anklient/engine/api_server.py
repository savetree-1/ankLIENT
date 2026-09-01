"""OpenAI-compatible API server.

Endpoints:
  POST /v1/chat/completions  — chat (streaming + non-streaming)
  GET  /v1/models            — model catalog
  GET  /v1/projects          — ChatGPT projects
  GET  /health               — health + Chrome status
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid

from aiohttp import web

from .breakers import BreakerKind, BreakerRegistry, CircuitOpenError
from .cdp_driver import (
    AuthExpiredError,
    CDPDriver,
    GenerationStuckError,
    RateLimitError,
    is_rate_limited_text,
)
from .config import Config
from .cross_process_lock import LockAcquisitionError
from .lock_resolver import MutationLock, OwnedTabRequiredError, resolve_mutation_lock
from .resilience import retry_on_rate_limit

logger = logging.getLogger(__name__)

# Model mapping: user-facing names → ChatGPT web slugs
MODEL_MAP = {
    "gpt-5.5": "gpt-5-5",
    "gpt-5.5-thinking": "gpt-5-5-thinking",
    "gpt-5.3": "gpt-5-3",
    "gpt-5.2": "gpt-5-2",
    "gpt-5.1": "gpt-5-1",
    "gpt-5": "gpt-5",
    "gpt-5-mini": "gpt-5-mini",
    "gpt-5.3-mini": "gpt-5-3-mini",
    "auto": "auto",
    # Legacy aliases
    "gpt-4o": "auto",
    "gpt-4": "gpt-5",
    "gpt-3.5-turbo": "gpt-5-mini",
}


class APIServer:
    """OpenAI-compatible API backed by CDP automation."""

    def __init__(
        self, config: Config, driver: CDPDriver, breakers: BreakerRegistry | None = None
    ) -> None:
        self._config = config
        self._driver = driver
        self._cdp_port = config.chrome.cdp_port
        self._parallel_tabs = config.chatgpt.parallel_tabs
        self._request_count = 0
        # Health telemetry (event-derived, not polled). These are the only
        # fields that make sense to cache: they mark WHEN something happened,
        # not whether something is alive right now (that's computed live in
        # _handle_health). Without last_successful_send_at, a zombie process
        # that never connected (cdp_connected=false, requests_served=0) looks
        # identical to a freshly-started healthy one — both report "waiting".
        self._started_at = time.time()
        self._last_error: str | None = None
        self._last_successful_send_at: float | None = None
        # Non-rate-limit breaker registry (Phase 4). Injected by Service so the
        # REST process shares one registry across Chrome + driver + server.
        # Default-constructed for back-compat with tests that don't pass one.
        self._breakers = breakers or BreakerRegistry()
        # Track last conversation for multi-turn continuity
        self._last_conv_id: str | None = None
        self._last_project_id: str | None = None

        self.app = web.Application(client_max_size=10 * 1024 * 1024)
        self.app.router.add_post("/v1/chat/completions", self._handle_chat)
        self.app.router.add_post("/chat/completions", self._handle_chat)
        self.app.router.add_get("/v1/models", self._handle_models)
        self.app.router.add_get("/v1/projects", self._handle_projects)
        self.app.router.add_get("/v1/memories", self._handle_memories)
        self.app.router.add_get("/v1/chatgpt/usage", self._handle_usage)
        self.app.router.add_post("/v1/chatgpt/vision", self._handle_vision)
        self.app.router.add_post("/v1/chatgpt/research", self._handle_research)
        self.app.router.add_get(
            "/v1/chatgpt/files/{file_id}/download", self._handle_file_download
        )
        self.app.router.add_post("/v1/images/edits", self._handle_image_edit)
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/", self._handle_health)
        self.app.router.add_get("/chat", self._handle_ui)
        self.app.router.add_get("/assets/{filename}", self._handle_static)

    async def _handle_ui(self, request: web.Request) -> web.Response:
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ankLIENT</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: "Josefin Sans", system-ui, sans-serif;
            background: url("/assets/chat_bg.png") center/cover no-repeat fixed;
            height: 100dvh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Full dark overlay so bg is visible but not blinding */
        body::before {
            content: "";
            position: fixed; inset: 0;
            background: rgba(0,0,0,0.45);
            z-index: 0;
        }

        header {
            position: relative; z-index: 10;
            display: flex; align-items: center; justify-content: space-between;
            padding: 14px 22px;
            background: rgba(0,0,0,0.55);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .logo { font-weight: 700; font-size: 1.05rem; letter-spacing: 2px; color: #fff; text-transform: uppercase; }
        .logo span { color: #19c37d; }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: #19c37d; box-shadow: 0 0 8px #19c37d; }

        #chat {
            position: relative; z-index: 5;
            flex: 1; overflow-y: auto;
            padding: 24px 16px 10px;
            display: flex; flex-direction: column; gap: 18px;
            scroll-behavior: smooth;
        }
        #chat::-webkit-scrollbar { width: 5px; }
        #chat::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }

        .welcome {
            margin: auto; text-align: center; padding: 30px 20px;
        }
        .welcome h2 {
            font-size: 2rem; font-weight: 700; letter-spacing: 3px;
            color: #fff; text-transform: uppercase; margin-bottom: 10px;
            text-shadow: 0 2px 20px rgba(0,0,0,0.8);
        }
        .welcome p { color: rgba(255,255,255,0.6); font-size: 0.9rem; letter-spacing: 1px; }

        .row { display: flex; gap: 10px; align-items: flex-end; max-width: 760px; width: 100%; margin: 0 auto; }
        .row.user { flex-direction: row-reverse; }

        .avatar {
            width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 700; letter-spacing: 1px;
        }
        .avatar.ai { background: #19c37d; color: #000; }
        .avatar.user { background: rgba(255,255,255,0.2); color: #fff; border: 1px solid rgba(255,255,255,0.3); }

        .bubble {
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.6;
            max-width: calc(100% - 46px);
            word-break: break-word;
            font-size: 0.95rem;
        }
        .row.user .bubble {
            background: rgba(25, 195, 125, 0.2);
            border: 1px solid rgba(25, 195, 125, 0.4);
            border-bottom-right-radius: 4px;
            color: #fff;
            backdrop-filter: blur(10px);
        }
        .row.ai .bubble {
            background: rgba(0, 0, 0, 0.55);
            border: 1px solid rgba(255,255,255,0.1);
            border-bottom-left-radius: 4px;
            color: #ececec;
            backdrop-filter: blur(10px);
        }

        .bubble p { margin: 0 0 10px; } .bubble p:last-child { margin: 0; }
        .bubble h1,.bubble h2,.bubble h3 { margin: 12px 0 6px; color: #fff; font-family: "Josefin Sans", sans-serif; }
        .bubble ul,.bubble ol { padding-left: 20px; margin: 6px 0; }
        .bubble li { margin: 3px 0; }
        .bubble code { background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-size: 0.85em; font-family: monospace; }
        .bubble pre { background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; overflow-x: auto; margin: 8px 0; }
        .bubble pre code { background: none; padding: 0; }
        .bubble strong { color: #fff; }
        .bubble a { color: #19c37d; }

        .typing { display: inline-flex; gap: 5px; padding: 4px 0; }
        .typing span { width: 6px; height: 6px; background: rgba(255,255,255,0.5); border-radius: 50%; animation: blink 1.3s infinite both; }
        .typing span:nth-child(2) { animation-delay: .2s; } .typing span:nth-child(3) { animation-delay: .4s; }
        @keyframes blink { 0%,80%,100%{opacity:.15} 40%{opacity:1} }

        .input-wrap {
            position: relative; z-index: 10;
            padding: 12px 16px 18px;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(16px);
            border-top: 1px solid rgba(255,255,255,0.08);
        }
        .input-box {
            max-width: 760px; margin: 0 auto;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 18px;
            display: flex; align-items: flex-end; gap: 10px; padding: 10px 14px;
            transition: border-color .2s;
        }
        .input-box:focus-within { border-color: rgba(25,195,125,0.7); }
        textarea {
            flex: 1; background: none; border: none; outline: none;
            color: #fff; font-size: 15px; resize: none; max-height: 160px;
            line-height: 1.5; font-family: "Josefin Sans", sans-serif;
        }
        textarea::placeholder { color: rgba(255,255,255,0.35); }
        .send-btn {
            width: 36px; height: 36px; border-radius: 50%; border: none;
            background: #19c37d; color: #000; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0; font-size: 15px; font-weight: 700;
            transition: opacity .2s, transform .15s;
        }
        .send-btn:disabled { opacity: 0.35; cursor: default; }
        .send-btn:hover:not(:disabled) { opacity: 0.85; transform: scale(1.06); }
        .hint { max-width: 760px; margin: 7px auto 0; text-align: center; font-size: 10px; color: rgba(255,255,255,0.3); letter-spacing: 0.5px; }
    </style>
</head>
<body>
    <header>
        <div class="logo">ank<span>LIENT</span></div>
        <div class="dot" id="dot"></div>
    </header>

    <div id="chat">
        <div class="welcome" id="welcome">
            <h2>What can I help with?</h2>
            <p>Your personal ChatGPT cloud API &mdash; powered by ankLIENT</p>
        </div>
    </div>

    <div class="input-wrap">
        <div class="input-box">
            <textarea id="prompt" rows="1" placeholder="Message ChatGPT..." autocomplete="off"></textarea>
            <button class="send-btn" id="sendBtn" title="Send">&#9650;</button>
        </div>
        <p class="hint">ankLIENT may produce inaccurate information &mdash; verify important facts</p>
    </div>

<script>
    // Minimal safe markdown parser (no CDN dependency)
    function parseMarkdown(text) {
        return text
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            // code blocks
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // bold
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // italic
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // headers
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            // unordered list
            .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>')
            .replace(/\n/g, '<br>');
    }

    const chatEl = document.getElementById('chat');
    const promptEl = document.getElementById('prompt');
    const sendBtn = document.getElementById('sendBtn');
    let messages = [];
    let isSending = false;

    promptEl.addEventListener('input', () => {
        promptEl.style.height = 'auto';
        promptEl.style.height = Math.min(promptEl.scrollHeight, 160) + 'px';
    });
    promptEl.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    sendBtn.addEventListener('click', send);

    async function send() {
        if (isSending) return;
        const text = promptEl.value.trim();
        if (!text) return;

        document.getElementById('welcome')?.remove();

        isSending = true;
        sendBtn.disabled = true;
        promptEl.value = '';
        promptEl.style.height = 'auto';

        messages.push({ role: 'user', content: text });
        addBubble(text, 'user');

        const aiRow = createRow('ai');
        const bubbleEl = aiRow.querySelector('.bubble');
        bubbleEl.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
        chatEl.appendChild(aiRow);
        scroll();

        let fullContent = '';

        try {
            const resp = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: 'auto', messages: messages, stream: true })
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let done = false;
            let streamStarted = false;

            while (!done) {
                const { value, done: d } = await reader.read();
                done = d;
                if (value) buffer += decoder.decode(value, { stream: true });

                let idx;
                while ((idx = buffer.indexOf('\n')) !== -1) {
                    const line = buffer.slice(0, idx).trimEnd();
                    buffer = buffer.slice(idx + 1);
                    if (!line.startsWith('data: ')) continue;
                    const payload = line.slice(6).trim();
                    if (payload === '[DONE]') { done = true; break; }
                    try {
                        const delta = JSON.parse(payload)?.choices?.[0]?.delta?.content;
                        if (delta) {
                            if (!streamStarted) { bubbleEl.innerHTML = ''; streamStarted = true; }
                            fullContent += delta;
                            bubbleEl.innerHTML = parseMarkdown(fullContent);
                            scroll();
                        }
                    } catch(_) {}
                }
            }

            if (!fullContent) {
                bubbleEl.innerHTML = '<em style="opacity:.5">No response received.</em>';
            }
            messages.push({ role: 'assistant', content: fullContent });

        } catch(err) {
            bubbleEl.innerHTML = '<span style="color:#ff6b6b">\u26a0 ' + err.message + '</span>';
        } finally {
            isSending = false;
            sendBtn.disabled = false;
            promptEl.disabled = false;
            promptEl.focus();
            scroll();
        }
    }

    function createRow(role) {
        const row = document.createElement('div');
        row.className = 'row ' + role;
        const label = role === 'user' ? 'U' : 'A';
        row.innerHTML = \`<div class="avatar \${role}">\${label}</div><div class="bubble"></div>\`;
        return row;
    }
    function addBubble(text, role) {
        const row = createRow(role);
        row.querySelector('.bubble').innerHTML = role === 'user'
            ? text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            : parseMarkdown(text);
        chatEl.appendChild(row);
        scroll();
    }
    function scroll() { chatEl.scrollTop = chatEl.scrollHeight; }

    fetch('/health').then(r=>r.json()).then(d=>{
        const dot = document.getElementById('dot');
        const ok = d.status === 'healthy';
        dot.style.background = ok ? '#19c37d' : '#f59e0b';
        dot.style.boxShadow = '0 0 8px ' + (ok ? '#19c37d' : '#f59e0b');
    }).catch(()=>{
        const dot = document.getElementById('dot');
        dot.style.background = '#ef4444';
        dot.style.boxShadow = '0 0 8px #ef4444';
    });
</script>
</body>
</html>"""
        return web.Response(text=html, content_type="text/html")

    async def _handle_static(self, request: web.Request) -> web.Response:
        """Serve static assets (images etc.) from the assets/ directory."""
        import pathlib, mimetypes
        filename = request.match_info.get("filename", "")
        # Security: no path traversal
        if ".." in filename or "/" in filename:
            raise web.HTTPForbidden()
        assets_dir = pathlib.Path(__file__).parent.parent.parent / "assets"
        file_path = assets_dir / filename
        if not file_path.exists():
            raise web.HTTPNotFound()
        mime, _ = mimetypes.guess_type(str(file_path))
        return web.Response(body=file_path.read_bytes(), content_type=mime or "application/octet-stream")
        # ── Auth ──────────────────────────────────────────────────

    def _check_auth(self, request: web.Request) -> web.Response | None:
        """Check API key if configured. Returns error response or None."""
        keys = self._config.server.api_keys
        if not keys:
            return None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            key = auth[7:]
        else:
            key = request.query.get("key", "")
        if key not in keys:
            return web.json_response(
                {"error": {"message": "Invalid API key", "type": "auth_error"}},
                status=401,
            )
        return None

    # ── Handlers ──────────────────────────────────────────────

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Honest health endpoint — observes current reality, not a stale mirror.

        The old version returned ``"waiting"`` when CDP was disconnected, which
        is indistinguishable from "freshly started, connecting now" — a zombie
        process (HTTP listener up, CDP never connected) reported the same
        status as a healthy one. This version distinguishes four states:

        - ``starting``: listener up, driver not yet connected, never served
        - ``healthy``: Chrome alive AND driver connected
        - ``degraded``: Chrome alive but driver disconnected (zombie/recovering)
        - ``broken``: Chrome itself unreachable

        Live fields (chrome_running, driver_connected) are computed fresh on
        each call — /health is infrequent (supervisor poll), and cached state
        would lag reality. Event-derived fields (started_at, last_error,
        last_successful_send_at, requests_served) are tracked on the instance.
        """
        import urllib.request

        driver_connected = bool(self._driver.is_connected)

        # Chrome liveness: cheap HTTP GET to /json/version. If Chrome is dead,
        # this fails fast (connection refused). Run synchronously — /health is
        # infrequent and the call is sub-millisecond on loopback.
        chrome_running = False
        try:
            loop = asyncio.get_event_loop()

            def _probe():
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{self._cdp_port}/json/version", timeout=2
                    ) as r:
                        return r.status == 200
                except Exception:
                    return False

            chrome_running = await loop.run_in_executor(None, _probe)
        except Exception:
            chrome_running = False

        # Status logic — zombie case (Chrome up, driver dead) is "degraded",
        # never "ok"/"waiting". The old "waiting" non-answer is gone.
        if not chrome_running:
            status = "broken"
        elif not driver_connected:
            status = "degraded"
        elif self._last_successful_send_at is None and self._request_count == 0:
            status = "starting"
        else:
            status = "healthy"

        # An open breaker can only DOWNGRADE starting|healthy -> degraded. It
        # must never override "broken" (Chrome down is a harder failure than a
        # tripped circuit) and never force "broken" — auth_required is serious,
        # but "broken" invites a destructive supervisor restart, while
        # "degraded" correctly signals "up but refusing some/all traffic". A
        # disconnect-degraded stays degraded (not worse).
        if (
            status in ("starting", "healthy")
            and self._breakers.first_open() is not None
        ):
            status = "degraded"

        # Current-state summary, distinct from the historical/latching last_error.
        open_kinds = [k.value for k in BreakerKind if self._breakers.is_open(k)]

        return web.json_response(
            {
                "status": status,
                "chrome_running": chrome_running,
                "cdp_connected": driver_connected,
                "driver_connected": driver_connected,
                "requests_served": self._request_count,
                "started_at": self._started_at,
                "last_successful_send_at": self._last_successful_send_at,
                "last_error": self._last_error,
                "open_breakers": open_kinds,
                "breakers": self._breakers.snapshot(),
            }
        )

    async def _handle_models(self, request: web.Request) -> web.Response:
        if err := self._check_auth(request):
            return err
        try:
            raw = await self._driver.get_models()
        except Exception:
            raw = []

        models = []
        for m in raw:
            slug = m.get("slug", "")
            models.append(
                {
                    "id": slug,
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "chatgpt-web",
                }
            )

        if not models:
            for slug in ["auto", "gpt-5-5", "gpt-5-mini"]:
                models.append(
                    {
                        "id": slug,
                        "object": "model",
                        "created": 1700000000,
                        "owned_by": "chatgpt-web",
                    }
                )

        return web.json_response({"object": "list", "data": models})

    async def _handle_memories(self, request: web.Request) -> web.Response:
        if err := self._check_auth(request):
            return err
        try:
            memories = await self._driver.get_memories()
        except Exception as e:
            logger.error("Failed to get memories: %s", e)
            memories = []
        return web.json_response({"object": "list", "data": memories})

    async def _handle_projects(self, request: web.Request) -> web.Response:
        if err := self._check_auth(request):
            return err
        try:
            projects = await self._driver.get_projects()
        except Exception as e:
            logger.error("Failed to get projects: %s", e)
            projects = []
        return web.json_response({"object": "list", "data": projects})

    # ── New Backend API Endpoints (ported from chatgpt-api) ──────────

    async def _handle_usage(self, request: web.Request) -> web.Response:
        """GET /v1/chatgpt/usage — account limits and quota."""
        if err := self._check_auth(request):
            return err
        try:
            usage = await self._driver.api_get_account_usage()
            return web.json_response(usage)
        except Exception as e:
            logger.error("Failed to get account usage: %s", e)
            return web.json_response(
                {"error": {"message": str(e), "type": "server_error"}},
                status=500,
            )

    async def _handle_vision(self, request: web.Request) -> web.Response:
        """POST /v1/chatgpt/vision — upload image + ask ChatGPT to describe it.

        Expects JSON body: {"image": "<base64>", "prompt": "...", "mime_type": "image/png"}
        """
        if err := self._check_auth(request):
            return err
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": {"message": "Invalid JSON", "type": "invalid_request_error"}},
                status=400,
            )

        b64_image = body.get("image", "")
        prompt = body.get("prompt", "Describe this image.")
        mime_type = body.get("mime_type", "image/png")

        if not b64_image:
            return web.json_response(
                {
                    "error": {
                        "message": "Missing 'image' field (base64)",
                        "type": "invalid_request_error",
                    }
                },
                status=400,
            )

        try:
            upload = await self._driver.api_upload_image(b64_image, mime_type=mime_type)
            if not upload.get("success"):
                return web.json_response(
                    {
                        "error": {
                            "message": f"Upload failed: {upload.get('error')}",
                            "type": "server_error",
                        }
                    },
                    status=500,
                )

            text = await self._driver.api_send_vision_chat(
                prompt, upload["file_id"], upload["size"]
            )
            return web.json_response(
                {
                    "object": "chatgpt.vision",
                    "file_id": upload["file_id"],
                    "response": text,
                }
            )
        except Exception as e:
            logger.error("Vision request failed: %s", e)
            return web.json_response(
                {"error": {"message": str(e), "type": "server_error"}},
                status=500,
            )

    async def _handle_research(self, request: web.Request) -> web.Response:
        """POST /v1/chatgpt/research — run a Deep Research query.

        Expects JSON body: {"prompt": "...", "model": "o4-mini-deep-research"}
        """
        if err := self._check_auth(request):
            return err
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": {"message": "Invalid JSON", "type": "invalid_request_error"}},
                status=400,
            )

        prompt = body.get("prompt", "")
        model = body.get("model", "o4-mini-deep-research")

        if not prompt:
            return web.json_response(
                {
                    "error": {
                        "message": "Missing 'prompt' field",
                        "type": "invalid_request_error",
                    }
                },
                status=400,
            )

        try:
            report = await self._driver.api_deep_research(prompt, model=model)
            return web.json_response(
                {
                    "object": "chatgpt.research",
                    "report": report,
                }
            )
        except Exception as e:
            logger.error("Deep Research failed: %s", e)
            return web.json_response(
                {"error": {"message": str(e), "type": "server_error"}},
                status=500,
            )

    async def _handle_file_download(self, request: web.Request) -> web.Response:
        """GET /v1/chatgpt/files/{file_id}/download — get temp download URL."""
        if err := self._check_auth(request):
            return err
        file_id = request.match_info["file_id"]
        try:
            url = await self._driver.api_download_file(file_id)
            if url:
                return web.json_response({"download_url": url})
            return web.json_response(
                {
                    "error": {
                        "message": "File not found or download unavailable",
                        "type": "not_found",
                    }
                },
                status=404,
            )
        except Exception as e:
            logger.error("File download failed: %s", e)
            return web.json_response(
                {"error": {"message": str(e), "type": "server_error"}},
                status=500,
            )

    async def _handle_image_edit(self, request: web.Request) -> web.Response:
        """POST /v1/images/edits"""
        if err := self._check_auth(request):
            return err

        # We need to parse multipart/form-data for OpenAI compat
        try:
            reader = await request.multipart()
            prompt = "Edit the image"
            images = []

            async for field in reader:
                if field.name == "prompt":
                    prompt = await field.read(decode=True)
                    prompt = prompt.decode("utf-8")
                elif field.name in ("image", "mask"):
                    data = await field.read()
                    import base64

                    b64 = base64.b64encode(data).decode()
                    mime_type = field.headers.get("Content-Type", "image/png")

                    upload = await self._driver.api_upload_image(
                        b64, mime_type=mime_type
                    )
                    if upload.get("success"):
                        images.append(
                            {"file_id": upload["file_id"], "size": upload["size"]}
                        )

            if not images:
                return web.json_response(
                    {"error": {"message": "No image provided"}}, status=400
                )

            assets = await self._driver.api_image_edit(prompt, images)

            result = []
            for asset in assets:
                url = await self._driver.api_download_file(asset)
                if url:
                    result.append({"url": url})

            return web.json_response({"created": int(time.time()), "data": result})

        except Exception as e:
            logger.error("Image edit failed: %s", e)
            return web.json_response({"error": {"message": str(e)}}, status=500)

    async def _handle_chat(self, request: web.Request) -> web.Response:
        if err := self._check_auth(request):
            return err

        self._request_count += 1

        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": {"message": "Invalid JSON", "type": "invalid_request_error"}},
                status=400,
            )

        messages = body.get("messages", [])
        if not messages:
            return web.json_response(
                {
                    "error": {
                        "message": "No messages provided",
                        "type": "invalid_request_error",
                    }
                },
                status=400,
            )

        model = body.get("model", self._config.chatgpt.default_model)
        stream = body.get("stream", False)
        project_id = (
            body.get("project_id")
            or body.get("gizmo_id")
            or (body.get("metadata", {}) or {}).get("project_id")
            or self._config.chatgpt.default_project_id
        )
        conversation_id = body.get("conversation_id")

        # Build conversation text from all messages
        # Includes prior assistant context for stateless clients (OpenAI SDK)
        system_parts = []
        conversation_lines = []
        user_msg_count = 0
        MAX_HISTORY_TURNS = 10  # Cap to avoid textarea overflow

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            else:
                content = str(content)

            if role == "system":
                system_parts.append(content)
            elif role == "user":
                conversation_lines.append(f"[User]\n{content}")
                user_msg_count += 1
            elif role == "assistant":
                conversation_lines.append(f"[Assistant]\n{content}")

        # Trim to last N turns if too many messages
        if len(conversation_lines) > MAX_HISTORY_TURNS * 2:
            conversation_lines = conversation_lines[-(MAX_HISTORY_TURNS * 2) :]

        # Verify at least one user message exists
        if user_msg_count == 0:
            return web.json_response(
                {
                    "error": {
                        "message": "No user message",
                        "type": "invalid_request_error",
                    }
                },
                status=400,
            )

        # Compose final text
        prefix = ""
        if system_parts:
            prefix = "[System Instructions]\n" + "\n".join(system_parts) + "\n\n"
        full_text = prefix + "\n".join(conversation_lines)

        model_slug = MODEL_MAP.get(model, model)
        timeout = self._config.server.request_timeout

        logger.info(
            "Request #%d: model=%s->%s conv=%s project=%s stream=%s msg=%.60s",
            self._request_count,
            model,
            model_slug,
            conversation_id,
            project_id,
            stream,
            full_text,
        )

        # Serialize — cross-process lock so MCP + REST don't corrupt each other
        try:
            # Circuit-open fail-fast (Phase 4 PR2): refuse before touching Chrome
            # if a breaker is open. Placed inside the try so it flows through
            # the except below → _error_response + _last_error, consistent with
            # every other failure path. Checked before acquiring the lock so a
            # process that already knows it will refuse doesn't block on the
            # browser lock. If AUTH_EXPIRED is open, probes auth recovery first
            # (the user may have logged back in).
            await self._check_circuit_or_recover()

            # PR4/5: per-target lock in parallel mode (port-wide otherwise).
            # Resolver raises OwnedTabRequiredError (→ 503) if parallel mode
            # has no owned target rather than silently degrading to the port
            # lock (split-brain guard). When parallel mode is OFF, skip the
            # resolver entirely and use the cached port — preserves the exact
            # legacy path (the resolver would read driver.port, which is the
            # same value but needlessly couples the legacy path to the driver).
            if self._parallel_tabs:
                _port, _key = resolve_mutation_lock(self._driver, True)
            else:
                _port, _key = self._cdp_port, None
            async with MutationLock(_port, _key):
                # Drift guard (parallel mode only): if the owned target changed
                # while we waited for the lock, the key we hold no longer names
                # the active tab. Fail retryably instead of mutating under a
                # stale key.
                if self._parallel_tabs:
                    _, _current_key = resolve_mutation_lock(self._driver, True)
                    if _current_key != _key:
                        raise OwnedTabRequiredError(
                            "owned target changed while waiting for mutation lock"
                        )
                # Second circuit-open check, now that we hold the lock. A
                # concurrent request may have tripped a breaker while we were
                # waiting. Without this, we'd drive Chrome despite the process
                # already knowing the circuit is open.
                await self._check_circuit_or_recover()

                # Select model if specified (non-fatal on failure)
                if model_slug and model_slug != "auto":
                    selected = await self._driver.select_model(model_slug)
                    if not selected:
                        logger.warning(
                            "Could not select model '%s', proceeding with active model",
                            model_slug,
                        )

                # Decide: continue existing conversation or start fresh?
                if conversation_id:
                    # Explicit conversation_id from client — navigate to it
                    await self._driver.navigate_conversation(conversation_id)
                elif (
                    self._last_conv_id
                    and self._driver._current_conv_id == self._last_conv_id
                    and project_id == self._last_project_id
                    and not system_parts
                ):
                    # Same session, same project, no system prompt override — continue.
                    # Reconcile against the live tab before sending: another process
                    # sharing the Chrome tab may have navigated it since our last turn,
                    # which would leave _current_conv_id stale. ensure_current_conversation
                    # verifies location.href and navigates back if needed (fail-closed).
                    logger.info("Continuing conversation: %s", self._last_conv_id)
                    await self._driver.ensure_current_conversation(self._last_conv_id)
                else:
                    # Fresh chat
                    await self._driver.navigate_new_chat(gizmo_id=project_id)
                    self._last_project_id = project_id

                if stream:
                    return await self._stream_response(
                        request, model_slug, full_text, timeout
                    )
                else:
                    return await self._full_response(
                        request, model_slug, full_text, timeout
                    )

        except Exception as e:
            logger.error("Chat error: %s", e, exc_info=True)
            self._last_error = f"{type(e).__name__}: {e}"
            return self._error_response(e)

    async def _check_circuit_or_recover(self) -> None:
        """Fail-fast if a breaker is open, with one exception: if AUTH_EXPIRED
        is the open breaker, probe auth recovery first (the user may have logged
        back in via the browser since the trip). If recovery succeeds the breaker
        is reset and the request proceeds; if it fails, or if a non-auth breaker
        is open, raise CircuitOpenError.

        Called at each fail-fast checkpoint (pre-lock, post-lock, streaming
        pre-prepare). Does NOT drive a chat send — recovery is a lightweight
        ``/api/auth/session`` token fetch via ``driver.recover_auth()``.
        """
        open_kind = self._breakers.first_open()
        if open_kind is None:
            return
        if open_kind is BreakerKind.AUTH_EXPIRED:
            if await self._driver.recover_auth():
                # Auth restored — re-check in case another breaker is also open.
                open_kind = self._breakers.first_open()
                if open_kind is None:
                    return
        raise CircuitOpenError(open_kind)

    # ── Error mapping ─────────────────────────────────────────

    def _error_response(self, exc: Exception) -> web.Response:
        """Map a driver exception to an OpenAI-shaped error response.

        - RateLimitError → HTTP 429 with the canonical OpenAI
          ``rate_limit_exceeded`` type/code and a ``Retry-After`` header, so any
          OpenAI-aware agent framework (SDK, LangChain, LlamaIndex) automatically
          backs off and retries with zero client integration.
        - AuthExpiredError → HTTP 401 ``invalid_api_key`` — the ChatGPT session
          expired; previously this surfaced as silent empty data or a generic
          timeout.
        - GenerationStuckError → HTTP 504 ``generation_stuck`` — the generation
          stalled (no DOM progress within the stall window); the phase is in the
          message for diagnosis.
        - Everything else stays a 500 ``server_error`` (a real failure, not
          retriable).
        """
        if isinstance(exc, RateLimitError):
            retry_after = str(int(exc.retry_after))
            return web.json_response(
                {
                    "error": {
                        "message": str(exc),
                        "type": "rate_limit_exceeded",
                        "param": None,
                        "code": "rate_limit_exceeded",
                    }
                },
                status=429,
                headers={"Retry-After": retry_after},
            )
        if isinstance(exc, AuthExpiredError):
            return web.json_response(
                {
                    "error": {
                        "message": str(exc),
                        "type": "invalid_api_key",
                        "param": None,
                        "code": "invalid_api_key",
                    }
                },
                status=401,
            )
        if isinstance(exc, GenerationStuckError):
            return web.json_response(
                {
                    "error": {
                        "message": str(exc),
                        "type": "server_error",
                        "param": None,
                        "code": "generation_stuck",
                    }
                },
                status=504,
            )
        if isinstance(exc, LockAcquisitionError):
            return web.json_response(
                {
                    "error": {
                        "message": str(exc),
                        "type": "server_error",
                        "param": None,
                        "code": "lock_timeout",
                    }
                },
                status=503,
            )
        if isinstance(exc, CircuitOpenError):
            return web.json_response(
                {
                    "error": {
                        "message": (
                            f"Circuit open for {exc.kind.value} — cooling down. Retry later."
                        ),
                        "type": "server_error",
                        "param": None,
                        "code": "circuit_open",
                    }
                },
                status=503,
            )
        if isinstance(exc, OwnedTabRequiredError):
            return web.json_response(
                {
                    "error": {
                        "message": f"{exc}. Retry later.",
                        "type": "server_error",
                        "param": None,
                        "code": "owned_tab_required",
                    }
                },
                status=503,
            )
        return web.json_response(
            {"error": {"message": str(exc), "type": "server_error"}},
            status=500,
        )

    # ── Response formatters ───────────────────────────────────

    async def _full_response(
        self, request: web.Request, model: str, text: str, timeout: float
    ) -> web.Response:
        """Non-streaming: collect all chunks, return one JSON.

        The send is wrapped in ``retry_on_rate_limit`` so a transient
        ChatGPT "Too many requests" pop-up is dismissed and retried
        transparently — the client only sees it (as a 429) if the limit
        persists across all retries.
        """
        # P1: resolve model-aware detector budgets from config.
        from .completion_detector import DetectorBudgets

        budgets = DetectorBudgets.from_config(self._config.chatgpt, model)

        async def _send_and_collect() -> str:
            collected = ""
            async for chunk in self._driver.send_and_stream(
                text,
                timeout=timeout,
                budgets=budgets,
                model=model,
            ):
                collected += chunk.delta
            return collected

        full_text = await retry_on_rate_limit(self._driver, _send_and_collect)

        conv_id = self._driver._current_conv_id or ""
        self._last_conv_id = conv_id
        self._last_successful_send_at = time.time()

        return web.json_response(
            {
                "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "conversation_id": conv_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": full_text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }
        )

    async def _stream_response(
        self, request: web.Request, model: str, text: str, timeout: float
    ) -> web.Response:
        """Streaming: SSE chunks as they arrive.

        Rate-limit handling for streaming is split, because once
        ``resp.prepare()`` commits the HTTP 200 status we can no longer send a
        429:

        - **Pre-flight** (before prepare): a single DOM scan. If throttled, we
          retry transparently (dismiss + backoff). If it persists, we return a
          proper 429 here while the status is still changeable.
        - **Mid-stream** (after prepare): a throttle is rare here (pre-flight
          cleared it), but if one occurs it falls back to the inline
          ``[Error: ...]`` SSE chunk — documented as a known limitation.
        """
        # P1: resolve model-aware detector budgets from config.
        from .completion_detector import DetectorBudgets

        budgets = DetectorBudgets.from_config(self._config.chatgpt, model)

        async def _preflight() -> None:
            """Raise RateLimitError if the pop-up is present right now."""
            try:
                scan = await self._driver._js_strict(
                    "(function(){var t=(document.body&&document.body.innerText)||'';"
                    "return JSON.stringify({text:t.slice(0,4000)});})()",
                    timeout=10,
                )
            except Exception:
                # CDP/JS error during scan — assume no rate limit (proceed).
                return
            try:
                body = json.loads(scan).get("text", "") if scan else ""
            except (json.JSONDecodeError, TypeError):
                body = ""
            if is_rate_limited_text(body):
                raise RateLimitError.from_text(body)

        # Transparent pre-flight retry — dismisses the pop-up and retries so a
        # transient limit never reaches the client as an error.
        try:
            await retry_on_rate_limit(self._driver, _preflight, max_attempts=3)
        except RateLimitError:
            # Persistent at pre-flight: still pre-prepare, so send a clean 429.
            raise

        # Circuit-open fail-fast (Phase 4 PR2): final check, after rate-limit
        # preflight but still before prepare() commits HTTP 200. A breaker may
        # have opened during model selection/navigation. After prepare() no
        # status change is possible, so this must stay pre-prepare.
        await self._check_circuit_or_recover()

        resp = web.StreamResponse()
        resp.content_type = "text/event-stream"
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["Connection"] = "keep-alive"
        await resp.prepare(request)

        cid = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        created = int(time.time())

        # Role chunk
        await self._send_sse(
            resp,
            {
                "id": cid,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None,
                    }
                ],
            },
        )

        try:
            async for chunk in self._driver.send_and_stream(
                text,
                timeout=timeout,
                budgets=budgets,
                model=model,
            ):
                if chunk.delta:
                    await self._send_sse(
                        resp,
                        {
                            "id": cid,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": chunk.delta},
                                    "finish_reason": None,
                                }
                            ],
                        },
                    )
                if chunk.finish_reason:
                    conv_id = self._driver._current_conv_id or ""
                    self._last_conv_id = conv_id
                    if chunk.finish_reason == "stop":
                        self._last_successful_send_at = time.time()
                    await self._send_sse(
                        resp,
                        {
                            "id": cid,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "conversation_id": conv_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": chunk.finish_reason,
                                }
                            ],
                        },
                    )
        except RateLimitError as e:
            # Mid-stream throttle (rare after pre-flight). Status is locked at
            # 200, so we can't upgrade to 429; surface as an inline error chunk
            # with a recognizable marker so clients can detect it.
            logger.warning("Mid-stream rate limit: %s", e)
            await self._send_sse(
                resp,
                {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": f"\n\n[Error: rate_limit_exceeded — retry in {e.retry_after}s]"
                            },
                            "finish_reason": "error",
                        }
                    ],
                },
            )
        except AuthExpiredError:
            # Session expired mid-stream (status locked at 200). Surface with a
            # recognizable marker so clients can prompt re-login.
            logger.warning("Mid-stream auth expiry")
            await self._send_sse(
                resp,
                {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": "\n\n[Error: auth_expired — re-login required]"
                            },
                            "finish_reason": "error",
                        }
                    ],
                },
            )
        except GenerationStuckError as e:
            # Generation stalled mid-stream (status locked at 200). Surface the
            # phase + duration so the client can decide whether to retry.
            logger.warning("Mid-stream generation stuck: %s", e)
            await self._send_sse(
                resp,
                {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": f"\n\n[Error: generation_stuck — stalled in {e.phase} for {e.stalled_for_s:.0f}s]"
                            },
                            "finish_reason": "error",
                        }
                    ],
                },
            )
        except Exception as e:
            logger.error("Stream error: %s", e)
            await self._send_sse(
                resp,
                {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": f"\n\n[Error: {e}]"},
                            "finish_reason": "error",
                        }
                    ],
                },
            )

        await resp.write(b"data: [DONE]\n\n")
        await resp.write_eof()
        return resp

    @staticmethod
    async def _send_sse(resp: web.StreamResponse, data: dict) -> None:
        await resp.write(f"data: {json.dumps(data)}\n\n".encode())
