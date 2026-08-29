import pathlib

from anklient.clipboard.macos import copy_to_clipboard, paste_from_clipboard
from anklient.config.settings import settings
from anklient.drivers.recovery import recover_connection
from anklient.prompts.templates import extract_variables, render_template
from anklient.ui.terminal import console


def cmd_help(context, *args):
    console.print("\n[bold cyan]CHATGPT LOCAL MANUAL[/bold cyan]")

    console.print("\n[bold white]1. Normal Chatting[/bold white]")
    console.print(
        "   Just type your question at the [bold magenta]You ›[/bold magenta] prompt and press Enter."
    )

    console.print("\n[bold white]2. Attaching Files & Photos[/bold white]")
    console.print(
        "   Step 1: Type [bold cyan]/file <path_to_file>[/bold cyan] and hit Enter."
    )
    console.print("           (You can drag and drop the file into the terminal)")
    console.print(
        "   Step 2: Type your text prompt and hit Enter to send them both together!"
    )

    console.print("\n[bold white]3. Using the Prompt Library[/bold white]")
    console.print(
        "   Step 1: Type [bold cyan]/prompts[/bold cyan] to see all your saved templates."
    )
    console.print(
        "   Step 2: Type [bold cyan]/use <id>[/bold cyan] (e.g. [cyan]/use 1[/cyan]) to load one."
    )
    console.print(
        "   Step 3: Fill in the requested variables. The final prompt will be sent automatically."
    )

    console.print("\n[bold white]4. Utility Commands[/bold white]")
    console.print(
        "   [bold cyan]/copy[/bold cyan]       Copy the AI's last response to your clipboard"
    )
    console.print(
        "   [bold cyan]/paste[/bold cyan]      Paste text from your clipboard into your prompt"
    )
    console.print(
        "   [bold cyan]/save <f>[/bold cyan]   Save the last response to a file (e.g. /save code.py)"
    )
    console.print("   [bold cyan]/history[/bold cyan]    View your recent chat history")
    console.print(
        "   [bold cyan]/generate[/bold cyan]   Generate an image using DALL-E (boots the visual engine)"
    )
    console.print(
        "   [bold cyan]/memories[/bold cyan]   List all personal memories stored in your ChatGPT account"
    )
    console.print(
        "   [bold cyan]/projects[/bold cyan]   List your ChatGPT projects and workspaces"
    )
    console.print(
        "   [bold cyan]/status[/bold cyan]     Check browser connection health"
    )
    console.print(
        "   [bold cyan]/recover[/bold cyan]    Reconnect if the browser tab reloads or disconnects"
    )
    console.print("   [bold cyan]/quit[/bold cyan]       Exit the app\n")


def cmd_history(context, *args):
    history_repo = context.get("history_repo")
    items = history_repo.get_recent(10)
    if not items:
        console.print("[dim]No history found.[/dim]")
        return

    for item in reversed(items):
        console.print(
            f"[dim]#{item.id}[/dim] {item.timestamp.strftime('%H:%M:%S')} - {item.prompt[:50]}..."
        )
    console.print()


def cmd_prompts(context, *args):
    prompt_mgr = context.get("prompt_mgr")
    prompts = prompt_mgr.get_all()

    console.print("\n[bold cyan]PROMPT LIBRARY[/bold cyan]\n")
    for p in prompts:
        console.print(f"  [meta.value]{p.id}.[/meta.value] [bold]{p.name}[/bold]")
        console.print(f"     [dim]{p.description}[/dim]")
    console.print()


def cmd_use(context, *args):
    if not args:
        console.print(
            "[error]Missing prompt ID. Usage: /use <id> [optional text][/error]"
        )
        return

    try:
        prompt_id = int(args[0])
    except ValueError:
        console.print("[error]Invalid prompt ID. Must be a number.[/error]")
        return

    prompt_mgr = context.get("prompt_mgr")
    prompts = prompt_mgr.get_all()

    template_str = None
    for p in prompts:
        if p.id == prompt_id:
            template_str = p.template
            prompt_mgr.increment_usage(prompt_id)
            break

    if not template_str:
        console.print(f"[error]Prompt #{prompt_id} not found.[/error]")
        return

    vars_needed = extract_variables(template_str)
    values = {}

    extra_text = " ".join(args[1:])

    if vars_needed:
        # If the user typed the text on the same line AND there is exactly one variable, auto-fill it!
        if extra_text and len(vars_needed) == 1:
            values[vars_needed[0]] = extra_text
        else:
            console.print("[dim]Fill in the blanks to complete this template:[/dim]")
            for var in vars_needed:
                val = console.input(f"[meta.value]{var}[/meta.value]: ")
                values[var] = val
    elif extra_text:
        # If there are no variables, just append the text to the end of the template
        template_str += "\n\n" + extra_text

    final_prompt = render_template(template_str, values)
    context["next_prompt"] = final_prompt


