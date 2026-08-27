# ⚡️ ChatGPT Local CLI

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)
![Rich](https://img.shields.io/badge/UI-Rich-magenta.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A powerful, entirely local Command Line Interface (CLI) that turns your authenticated ChatGPT browser tab into a blazing-fast terminal powerhouse.

## 📖 About The Project

Tired of context-switching between your terminal and the browser? Frustrated by expensive API costs for simple tasks? 

**ChatGPT Local CLI** solves this by directly hooking into your active Microsoft Edge browser session using Chrome DevTools Protocol (CDP). It allows you to use your existing ChatGPT account (including Plus features like GPT-4o, image generation, and data analysis) entirely from your terminal—without ever needing an API key.

Built with Python, Playwright, and Rich, it offers a seamless, beautiful terminal UI with real-time streaming, syntax highlighting, and persistent local storage.

---

## ✨ Core Features

* **🚀 Zero API Keys**: Uses your existing browser session. If you can access it in the browser, you can access it in the terminal.
* **📚 Dynamic Prompt Library**: Create complex prompt templates (e.g., Code Reviewer, Text Humanizer) with variables. The CLI will automatically ask you to fill in the blanks before sending.
* **📂 Seamless File Uploads**: Attach local files or photos to your prompts directly from the CLI. The tool handles the hidden DOM interactions automatically.
* **💻 Interactive Slash Commands**: A beautiful auto-completing dropdown menu for commands, triggered instantly when you type `/`.
* **📋 Clipboard Integration**: Instantly copy AI responses or paste massive blocks of code from your clipboard without messing up terminal formatting.
* **💾 Local SQLite History**: Every chat, request, and exact timing metric (Time-To-First-Token, Total Time) is saved locally to a SQLite database.
* **⚡️ Blazing Fast UI**: Real-time streaming, beautiful markdown rendering, and syntax highlighting.

---

## 🛠 Prerequisites

* Python 3.10 or higher
* Microsoft Edge (or Google Chrome) installed on your machine
* A ChatGPT Account

---

## 💻 Installation

### macOS / Linux
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chatgpt-local.git
   cd chatgpt-local
   ```
2. Run the automated installer:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   *(This creates a virtual environment, installs dependencies, downloads Playwright browsers, and creates a global `gpt` command).*

### Windows
1. Download and extract this repository.
2. Open the folder and double-click the `install.bat` file.
3. The script will automatically install all dependencies and generate a `gpt.bat` file. 
4. *(Optional)* To use the `gpt` command from anywhere, copy `gpt.bat` into `C:\Windows`.

---

## 🔌 Connecting to the Browser

Because this CLI acts as a remote control, you **must** launch Microsoft Edge with remote debugging enabled on port `9222`. 

Close Edge completely, then run the specific command for your OS:

**Mac:**
```bash
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222 --user-data-dir="$HOME/edge-chatgpt-profile"
```

**Windows (Command Prompt):**
```cmd
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\edge-chatgpt-profile"
```

Once Edge opens, navigate to [chatgpt.com](https://chatgpt.com) and log in. **Leave the tab open in the background!**

---

## 🎮 Detailed Usage Guide

Open a new terminal window and launch the interface:
```bash
gpt
```

### 1. Normal Chatting
Just type naturally at the `You ›` prompt and press Enter. The CLI will stream the response back to you with full Markdown rendering.

### 2. Attaching Files & Photos
Need to analyze an image or read a document?
1. Type `/file <path_to_file>` (e.g. `/file ~/Desktop/image.png`) and hit Enter. You can even drag and drop the file into the terminal.
2. Type your text prompt (e.g., *"What is in this image?"*) and hit Enter to send them both together!

### 3. Using the Prompt Library
Automate repetitive tasks using templates:
1. Type `/prompts` to view your saved template library and their ID numbers.
2. Type `/use <id>` (e.g. `/use 1`) to load a template.
3. The CLI will detect variables (like `{{code}}` or `{{instructions}}`) and ask you to fill them in one by one. The final stitched prompt will be sent automatically.

### Command Reference

| Command | Description |
| :--- | :--- |
| `/help` | View the manual and all available commands. |
| `/prompts` | View your saved template library. |
| `/use <id>` | Use a template. (e.g. `/use 1`). Prompts you for variables. |
| `/file <path>`| Attach a local file/photo to your next message. |
| `/copy` | Copies ChatGPT's very last response to your clipboard. |
| `/paste` | Pastes your clipboard's contents directly into the prompt. |
| `/save <file>`| Saves the last response to a file (e.g. `/save script.py`). |
| `/history` | View your 10 most recent chats. |
| `/status` | Check the health of your browser connection. |
| `/recover` | Reconnect if the browser tab reloads or disconnects. |
| `/quit` | Exit the CLI. |

---

## 📁 Architecture Overview

The project is heavily modularized for easy contribution and expansion:

* `app/main.py` - The central entry point. Handles the REPL loop and threaded `prompt_toolkit` dropdowns.
* `app/browser/` - Playwright automation. Handles the CDP connection, DOM selectors, page interaction, and recovery logic.
* `app/chat/` - Message abstraction and timing calculation logic (TTFT, total ms).
* `app/ui/` - Rich terminal UI components, theming, and layout panels.
* `app/prompts/` - Template engine supporting variables (regex parsing) and SQLite storage.
* `app/history/` - SQLite logging of all chats, payloads, and performance metrics.
* `app/commands/` - Interactive REPL builtins and Slash commands execution logic.

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---
Made with ♥ by Ankush.
