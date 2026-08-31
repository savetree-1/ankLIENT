# ankLIENT

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

**A local, OpenAI-compatible API daemon that bridges your authenticated ChatGPT Web session directly to your terminal and any API client.**

[Installation](#installation) · [Quick Start](#quick-start) · [API Reference](#api-reference) · [CLI Commands](#cli-usage-reference) · [Architecture](#architecture) · [Configuration](#configuration)

</div>

---

## What is ankLIENT?

ankLIENT is a modular, enterprise-grade background daemon that attaches to an authenticated ChatGPT Web browser session via the **Chrome DevTools Protocol (CDP)** and exposes all of its capabilities as a fully local, **OpenAI-compatible REST API** on `http://localhost:8080`.

This is not a simple web scraper. ankLIENT implements:
- **Direct backend API access**: It communicates directly with ChatGPT's private `backend-api` endpoints using your authenticated session token, bypassing the normal browser UI entirely.
- **Sentinel Proof-of-Work bypass**: It natively generates and solves OpenAI's Sentinel challenge tokens (`required`, `SHA-3` difficulty-based), allowing direct API calls without browser automation.
- **Full streaming support**: All chat completions are streamed via Server-Sent Events (SSE) in real-time, token by token, just like the official OpenAI API.
- **Advanced feature access**: Deep Research, DALL-E image generation, image editing/compositing, vision/OCR, and account usage monitoring — all capabilities that are not available on standard API plans.

The key insight: You pay for ChatGPT Plus/Pro. You already have access to these features. ankLIENT simply gives you a clean, programmatic interface to them.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [macOS / Linux](#macos--linux)
  - [Windows](#windows)
  - [Manual Setup](#manual-setup)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
  - [CDP Session Attachment](#cdp-session-attachment)
  - [Sentinel Proof-of-Work](#sentinel-proof-of-work)
  - [Asset Protocol Handling](#asset-protocol-handling)
- [API Reference](#api-reference)
  - [Chat Completions](#post-v1chatcompletions)
  - [Models](#get-v1models)
  - [Projects](#get-v1projects)
  - [Memories](#get-v1memories)
  - [Vision](#post-v1chatgptvision)
  - [Deep Research](#post-v1chatgptresearch)
  - [Image Edits](#post-v1imagesedits)
  - [File Download](#get-v1chatgptfilesfile_iddownload)
  - [Account Usage](#get-v1chatgptusage)
  - [Health Check](#get-health)
- [CLI Usage Reference](#cli-usage-reference)
  - [Interactive REPL Mode](#interactive-repl-mode)
  - [Slash Commands](#slash-commands)
- [Configuration](#configuration)
  - [Config File](#config-file)
  - [Chrome / CDP Settings](#chrome--cdp-settings)
  - [Server Settings](#server-settings)
  - [API Key Authentication](#api-key-authentication)
- [Architecture](#architecture)
  - [Directory Structure](#directory-structure)
  - [Engine Layer](#engine-layer)
  - [Circuit Breakers](#circuit-breakers)
  - [Multi-Tab Mode](#multi-tab-mode)
- [Cloud Deployment (Proof of Concept)](#cloud-deployment-proof-of-concept)
  - [Codespaces Testing Methodology](#codespaces-testing-methodology)
  - [Key Findings & Outcomes](#key-findings--outcomes)
  - [Next Steps (VPS Migration)](#next-steps-vps-migration)
- [Integrations](#integrations)
  - [Using with OpenAI SDK](#using-with-openai-sdk)
  - [Using with opencode](#using-with-opencode)
  - [Using with any HTTP client](#using-with-any-http-client)
- [Development & Contributing](#development--contributing)
  - [Pre-commit Hooks](#pre-commit-hooks)
  - [Running Tests](#running-tests)
  - [Coding Standards](#coding-standards)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

### Core Capabilities

| Capability | Status | Notes |
| :--- | :---: | :--- |
| Chat Completions (streaming) | Working | Full SSE streaming, multi-turn memory |
| Chat Completions (non-streaming) | Working | Standard JSON response |
| Tool / Function Calling | Working | Full function call bridge |
| Vision & OCR | Working | Local image files uploaded via Azure blob |
| DALL-E Image Generation | Working | Polls for `sediment://` and `file-service://` assets |
| Image Edit / Composite | Working | Multimodal text with `system_hints: ["picture_v2"]` |
| Deep Research | Working | Triggers and polls background research widgets |
| File Downloads | Working | Resolves both asset pointer formats to CDN URLs |
| Account Usage & Limits | Working | Real-time quota data from ChatGPT backend |
| Projects & Workspaces | Working | List and target specific ChatGPT projects |
| Memory Management | Working | Reads stored ChatGPT memories |
| Multi-Turn Conversations | Working | Automatic conversation ID continuity |
| Parallel Multi-Tab | Working | Concurrent sessions via tab isolation |
| Circuit Breakers | Working | Auth expiry, rate limit, generation-stuck detectors |
| Sentinel PoW Bypass | Working | Native SHA-3 proof-of-work generation |

### Infrastructure

- **OpenAI-Compatible API**: Drop-in replacement for the `openai` Python SDK. Just change the `base_url` to `http://localhost:8080/v1`.
- **Enterprise CI Pipeline**: Pre-commit hooks (secret leak detection, Ruff linting, formatting enforcement) and GitHub Actions gatekeeper workflow.
- **Local Persistence**: SQLite database (`~/.anklient/anklient.db`) for query/response history, telemetrics (Time-To-First-Token, Total Time, word count).
- **Rich Terminal UI**: Built on `prompt_toolkit` and `rich`, providing an interactive REPL with auto-completing slash commands, live streaming panels, and markdown syntax highlighting.

---

## Prerequisites

- **Python 3.10 or higher**
- **Google Chrome** (recommended) or **Microsoft Edge**
- **A valid ChatGPT account** (Free, Plus, or Pro)
- `git`

---

## Installation

### macOS / Linux

```bash
# 1. Clone the repository
git clone https://github.com/savetree-1/ankLIENT.git
cd ankLIENT

# 2. Run the automated installer
chmod +x install.sh
./install.sh
```

The installer:
- Creates an isolated Python virtual environment at `.venv/`
- Installs all Python dependencies from `requirements.txt`
- Creates a `gpt` executable symlink in `/usr/local/bin` (or `~/.local/bin` if no sudo)

### Windows

```cmd
:: 1. Clone the repository
git clone https://github.com/savetree-1/ankLIENT.git
cd ankLIENT

:: 2. Run the installer
install.bat
```

The Windows installer generates a `gpt.bat` wrapper that activates the virtual environment and launches the CLI.

### Manual Setup

If you prefer to install manually:

```bash
git clone https://github.com/savetree-1/ankLIENT.git
cd ankLIENT

python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Quick Start

### Step 1: Launch Chrome with Remote Debugging

Close your browser completely, then launch it from the terminal with the CDP port exposed:

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.anklient/chrome-profile"
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%USERPROFILE%\.anklient\chrome-profile"
```

**Linux:**
```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.anklient/chrome-profile"
```

### Step 2: Log Into ChatGPT

In the newly opened browser window, navigate to `https://chatgpt.com` and log in to your account. Leave this tab open in the background.

### Step 3: Start ankLIENT

```bash
gpt
```

The daemon boots up, attaches to your browser session, acquires an access token, and starts the local API server. You will see:

```
Starting ankLIENT Daemon on port 8080...
Connected to Chrome on CDP port 9222
Access token acquired.
API server listening on http://127.0.0.1:8080
You ›
```

You are now ready to use the interactive CLI and the local API simultaneously.

---

## How It Works

### CDP Session Attachment

ankLIENT does not use Playwright's high-level browser abstraction for network traffic. Instead it:

1. Uses Playwright to attach to the existing Chrome process via `--remote-debugging-port=9222`.
2. Executes JavaScript inside the authenticated ChatGPT tab to extract the `__reactFiber` / session state and obtain a valid Bearer token.
3. Makes **direct HTTP requests** to ChatGPT's private `backend-api` endpoints (e.g. `POST /backend-api/conversation`) with the authenticated token — no browser involved in the actual request.
4. Parses the SSE stream from the backend and proxies it back to the local API caller in real-time.

This architecture means the browser is only needed for its authenticated cookie jar and token. All actual data exchange is direct HTTPS.

### Sentinel Proof-of-Work

OpenAI's backend requires a `openai-sentinel-proof-token` header on all conversation requests. This is a SHA-3 based proof-of-work challenge designed to throttle bots.

ankLIENT's `anklient/engine/pow.py` module:
1. Fetches the current challenge parameters (`seed`, `difficulty`, `required`) from the ChatGPT session.
2. Natively computes the required hash in Python without needing any browser JavaScript execution.
3. Attaches the solved token to every backend API request automatically.

This is what allows ankLIENT to communicate directly with the backend API instead of going through the browser UI.

### Asset Protocol Handling

ChatGPT's backend references generated files using two internal URI schemes:

| Scheme | Origin | Description |
| :--- | :--- | :--- |
| `file-service://file_XXXX` | User uploads | Standard files uploaded via the Azure blob flow |
| `sediment://file_XXXX` | DALL-E outputs | Images generated by the image generation pipeline |

ankLIENT's asset resolver strips both prefixes, resolves the file ID against the `/backend-api/files/{id}/download` endpoint, and returns the final signed CDN URL to the caller.

---

## API Reference

The local API is fully OpenAI-compatible. All endpoints are on `http://127.0.0.1:8080`.

### `POST /v1/chat/completions`

Standard OpenAI-compatible chat completions. Supports streaming.

**Request:**
```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum entanglement in simple terms."}
  ],
  "stream": true
}
```

**Supported Models:**

| API Model Name | Resolves To |
| :--- | :--- |
| `gpt-5.5` | GPT-5.5 |
| `gpt-5` | GPT-5 |
| `gpt-5-mini` | GPT-5 Mini |
| `gpt-4o` | auto (default) |
| `auto` | auto (ChatGPT picks best) |

**Response (streaming):** Standard SSE `data: {...}` chunks followed by `data: [DONE]`.

**Response (non-streaming):**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "choices": [{
    "message": {"role": "assistant", "content": "..."},
    "finish_reason": "stop"
  }]
}
```

**Targeting a Project:**

Pass `project_id` in the request body to route the conversation to a specific ChatGPT project/workspace:
```json
{
  "model": "auto",
  "project_id": "proj_abc123",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

---

### `GET /v1/models`

Returns the list of available models.

```bash
curl http://localhost:8080/v1/models
```

---

### `GET /v1/projects`

Returns all ChatGPT projects associated with the authenticated account.

```bash
curl http://localhost:8080/v1/projects
```

**Response:**
```json
{
  "projects": [
    {"id": "proj_abc123", "name": "My Project", "created_at": "..."}
  ]
}
```

---

### `GET /v1/memories`

Returns all personal memories stored in the authenticated ChatGPT account.

```bash
curl http://localhost:8080/v1/memories
```

---

### `POST /v1/chatgpt/vision`

Upload a local image and send a vision/OCR query about it.

**Request (multipart/form-data or JSON with base64):**
```json
{
  "image_b64": "<base64-encoded-image>",
  "mime_type": "image/png",
  "prompt": "What is shown in this image? Describe in detail."
}
```

**Response:**
```json
{
  "response": "The image shows a Python script with..."
}
```

---

### `POST /v1/chatgpt/research`

Trigger a ChatGPT Deep Research query. This starts a multi-source research job in the background and returns a comprehensive markdown report when complete.

**Note:** Deep Research queries can take 2–10 minutes. The request will block until the research widget finishes.

**Request:**
```json
{
  "prompt": "What are the latest developments in room-temperature superconductors in 2025?"
}
```

**Response:**
```json
{
  "report": "# Room-Temperature Superconductors: 2025 Update\n\n## Summary\n...",
  "sources": ["https://...", "https://..."]
}
```

---

### `POST /v1/images/edits`

Edit or composite an existing image using DALL-E. The base image is uploaded, and the edit prompt is applied.

**Request:**
```json
{
  "image_b64": "<base64-encoded-image>",
  "mime_type": "image/png",
  "prompt": "Add a rainbow in the sky of this landscape photo."
}
```

**Response:**
```json
{
  "file_id": "file_00000000abc123...",
  "download_url": "https://..."
}
```

---

### `GET /v1/chatgpt/files/{file_id}/download`

Resolve an internal ChatGPT asset ID (from `file-service://` or `sediment://` pointers) to a direct, signed CDN download URL.

```bash
curl "http://localhost:8080/v1/chatgpt/files/file_00000000abc123/download"
```

**Response:**
```json
{
  "url": "https://oaiusercontent-prod.blob.core.windows.net/..."
}
```

---

### `GET /v1/chatgpt/usage`

Fetch real-time account limits and current quota usage.

```bash
curl http://localhost:8080/v1/chatgpt/usage
```

**Response:**
```json
{
  "limits": [
    {
      "feature": "gpt-5-heavy",
      "limit": 50,
      "used": 12,
      "remaining": 38,
      "resets_at": "2025-09-01T00:00:00Z"
    }
  ]
}
```

---

### `GET /health`

Returns the health and telemetry state of the running daemon.

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "ok",
  "cdp_connected": true,
  "requests_served": 42,
  "last_error": null,
  "uptime_seconds": 3812
}
```

---

## CLI Usage Reference

### Interactive REPL Mode

When you run `gpt`, the daemon starts and you are placed into an interactive REPL. Simply type any message and press `Enter` to chat.

```
You › What is the capital of France?

ChatGPT › Paris is the capital of France. It has been the country's political
           and cultural center for centuries, and is home to landmarks such as
           the Eiffel Tower, the Louvre, and Notre-Dame Cathedral.

You ›
```

The REPL supports:
- **Up/Down arrows** to navigate command history
- **Tab completion** for all `/` slash commands
- **Live streaming panel** that renders the response in real time as it arrives

### Slash Commands

All advanced features are accessible through slash commands typed at the `You ›` prompt.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/help` | — | Display the full command manual |
| `/file` | `<path>` | Attach a local file or image to the next message |
| `/vision` | `<path> <prompt>` | Upload an image and run a vision/OCR query |
| `/research` | `<prompt>` | Run an extensive ChatGPT Deep Research query |
| `/generate` | `<prompt>` | Generate a DALL-E image and save it locally |
| `/usage` | — | Display account quota limits as a formatted table |
| `/download` | `<file_id>` | Resolve and download an internal ChatGPT asset |
| `/memories` | — | List all personal memories stored in your account |
| `/projects` | — | List your ChatGPT projects and workspaces |
| `/prompts` | — | List all saved prompt templates |
| `/use` | `<id>` | Load a prompt template by ID and fill its variables |
| `/newprompt` | — | Create and save a new prompt template interactively |
| `/copy` | — | Copy the last AI response to the system clipboard |
| `/paste` | — | Paste clipboard contents into the input buffer |
| `/save` | `<filename>` | Save the last AI response to a local file |
| `/history` | — | Display the 10 most recent conversation turns |
| `/status` | — | Verify CDP connection state and active target |
| `/recover` | — | Re-initialize DOM locators if the page reloads |
| `/quit` | — | Terminate the daemon and exit |

#### Example: Vision Query

```
You › /vision ~/screenshot.png What text is in this image?

ChatGPT › The image contains the following text: "Welcome to ankLIENT..."
```

#### Example: Deep Research

```
You › /research Latest breakthroughs in fusion energy 2025

[Deep Research running... this may take a few minutes]

ChatGPT › # Fusion Energy: 2025 Breakthroughs
## Summary
In 2025, significant progress was made across three major programs...
```

#### Example: Account Usage

```
You › /usage

  Feature          Used    Limit   Remaining   Resets
 ─────────────────────────────────────────────────────
  GPT-5 Heavy       12      50        38       Sep 1
  DALL-E Images      3      40        37       Sep 1
  Deep Research      1      10         9       Sep 1
```

---

## Configuration

### Config File

ankLIENT reads its configuration from `~/.anklient/config.json`. This file is created automatically on first run with sensible defaults.

```json
{
  "chrome": {
    "cdp_port": 9222,
    "headless": false,
    "restart_on_crash": true
  },
  "server": {
    "port": 8080,
    "host": "127.0.0.1",
    "api_keys": [],
    "request_timeout": 120
  },
  "chatgpt": {
    "default_model": "auto",
    "default_project_id": null,
    "tab_mode": "owned",
    "parallel_tabs": false
  },
  "log": {
    "level": "INFO"
  }
}
```

### Chrome / CDP Settings

| Key | Default | Description |
| :--- | :--- | :--- |
| `cdp_port` | `9222` | Port Chrome was launched with `--remote-debugging-port` |
| `headless` | `false` | Run Chrome without a visible window |
| `restart_on_crash` | `true` | Auto-restart Chrome if it unexpectedly exits |
| `user_data_dir` | `~/.anklient/chrome-profile` | Chrome profile directory (persists cookies/session) |

### Server Settings

| Key | Default | Description |
| :--- | :--- | :--- |
| `port` | `8080` | Port for the local API server |
| `host` | `127.0.0.1` | Bind address (`0.0.0.0` to expose on LAN) |
| `api_keys` | `[]` | Optional list of Bearer tokens to require on requests |
| `request_timeout` | `120` | Seconds before an API request times out |

### API Key Authentication

If you set `api_keys` in the config, all requests must include an `Authorization: Bearer <key>` header. This is useful if you expose ankLIENT on your local network and want basic access control.

```json
{
  "server": {
    "api_keys": ["my-secret-key-abc123"]
  }
}
```

Then clients must send:
```
Authorization: Bearer my-secret-key-abc123
```

---

## Architecture

ankLIENT is organized into clean, decoupled modules following SOLID principles.

### Directory Structure

```
anklient/
├── engine/               # Core engine: CDP driver, API server, browser management
│   ├── api_server.py     # OpenAI-compatible HTTP API (aiohttp)
│   ├── cdp_driver.py     # Direct backend API calls, Sentinel PoW, asset resolution
│   ├── cdp_transport.py  # Low-level Chrome DevTools Protocol WebSocket transport
│   ├── config.py         # Typed configuration dataclasses
│   ├── pow.py            # SHA-3 Sentinel Proof-of-Work solver
│   ├── service.py        # Daemon orchestration (Chrome + driver + API server)
│   ├── chrome.py         # Chrome process manager (launch, health check, restart)
│   ├── turn_anchor.py    # SSE stream parser and turn-boundary detector
│   ├── resilience.py     # Retry logic with exponential backoff for rate limits
│   ├── breakers.py       # Circuit breaker registry (auth, rate limit, stuck)
│   ├── mcp_server.py     # Model Context Protocol server (tool bridge)
│   └── ensure.py         # Pre-flight environment checks
│
├── chat/                 # Client-side abstractions
│   ├── api_client.py     # HTTP client for the local daemon API
│   ├── client.py         # Legacy Playwright DOM-based client (kept for fallback)
│   └── message.py        # ChatResponse and timing data models
│
├── commands/             # CLI slash command implementations
│   ├── builtins.py       # All /command handler functions
│   └── router.py         # Command dispatch and argument parsing
│
├── daemon/
│   └── server.py         # Entry point for the background daemon process
│
├── drivers/              # Legacy Playwright driver abstractions
│   ├── playwright_driver.py
│   ├── connection.py
│   └── recovery.py
│
├── history/              # SQLite persistence layer
│   ├── database.py       # Schema and connection management
│   ├── models.py         # HistoryItem dataclass
│   └── repository.py     # CRUD operations
│
├── prompts/              # Prompt template engine
│   ├── templates.py      # Variable extraction and rendering
│   ├── manager.py        # Template storage and retrieval
│   └── models.py         # Prompt dataclass
│
├── ui/                   # Terminal rendering components
│   ├── terminal.py       # Console, live panels, streaming display
│   ├── panels.py         # Request/response panel builders
│   └── theme.py          # Rich color theme definitions
│
└── main.py               # Interactive REPL entry point
```

### Engine Layer

The engine is the heart of ankLIENT. It is fully async (`asyncio` + `aiohttp`) and structured in three layers:

1. **CDP Transport** (`cdp_transport.py`): A raw WebSocket client for the Chrome DevTools Protocol. Handles `Runtime.evaluate`, `Page.navigate`, `Target.createTarget`, and all other CDP methods.

2. **CDP Driver** (`cdp_driver.py`): The high-level business logic layer. It:
   - Acquires and refreshes the ChatGPT access token via JavaScript execution in the browser.
   - Generates Sentinel proof tokens natively in Python.
   - Uploads files to Azure Blob Storage using SAS URLs fetched from ChatGPT's backend.
   - Posts conversations directly to `POST /backend-api/conversation` with properly-formed payloads.
   - Polls conversation state for async-generated assets (images, research reports).
   - Resolves `file-service://` and `sediment://` asset pointers to signed CDN URLs.

3. **API Server** (`api_server.py`): An `aiohttp` web application that translates OpenAI-compatible HTTP requests into driver method calls and proxies the responses back.

### Circuit Breakers

ankLIENT implements a circuit breaker pattern to gracefully handle failure modes without crashing:

| Breaker | Trigger | Behavior |
| :--- | :--- | :--- |
| `AUTH_EXPIRED` | 401 from backend API | Pauses requests, prompts re-login |
| `RATE_LIMITED` | 429 from backend API | Exponential backoff (up to 5 minutes) |
| `GENERATION_STUCK` | DALL-E never produces asset | Timeout after 60 seconds, error returned |

The breaker state is exposed on the `/health` endpoint so you can monitor it from external tools.

### Multi-Tab Mode

By default, ankLIENT uses `tab_mode: "owned"`, where each driver session creates a **dedicated, isolated ChatGPT tab** via `Target.createTarget`. This means:

- Two simultaneous API requests never conflict on the same DOM.
- Each tab maintains its own conversation context.
- Tabs are automatically cleaned up when the daemon shuts down.

Setting `parallel_tabs: true` in the config enables concurrent multi-tab processing for high-throughput use cases.

---

## Cloud Deployment (Proof of Concept)

ankLIENT was initially developed as a localized macOS background daemon. However, extensive live testing on GitHub Codespaces has successfully proven that **ankLIENT is 100% cloud-ready and can run natively in a headless Linux server environment** without requiring a physical machine or graphical display.

### Codespaces Testing Methodology

To validate the cloud viability without incurring infrastructure costs, a sandboxed Proof-of-Concept (POC) was executed using GitHub Codespaces. The setup included:
- **Environment:** Debian 12 (Bookworm) Linux Container with Python 3.11.
- **Dependencies:** Core OS libraries (e.g., `libnss3`, `libasound2`) installed via a custom `.devcontainer`.
- **Browser:** A fully headless Chromium browser managed by Playwright binaries (which guarantees compatibility in Dockerized/isolated environments).
- **Session Injection:** The `__Secure-next-auth.session-token` cookie from an existing authenticated macOS browser session was directly injected into the headless Chromium profile using a CDP script, entirely bypassing the need for a VNC or GUI-based login.

### Key Findings & Outcomes

The test yielded four major successes, paving the way for a permanent VPS deployment:

1. **Mac-Free Execution:** The daemon successfully ran on an isolated Linux server without any reliance on macOS-specific tools or background services.
2. **Headless Bot Evasion:** OpenAI's Cloudflare and bot-detection systems were successfully bypassed by configuring the headless Chromium instance with specific launch flags (such as `--disable-blink-features=AutomationControlled`) and a spoofed standard User-Agent, preventing the `HeadlessChrome` detection.
3. **Session Persistence:** It was verified that the ChatGPT session cookie remains valid and securely authorizes direct `backend-api` HTTP requests, effectively eliminating the need for periodic manual logins on the server (the cookie is naturally valid for ~30-90 days).
4. **Global API Accessibility:** The local API (`localhost:8080`) was successfully exposed via Codespaces port forwarding, allowing real-world external HTTP clients (e.g., mobile phones, other servers) to successfully query the OpenAI-compatible REST API remotely.

### Next Steps (VPS Migration)

Since GitHub Codespaces enforce a strict 30-minute idle timeout and monthly compute limits, the environment is strictly for development and testing. 

With the Linux deployment architecture now verified, the next milestone is to migrate the identical containerized setup to an **Always Free Oracle Cloud ARM VM** (or a low-cost Hetzner Linux VPS). This will provide a true 24/7/365, permanently active OpenAI-compatible backend proxy powered entirely by your ChatGPT Plus subscription.

---

## Integrations

### Using with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed",  # ankLIENT doesn't require a key by default
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Using with opencode

`opencode` is a terminal-based AI coding assistant that supports any OpenAI-compatible API. Create an `opencode.json` in your project:

```json
{
  "model": "gpt-4o",
  "provider": {
    "name": "anklient",
    "baseURL": "http://localhost:8080/v1",
    "apiKey": "not-needed"
  }
}
```

Then run `opencode` in your project directory. It will route all requests through your local ChatGPT session.

### Using with any HTTP client

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

---

## Development & Contributing

### Pre-commit Hooks

ankLIENT uses `pre-commit` to enforce quality gates before every commit:

```bash
pip install pre-commit
pre-commit install
```

The following checks run automatically on `git commit`:

1. **Trailing whitespace** — removed automatically
2. **End-of-file fixer** — ensures a trailing newline
3. **YAML validation** — checks config and workflow files
4. **Large file detection** — prevents accidentally committing binary blobs
5. **Secret leak detection** — prevents committing API keys or tokens
6. **Ruff linting** — catches code smells and applies auto-fixes
7. **Ruff formatting** — enforces consistent code style

### Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

Unit tests are in `tests/unit/` and use `unittest.mock` to mock all browser and network calls. They are fast and require no running Chrome instance.

Integration tests (in `tests/integration/`) require a running daemon (`gpt &`) and test the actual API endpoints against `localhost:8080`.

### Coding Standards

See [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) for the full engineering standards. Key rules:

- **Formatter:** `ruff format` (line length 100)
- **Type hints:** Required on all functions
- **Docstrings:** Google-style, explaining *why* not just *what*
- **No bare exceptions:** Always catch specific error types
- **No `time.sleep()`:** Always use `asyncio.sleep()` in async contexts
- **Functions ≤ 100 lines:** Refactor into helpers if exceeded

---

## Troubleshooting

### `Connection refused` on port 9222

Chrome was not launched with remote debugging enabled. Close all Chrome windows completely and re-launch from the terminal with `--remote-debugging-port=9222`.

### `Access token could not be acquired`

You are not logged in to ChatGPT in the browser. Navigate to `chatgpt.com` and complete login before starting the daemon.

### `Rate limit` errors

ChatGPT's backend is returning 429s. ankLIENT will automatically apply exponential backoff and retry. The `/health` endpoint will show the breaker state. Wait for the backoff to expire.

### Response is empty / daemon hangs

This can happen if ChatGPT's UI has changed and the DOM selectors are stale. Try:
```
You › /recover
```
Or restart the daemon: `gpt`

### `fatal: refusing to allow an OAuth App to create or update workflow`

Your local Git token doesn't have the `workflow` scope. Create the `.github/workflows/ci.yml` file directly through the GitHub web UI instead (Actions tab → "set up a workflow yourself").

---

## Roadmap

- **Phase 3: Unit Test Suite** — Comprehensive mocked unit tests for all engine modules.
- **Phase 4: MCP Tool Call Bridge** — Expose ChatGPT's native function calling through the Model Context Protocol server.
- **Phase 5: Conversation Memory** — Persistent, searchable conversation history with vector embeddings.
- **Phase 6: Multi-Account Support** — Route requests to different ChatGPT accounts based on API key, load balance across Plus and Pro seats.

---

## License

Distributed under the MIT License. See `LICENSE` for details.

---

Made with ❤️ by Ankush.