def cmd_newprompt(context, *args):
    console.print("\n[bold cyan]Create a New Prompt Template[/bold cyan]")
    name = console.input("[bold]Name[/bold] (e.g. Humanize Text): ")
    if not name:
        return

    desc = console.input("[bold]Description[/bold]: ")

    console.print(
        "\n[dim]Enter your template below. Use {{variable}} to create fill-in-the-blanks.[/dim]"
    )
    console.print(
        "[dim]Type [bold white]SAVE[/bold white] on an empty line when you are finished.[/dim]\n"
    )

    lines = []
    while True:
        line = input()
        if line.strip() == "SAVE":
            break
        lines.append(line)

    template = "\n".join(lines)

    if not template.strip():
        console.print("[error]Template cannot be empty. Cancelled.[/error]")
        return

    from anklient.prompts.models import PromptModel

    prompt_mgr = context.get("prompt_mgr")

    new_prompt = PromptModel(
        id=None,
        name=name,
        description=desc,
        category="Custom",
        template=template,
        tags="",
        favorite=False,
        usage_count=0,
        last_used=None,
    )

    new_id = prompt_mgr.add_prompt(new_prompt)
    console.print(
        f"\n[status.done]✓ Successfully saved as Prompt #{new_id}![/status.done]"
    )
    console.print(f"[dim]You can now use it by typing: /use {new_id}[/dim]\n")


def cmd_copy(context, *args):
    last_response = context.get("last_response")
    if not last_response:
        console.print("[error]No recent response to copy.[/error]")
        return
    copy_to_clipboard(last_response)
    console.print("[status.done]Copied to clipboard[/status.done]")


def cmd_paste(context, *args):
    content = paste_from_clipboard()
    if not content:
        console.print("[dim]Clipboard is empty.[/dim]")
        return
    context["next_prompt"] = content


def cmd_save(context, *args):
    if not args:
        console.print("[error]Missing filename. Usage: /save <filename>[/error]")
        return
    last_response = context.get("last_response")
    if not last_response:
        console.print("[error]No recent response to save.[/error]")
        return

    filename = args[0]

    export_dir = pathlib.Path.cwd() / "data" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(last_response)
    console.print(f"[status.done]Saved to {filepath}[/status.done]")


def cmd_status(context, *args):
    console.print()
    console.print("╭─ STATUS ─────────────────────────────────────────────────────╮")
    console.print("│ API           ankLIENT Daemon (localhost:8080)               │")

    client = context.get("client")
    if hasattr(client, "page"):
        # Legacy Playwright mode
        if client.page.page:
            url = client.page.page.url
            console.print(f"│ Page          {url[:43]:<43}│")
    else:
        # API Mode
        console.print(
            "│ Mode          REST API Client                                │"
        )

    console.print("╰──────────────────────────────────────────────────────────────╯")
    console.print()
    console.print("╭─ STATUS ─────────────────────────────────────────────────────╮")
    console.print("│ Browser       Microsoft Edge                                 │")
    console.print(f"│ CDP           {settings.cdp_url:<43}│")

    client = context.get("client")
    if client and client.page.page:
        console.print(
            "│ ChatGPT       Connected                                      │"
        )
        url = client.page.page.url
        console.print(f"│ Page          {url[:43]:<43}│")
    else:
        console.print(
            "│ ChatGPT       Disconnected                                   │"
        )

    console.print("╰──────────────────────────────────────────────────────────────╯")
    console.print()


def cmd_recover(context, *args):
    client = context.get("client")
    if hasattr(client, "page"):
        console.print("[dim]Attempting to recover Playwright connection...[/dim]")
        try:
            conn, page = recover_connection(settings.cdp_url)
            context["client"].page = page
            console.print(
                "[status.done]Successfully recovered connection to ChatGPT tab.[/status.done]"
            )
        except Exception as e:
            console.print(f"[error]Failed to recover: {e}[/error]")
    else:
        console.print(
            "[dim]The daemon auto-recovers. If it crashed, restart the ankLIENT Daemon.[/dim]"
        )


