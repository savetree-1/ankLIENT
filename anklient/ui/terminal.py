import time

from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from anklient.chat.message import ChatResponse

from .panels import create_request_panel, create_response_panel
from .theme import chatgpt_theme

console = Console(theme=chatgpt_theme)

ASCII_ART = r"""[bold cyan]                     /$$       /$$       /$$$$$$ /$$$$$$$$ /$$   /$$ /$$$$$$$$
                    | $$      | $$      |_  $$_/| $$_____/| $$$ | $$|__  $$__/
  /$$$$$$  /$$$$$$$ | $$   /$$| $$        | $$  | $$      | $$$$| $$   | $$   
 |____  $$| $$__  $$| $$  /$$/| $$        | $$  | $$$$$   | $$ $$ $$   | $$   
  /$$$$$$$| $$  \ $$| $$$$$$/ | $$        | $$  | $$__/   | $$  $$$$   | $$   
 /$$__  $$| $$  | $$| $$_  $$ | $$        | $$  | $$      | $$\  $$$   | $$   
|  $$$$$$$| $$  | $$| $$ \  $$| $$$$$$$$ /$$$$$$| $$$$$$$$| $$ \  $$   | $$   
 \_______/|__/  |__/|__/  \__/|________/|______/|________/|__/  \__/   |__/[/bold cyan]"""


def print_header():
    console.print()
    console.print(ASCII_ART)
    console.print()
    console.print(
        "  [bold cyan]A powerful, local CLI for your authenticated ChatGPT session.[/bold cyan]"
    )
    console.print(
        "  [dim]Use it to manage prompts, search history, and script AI tasks directly from your terminal.[/dim]"
    )
    console.print()
    console.print(
        "  [status.done]●[/status.done] [bold white]Connected to ankLIENT Daemon[/bold white] [dim]— API :8080[/dim]"
    )
    console.print()
    console.print("  [bold]How to use:[/bold]")
    console.print(
        "  [dim]•[/dim] [bold magenta]Type manually[/bold magenta] and press Enter to chat directly."
    )
    console.print(
        "  [dim]•[/dim] Type [bold cyan]/prompts[/bold cyan] to access your template library."
    )
    console.print(
        "  [dim]•[/dim] Type [bold cyan]/help[/bold cyan] to view all available commands."
    )
    console.print("  [dim]•[/dim] Type [bold yellow]/quit[/bold yellow] to exit.")
    console.print()
    console.print("  [dim]Made with [/dim][bold red]♥[/bold red][dim] by Ankush.[/dim]")
    console.print()


def print_request(prompt: str):
    console.print(create_request_panel(prompt))


def print_response_stats(response: ChatResponse):
    console.print("[status.done]Complete[/status.done]")
    console.print(
        f"  [meta.label]TTFT[/meta.label]       [meta.value]{response.timing.ttft_ms:,.0f} ms[/meta.value]"
    )
    console.print(
        f"  [meta.label]Total[/meta.label]      [meta.value]{response.timing.total_ms / 1000:,.2f} s[/meta.value]"
    )
    console.print(
        f"  [meta.label]Words[/meta.label]      [meta]{response.word_count:,}[/meta]"
    )
    console.print(
        f"  [meta.label]Characters[/meta.label] [meta]{response.char_count:,}[/meta]"
    )
    console.print()


def print_response(response: ChatResponse):
    print_response_stats(response)
    console.print(create_response_panel(response.content))
    if hasattr(response, "saved_images") and response.saved_images:
        console.print()
        for path in response.saved_images:
            console.print(f"  [status.done]Saved image to:[/status.done] {path}")
    console.print()


def print_error(error: Exception):
    console.print("\n[error]Request failed[/error]")
    console.print(f"Reason:\n{error}\n")
    console.print("Try checking if the background daemon is running.\n")


class ImageGenerationLivePanel:
    def __init__(self):
        self.live = None
        self.start_time = time.time()
        self.current_status = "Creating image..."
        self.animation_frame = 0
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __rich__(self):
        elapsed = time.time() - self.start_time
        # Slow down the spinner slightly since it refreshes 10 times a sec
        self.animation_frame += 1
        spinner = self.frames[(self.animation_frame // 2) % len(self.frames)]

        content = (
            f"{spinner} {self.current_status}\n\n[dim]Elapsed: {elapsed:.1f} s[/dim]"
        )
        return Panel(
            content, title="IMAGE GENERATION", border_style="magenta", padding=(1, 2)
        )

    def start(self):
        self.live = Live(self, refresh_per_second=10, console=console, transient=True)
        self.live.start()

    def update(self, status: str):
        if status:
            self.current_status = status

    def stop(self):
        if self.live:
            self.live.stop()
            self.live = None


class TextStreamingLivePanel:
    def __init__(self):
        self.live = None
        self.current_text = "..."

    def start(self):
        self.live = Live(
            self._build_panel(), refresh_per_second=15, console=console, transient=True
        )
        self.live.start()

    def update(self, text: str):
        if text and text != self.current_text:
            self.current_text = text
            if self.live:
                self.live.update(self._build_panel())

    def stop(self):
        if self.live:
            self.live.stop()
            self.live = None

    def _build_panel(self):
        return create_response_panel(self.current_text)
