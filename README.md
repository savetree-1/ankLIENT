# ankLIENT

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

ankLIENT is a powerful local daemon and CLI that bridges an authenticated ChatGPT Web session into a fully functional, OpenAI-compatible API on your local machine. By attaching to a local browser instance via the Chrome DevTools Protocol (CDP), it unlocks web-only capabilities—including Deep Research, DALL-E image generation/editing, vision, and tool calls—directly from your terminal or any API client, bypassing traditional API costs and limitations.

## Features

* **OpenAI-Compatible API**: Exposes a local API server (default `localhost:8080`) with endpoints for chat completions, mimicking the official OpenAI API structure.
* **Sentinel Proof-of-Work Bypass**: Natively solves and generates OpenAI's required Proof-of-Work hash tokens for direct backend API communication.
* **Deep Research**: Natively triggers and polls background Deep Research widgets (`/v1/chatgpt/research`).
* **Advanced Vision & OCR**: Uploads local files and processes vision queries via direct Azure blob storage uploads (`/v1/chatgpt/vision`).
* **Image Generation & Editing**: Supports DALL-E image generation and image compositing/editing natively (`/v1/images/edits`).
* **File Management**: Automatically downloads generated assets (images, documents) from ChatGPT's internal backend (`file-service://` and `sediment://`).
* **Account Usage Monitoring**: Fetches real-time account limits and usage quotas (`/v1/chatgpt/usage`).
* **Interactive CLI**: Includes a rich REPL interface with slash commands for quick access to all advanced features.

## Prerequisites

* Python 3.10 or higher
* Microsoft Edge (or Google Chrome)
* A valid ChatGPT account

## Installation

### macOS / Linux
1. Clone the repository:
   ```bash
   git clone https://github.com/savetree-1/ankLIENT.git
   cd ankLIENT
   ```
2. Run the automated installer:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   *(This creates a virtual environment, installs dependencies, downloads required Playwright binaries, and symlinks the `gpt` executable).*

## Execution

Because ankLIENT operates as a CDP client, the target browser must be launched with remote debugging enabled on port `9222`.

Close your browser completely, then launch it from the terminal:

**macOS:**
```bash
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222 --user-data-dir="$HOME/edge-chatgpt-profile"
```

Navigate to `chatgpt.com` in the newly opened browser and authenticate. Leave the tab active in the background.

Initialize the Daemon & CLI:
```bash
gpt
```

## Local API Endpoints

Once the daemon is running, it exposes the following endpoints on `http://localhost:8080`:

* `POST /v1/chat/completions` - Standard chat completions (supports tool calls).
* `POST /v1/chatgpt/vision` - Vision and image analysis.
* `POST /v1/chatgpt/research` - Run a Deep Research query.
* `POST /v1/images/edits` - Edit/composite images with DALL-E.
* `GET /v1/chatgpt/files/{file_id}/download` - Get a direct download URL for a generated asset.
* `GET /v1/chatgpt/usage` - Fetch current account limits.

## CLI Usage Reference

The client operates as a standard chat REPL. In addition to text input, it supports interactive commands triggered by the `/` prefix:

| Command | Description |
| :--- | :--- |
| `/help` | Display the command manual. |
| `/vision <file> <prompt>` | Upload an image and run a vision query. |
| `/research <prompt>` | Run an extensive Deep Research query. |
| `/download <file_id>` | Resolve and download an internal ChatGPT asset. |
| `/usage` | Display account limits and current quota progress. |
| `/quit` | Terminate the client and API daemon. |

## Architecture

The codebase is modular, cleanly separating the browser driver from the API server and CLI interface:

* `anklient/engine/cdp_driver.py` - Core Playwright bindings, DOM manipulation, and direct Backend API interaction (Azure blob uploads, conversation polling).
* `anklient/engine/api_server.py` - HTTP server routing client requests to the engine driver.
* `anklient/engine/pow.py` - Sentinel Proof-of-Work hash generation.
* `anklient/chat/api_client.py` - Local Python client for interacting with the daemon.
* `anklient/commands/` - CLI slash command implementations.

## License

Distributed under the MIT License. See `LICENSE` for details.

---
Made with ❤️ by Ankush.