def cmd_file(context, *args):
    client = context.get("client")
    if hasattr(client, "attach_file"):
        if not args:
            console.print("[error]Missing file path. Usage: /file <path>[/error]")
            return

        import os

        filepath = " ".join(args)
        filepath = filepath.strip("'\"")
        filepath = os.path.expanduser(filepath)

        try:
            client.attach_file(filepath)
            console.print(
                f"[status.done]✓ Successfully attached '{filepath}'![/status.done]"
            )
        except Exception as e:
            console.print(f"[error]Failed to attach file: {e}[/error]")
    else:
        console.print(
            "[error]File uploads are currently unsupported in API mode.[/error]"
        )


def register_builtins(router):
    router.register("help", cmd_help)
    router.register("history", cmd_history)
    router.register("prompts", cmd_prompts)
    router.register("use", cmd_use)
    router.register("newprompt", cmd_newprompt)
    router.register("copy", cmd_copy)
    router.register("paste", cmd_paste)
    router.register("save", cmd_save)
    router.register("status", cmd_status)
    router.register("recover", cmd_recover)
    router.register("file", cmd_file)
    router.register("upload", cmd_file)
    router.register("memories", cmd_memories)
    router.register("projects", cmd_projects)
    router.register("generate", cmd_generate)
    router.register("research", cmd_research)
    router.register("vision", cmd_vision)
    router.register("usage", cmd_usage)
    router.register("download", cmd_download)
    router.register("p", cmd_use)


def cmd_download(context, *args):
    """Download a ChatGPT file by its ID."""
    client = context.get("client")
    if not hasattr(client, "download_file"):
        console.print("[error]File downloads are only available in API mode.[/error]")
        return

    if not args:
        console.print("[error]Usage: /download <file_id> [save_path][/error]")
        return

    file_id = args[0].strip()
    save_path = args[1].strip("'\"") if len(args) > 1 else None

    console.print(f"[dim]Fetching download URL for {file_id}...[/dim]")
    try:
        url = client.download_file(file_id)
        if not url:
            console.print("[error]File not found or download unavailable.[/error]")
            return

        if save_path:
            import os
            import urllib.request

            save_path = os.path.expanduser(save_path)
            console.print(f"[dim]Downloading to {save_path}...[/dim]")
            urllib.request.urlretrieve(url, save_path)
            size = os.path.getsize(save_path)
            console.print(
                f"[status.done]✓ Saved ({size:,} bytes) → {save_path}[/status.done]"
            )
        else:
            console.print(f"[bold]Download URL:[/bold] {url}")
    except Exception as e:
        console.print(f"[error]Download failed: {e}[/error]")


def cmd_usage(context, *args):
    """Show ChatGPT account usage and remaining quotas."""
    client = context.get("client")
    if not hasattr(client, "get_usage"):
        console.print("[error]Usage info is only available in API mode.[/error]")
        return

    console.print("[dim]Fetching account usage...[/dim]")
    try:
        data = client.get_usage()
        model = data.get("default_model_slug", "unknown")
        console.print(f"\n[bold]Default Model:[/bold] {model}")

        limits = data.get("limits_progress", [])
        if limits:
            from rich.table import Table

            table = Table(title="Account Limits")
            table.add_column("Feature", style="cyan")
            table.add_column("Remaining", style="green", justify="right")
            table.add_column("Resets After", style="dim")

            for item in limits:
                name = item.get("feature_name", "?")
                remaining = str(item.get("remaining", "?"))
                resets = item.get("reset_after", "—")
                if isinstance(resets, str) and "T" in resets:
                    resets = resets.split("T")[0]
                table.add_row(name, remaining, resets)

            console.print(table)
        else:
            console.print("[dim]No limit data available.[/dim]")

        blocked = data.get("blocked_features", [])
        if blocked:
            console.print(f"\n[warning]Blocked features: {blocked}[/warning]")
    except Exception as e:
        console.print(f"[error]Failed to get usage: {e}[/error]")


def cmd_research(context, *args):
    """Run a Deep Research query via ChatGPT."""
    client = context.get("client")
    if not hasattr(client, "deep_research"):
        console.print("[error]Deep Research is only available in API mode.[/error]")
        return

    if not args:
        console.print("[error]Usage: /research <your research question>[/error]")
        return

    prompt = " ".join(args)
    console.print(f"[dim]Running Deep Research: {prompt[:80]}...[/dim]")
    console.print("[dim]This may take a few minutes...[/dim]")
    try:
        report = client.deep_research(prompt)
        console.print("\n[bold]── Deep Research Report ──[/bold]\n")
        from rich.markdown import Markdown

        console.print(Markdown(report))
    except Exception as e:
        console.print(f"[error]Deep Research failed: {e}[/error]")


