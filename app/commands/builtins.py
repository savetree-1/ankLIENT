from app.ui.terminal import console
from app.prompts.templates import extract_variables, render_template
from app.clipboard.macos import copy_to_clipboard, paste_from_clipboard
from app.browser.recovery import recover_connection
from app.config.settings import settings
import pathlib
from datetime import datetime

def cmd_help(context, *args):
    console.print("\n[bold cyan]📖 CHATGPT LOCAL MANUAL[/bold cyan]")
    
    console.print("\n[bold white]1. Normal Chatting[/bold white]")
    console.print("   Just type your question at the [bold magenta]You ›[/bold magenta] prompt and press Enter.")
    
    console.print("\n[bold white]2. Attaching Files & Photos[/bold white]")
    console.print("   Step 1: Type [bold cyan]/file <path_to_file>[/bold cyan] and hit Enter.")
    console.print("           (You can drag and drop the file into the terminal)")
    console.print("   Step 2: Type your text prompt and hit Enter to send them both together!")

    console.print("\n[bold white]3. Using the Prompt Library[/bold white]")
    console.print("   Step 1: Type [bold cyan]/prompts[/bold cyan] to see all your saved templates.")
    console.print("   Step 2: Type [bold cyan]/use <id>[/bold cyan] (e.g. [cyan]/use 1[/cyan]) to load one.")
    console.print("   Step 3: Fill in the requested variables. The final prompt will be sent automatically.")

    console.print("\n[bold white]4. Utility Commands[/bold white]")
    console.print("   [bold cyan]/copy[/bold cyan]       Copy the AI's last response to your clipboard")
    console.print("   [bold cyan]/paste[/bold cyan]      Paste text from your clipboard into your prompt")
    console.print("   [bold cyan]/save <f>[/bold cyan]   Save the last response to a file (e.g. /save code.py)")
    console.print("   [bold cyan]/history[/bold cyan]    View your recent chat history")
    console.print("   [bold cyan]/status[/bold cyan]     Check browser connection health")
    console.print("   [bold cyan]/recover[/bold cyan]    Reconnect if the browser tab reloads or disconnects")
    console.print("   [bold cyan]/quit[/bold cyan]       Exit the app\n")

def cmd_history(context, *args):
    history_repo = context.get('history_repo')
    items = history_repo.get_recent(10)
    if not items:
        console.print("[dim]No history found.[/dim]")
        return
        
    for item in reversed(items):
        console.print(f"[dim]#{item.id}[/dim] {item.timestamp.strftime('%H:%M:%S')} - {item.prompt[:50]}...")
    console.print()

def cmd_prompts(context, *args):
    prompt_mgr = context.get('prompt_mgr')
    prompts = prompt_mgr.get_all()
    
    console.print("\n[bold cyan]PROMPT LIBRARY[/bold cyan]\n")
    for p in prompts:
        console.print(f"  [meta.value]{p.id}.[/meta.value] [bold]{p.name}[/bold]")
        console.print(f"     [dim]{p.description}[/dim]")
    console.print()

def cmd_use(context, *args):
    if not args:
        console.print("[error]Missing prompt ID. Usage: /use <id>[/error]")
        return
        
    prompt_id = int(args[0])
    prompt_mgr = context.get('prompt_mgr')
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
    
    if vars_needed:
        console.print("[dim]Fill in the blanks to complete this template:[/dim]")
        for var in vars_needed:
            val = console.input(f"[meta.value]{var}[/meta.value]: ")
            values[var] = val
            
    final_prompt = render_template(template_str, values)
    context['next_prompt'] = final_prompt

def cmd_copy(context, *args):
    last_response = context.get('last_response')
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
    context['next_prompt'] = content

def cmd_save(context, *args):
    if not args:
        console.print("[error]Missing filename. Usage: /save <filename>[/error]")
        return
    last_response = context.get('last_response')
    if not last_response:
        console.print("[error]No recent response to save.[/error]")
        return
        
    filename = args[0]
    
    export_dir = pathlib.Path.cwd() / "data" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(last_response)
    console.print(f"[status.done]Saved to {filepath}[/status.done]")

def cmd_status(context, *args):
    console.print()
    console.print("╭─ STATUS ─────────────────────────────────────────────────────╮")
    console.print("│ Browser       Microsoft Edge                                 │")
    console.print(f"│ CDP           {settings.cdp_url:<43}│")
    
    client = context.get('client')
    if client and client.page.page:
        console.print("│ ChatGPT       Connected                                      │")
        url = client.page.page.url
        console.print(f"│ Page          {url[:43]:<43}│")
    else:
        console.print("│ ChatGPT       Disconnected                                   │")
        
    console.print("╰──────────────────────────────────────────────────────────────╯")
    console.print()

def cmd_recover(context, *args):
    console.print("[dim]Attempting to recover connection...[/dim]")
    try:
        conn, page = recover_connection(settings.cdp_url)
        context['client'].page = page
        console.print("[status.done]Successfully recovered connection to ChatGPT tab.[/status.done]")
    except Exception as e:
        console.print(f"[error]Failed to recover: {e}[/error]")

def cmd_file(context, *args):
    if not args:
        console.print("[error]Missing file path. Usage: /file <path>[/error]")
        return
    
    import os
    filepath = " ".join(args)
    # Strip quotes in case the user dragged and dropped the file into the terminal
    filepath = filepath.strip("'\"")
    filepath = os.path.expanduser(filepath)
    
    client = context.get('client')
    if not client:
        console.print("[error]Client not connected.[/error]")
        return
        
    try:
        client.attach_file(filepath)
        console.print(f"[status.done]✓ Successfully attached '{filepath}'![/status.done]")
        console.print("[dim]Now type your text prompt and press Enter to send it with this file.[/dim]")
    except Exception as e:
        console.print(f"[error]Failed to attach file: {e}[/error]")

def register_builtins(router):
    router.register("help", cmd_help)
    router.register("history", cmd_history)
    router.register("prompts", cmd_prompts)
    router.register("use", cmd_use)
    router.register("copy", cmd_copy)
    router.register("paste", cmd_paste)
    router.register("save", cmd_save)
    router.register("status", cmd_status)
    router.register("recover", cmd_recover)
    router.register("file", cmd_file)
    router.register("upload", cmd_file)
    router.register("p", cmd_use)
