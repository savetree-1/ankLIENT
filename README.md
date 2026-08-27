# ankLIENT

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)
![Rich](https://img.shields.io/badge/UI-Rich-magenta.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

ankLIENT is a modular Command Line Interface (CLI) that connects directly to an authenticated web session of ChatGPT via the Chrome DevTools Protocol (CDP). By attaching to a local browser instance, the client provides access to web-only capabilities—including DALL-E image generation, file uploads, and Plus features—directly from the terminal without requiring API keys.

## Features

* **Session Attachment**: Connects to an existing browser session via Playwright and CDP, bypassing API limitations and costs.
* **Image Generation Tracking**: Mirrors live DALL-E image generation DOM states (e.g., "Sketching it out", "Polishing details") directly to a live terminal panel, and automatically downloads the resulting image assets to the local filesystem.
* **File Operations**: Natively supports attaching local files and images to prompts via DOM injection.
* **Template Engine**: Supports parameterized prompt templates. The CLI automatically extracts variables (e.g., `{{variable}}`) and prompts the user for input during execution.
* **Local Persistence**: All queries, responses, and performance metrics (Time-To-First-Token, Total Time) are logged to a local SQLite database for historical analysis.
* **Terminal Interface**: Built on `prompt_toolkit` and `rich`, providing an interactive REPL with auto-completing slash commands, markdown rendering, and syntax highlighting.

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

### Windows
1. Clone the repository.
2. Execute the `install.bat` file.
3. The script will configure the Python environment and generate a `gpt.bat` executable wrapper.

## Execution

Because ankLIENT operates as a CDP client, the target browser must be launched with remote debugging enabled on port `9222`.

Close your browser completely, then launch it from the terminal:

**macOS:**
```bash
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222 --user-data-dir="$HOME/edge-chatgpt-profile"
```

**Windows:**
```cmd
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\edge-chatgpt-profile"
```

Navigate to `chatgpt.com` in the newly opened browser and authenticate. Leave the tab active in the background.

Initialize the CLI:
```bash
gpt
```

## Usage Reference

The client operates as a standard chat REPL. In addition to standard text input, it supports the following interactive commands triggered by the `/` prefix:

| Command | Description |
| :--- | :--- |
| `/help` | Display the command manual. |
| `/prompts` | List all saved prompt templates and their respective IDs. |
| `/use <id>` | Load a template by ID and begin variable injection. |
| `/file <path>`| Attach a local file or image to the current context buffer. |
| `/copy` | Copy the previous model response to the system clipboard. |
| `/paste` | Inject the system clipboard contents into the input buffer. |
| `/save <file>`| Write the previous model response to a local file. |
| `/history` | Display the 10 most recent conversational turns. |
| `/status` | Verify the CDP connection state and active target. |
| `/recover` | Re-initialize the DOM locators if the target page navigates or reloads. |
| `/quit` | Terminate the client. |

## Architecture

The codebase is organized into independent modules to facilitate maintenance and extension:

* `app/main.py` - Core execution loop and `prompt_toolkit` integration.
* `app/browser/` - Playwright bindings, CDP session management, state tracking, and image generation DOM observers.
* `app/chat/` - Message abstractions and telemetric timing logic.
* `app/ui/` - Terminal rendering components, live panels, and theming.
* `app/prompts/` - Regex-based template parsing and storage interface.
* `app/history/` - SQLite schema definitions and repository layer.
* `app/commands/` - Command router and built-in function implementations.

## Contributing

Contributions are accepted and encouraged. Please ensure that all modifications align with the existing modular architecture and maintain strict decoupling between DOM manipulation and terminal rendering.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/Implementation`)
3. Commit your changes (`git commit -m 'Implement standard feature'`)
4. Push to the branch (`git push origin feature/Implementation`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for details.

---
Made with love by Ankush.