def cmd_vision(context, *args):
    """Upload an image and ask ChatGPT about it."""
    client = context.get("client")
    if not hasattr(client, "send_vision"):
        console.print("[error]Vision is only available in API mode.[/error]")
        return

    if not args:
        console.print("[error]Usage: /vision <image_path> [prompt][/error]")
        return

    import base64
    import os

    filepath = args[0].strip("'\"")
    filepath = os.path.expanduser(filepath)
    prompt = " ".join(args[1:]) if len(args) > 1 else "Describe this image in detail."

    if not os.path.exists(filepath):
        console.print(f"[error]File not found: {filepath}[/error]")
        return

    console.print(f"[dim]Uploading {os.path.basename(filepath)}...[/dim]")
    try:
        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        ext = os.path.splitext(filepath)[1].lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/png")

        response = client.send_vision(b64, prompt, mime)
        console.print(f"\n[bold]ChatGPT:[/bold] {response}")
    except Exception as e:
        console.print(f"[error]Vision failed: {e}[/error]")


def cmd_memories(context, *args):
    client = context.get("client")
    if not hasattr(client, "get_memories"):
        console.print(
            "[error]Memories are only supported when using the APIClient.[/error]"
        )
        return

    console.print("[dim]Fetching memories from ChatGPT...[/dim]")
    try:
        memories = client.get_memories()
        if not memories:
            console.print("[dim]No memories found in your account.[/dim]")
            return

        console.print(
            f"\\n[bold cyan]CHATGPT MEMORIES ({len(memories)})[/bold cyan]\\n"
        )
        for m in memories:
            content = (
                m.get("content", {}).get("memory_text", "Unknown")
                if isinstance(m.get("content"), dict)
                else str(m.get("content", ""))
            )
            console.print(f"  [dim]•[/dim] {content}")
        console.print()
    except Exception as e:
        console.print(f"[error]{e}[/error]")


def cmd_projects(context, *args):
    client = context.get("client")
    if not hasattr(client, "get_projects"):
        console.print(
            "[error]Projects are only supported when using the APIClient.[/error]"
        )
        return

    console.print("[dim]Fetching projects from ChatGPT...[/dim]")
    try:
        projects = client.get_projects()
        if not projects:
            console.print("[dim]No projects found in your account.[/dim]")
            return

        console.print(
            f"\\n[bold cyan]CHATGPT PROJECTS ({len(projects)})[/bold cyan]\\n"
        )
        for p in projects:
            name = p.get("name", "Unnamed")
            desc = p.get("description", "")
            console.print(f"  [meta.value]■[/meta.value] [bold]{name}[/bold]")
            if desc:
                console.print(f"      [dim]{desc}[/dim]")
        console.print()
    except Exception as e:
        console.print(f"[error]{e}[/error]")


def cmd_generate(context, *args):
    if not args:
        console.print(
            "[error]Missing prompt. Usage: /generate <image description>[/error]"
        )
        return

    prompt = " ".join(args)
    console.print("\n[dim]Booting Visual Engine for Image Generation...[/dim]")

    from anklient.chat.client import ChatGPTClient
    from anklient.config.settings import settings
    from anklient.drivers.connection import BrowserConnection
    from anklient.drivers.playwright_driver import ChatGPTPage
    from anklient.ui.terminal import TextStreamingLivePanel, print_response

    def print_status(msg: str):
        if msg == "Sending...":
            console.print("[status]Sending to Visual Engine...[/status]")

    try:
        with BrowserConnection(settings.cdp_url) as conn:
            page = ChatGPTPage(conn.browser)
            visual_client = ChatGPTClient(page)

            stream_panel = TextStreamingLivePanel()

            def handle_stream(text: str):
                if not stream_panel.live:
                    stream_panel.start()
                stream_panel.update(text)

            response = visual_client.send_message(
                prompt, on_status=print_status, on_stream=handle_stream
            )
            stream_panel.stop()
            print_response(response)

            # Save to history
            history_repo = context.get("history_repo")
            if history_repo:
                import datetime as dt
                from datetime import datetime

                from anklient.history.models import HistoryItem

                history_repo.save(
                    HistoryItem(
                        id=None,
                        timestamp=datetime.now(dt.timezone.utc),
                        prompt=prompt,
                        response=response.content,
                        category="image",
                        ttft_ms=response.timing.ttft_ms,
                        total_ms=response.timing.total_ms,
                        word_count=response.word_count,
                        char_count=response.char_count,
                        status="success",
                    )
                )
    except Exception as e:
        console.print(f"[error]Image generation failed: {e}[/error]")
        console.print(
            "[dim]Make sure Microsoft Edge is running with remote debugging on port 9222.[/dim]"
        )
