import argparse
import sys
from datetime import datetime
from app.browser.connection import BrowserConnection
from app.browser.chatgpt_page import ChatGPTPage
from app.chat.client import ChatGPTClient
from app.ui.terminal import console, print_header, print_request, print_response, print_error
from app.history.database import init_db
from app.history.models import HistoryItem
from app.history.repository import HistoryRepository
from app.prompts.manager import PromptManager
from app.commands.router import CommandRouter
from app.commands.builtins import register_builtins
from app.files.reader import read_stdin
from app.config.settings import settings

def print_status(msg: str):
    if msg == "Sending...":
        console.print("\n[status]Sending...[/status]")

def run_interactive(client, history_repo, prompt_mgr):
    router = CommandRouter()
    register_builtins(router)
    cmd_context = {
        'history_repo': history_repo,
        'prompt_mgr': prompt_mgr,
        'client': client,
        'next_prompt': None,
        'last_response': None
    }

    print_header()
    import concurrent.futures
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style
    from prompt_toolkit.completion import Completer, Completion

    class SlashCommandCompleter(Completer):
        def __init__(self):
            self.commands = [
                '/help', '/prompts', '/history', '/status', 
                '/recover', '/copy', '/paste', '/save', '/use', '/quit',
                '/file', '/upload'
            ]
            
        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            # Only show dropdown if the user is typing a command at the start of the line
            if text.startswith('/'):
                word = text.split()[-1] if ' ' in text else text
                for cmd in self.commands:
                    if cmd.startswith(word):
                        yield Completion(cmd, start_position=-len(word))

    style = Style.from_dict({'prompt': 'ansimagenta bold'})
    session = PromptSession(
        history=InMemoryHistory(), 
        style=style,
        completer=SlashCommandCompleter(),
        complete_while_typing=True
    )
    
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    
    def get_input():
        return session.prompt("You › ")
    
    while True:
        try:
            if cmd_context.get('next_prompt'):
                prompt = cmd_context['next_prompt']
                cmd_context['next_prompt'] = None
            else:
                prompt = executor.submit(get_input).result().strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[status]Bye![/status]")
            break
        
        if prompt.lower() in {"exit", "quit", "/quit"}:
            console.print("\n[status]Bye![/status]")
            break
        if not prompt:
            continue

        if router.is_command(prompt):
            router.execute(prompt, cmd_context)
            continue

        try:
            print_request(prompt)
            
            from app.ui.terminal import TextStreamingLivePanel
            stream_panel = TextStreamingLivePanel()
            
            def handle_stream(text: str):
                if not stream_panel.live:
                    stream_panel.start()
                stream_panel.update(text)
                
            response = client.send_message(prompt, on_status=print_status, on_stream=handle_stream)
            stream_panel.stop()
            print_response(response)
            
            cmd_context['last_response'] = response.content
            
            history_repo.save(HistoryItem(
                id=None, timestamp=datetime.now(), prompt=prompt, response=response.content,
                category=None, ttft_ms=response.timing.ttft_ms, total_ms=response.timing.total_ms,
                word_count=response.word_count, char_count=response.char_count, status="success"
            ))
        except Exception as e:
            if 'stream_panel' in locals(): stream_panel.stop()
            print_error(e)

def main():
    parser = argparse.ArgumentParser(description="ChatGPT Local CLI")
    parser.add_argument("query", nargs="*", help="Question to ask (one-shot mode)")
    parser.add_argument("--history", action="store_true", help="Show recent history and exit")
    parser.add_argument("--prompts", action="store_true", help="List saved prompts and exit")
    parser.add_argument("--prompt", help="Use a specific prompt template by name")
    
    args = parser.parse_args()
    
    stdin_content = read_stdin()
    
    try:
        db_conn = init_db()
        history_repo = HistoryRepository(db_conn)
        prompt_mgr = PromptManager(db_conn)
        
        if args.history:
            from app.commands.builtins import cmd_history
            cmd_history({'history_repo': history_repo})
            return
            
        if args.prompts:
            from app.commands.builtins import cmd_prompts
            cmd_prompts({'prompt_mgr': prompt_mgr})
            return
            
        console.print("[dim]Connecting to Edge...[/dim]")
        with BrowserConnection(settings.cdp_url) as conn:
            page = ChatGPTPage(conn.browser)
            client = ChatGPTClient(page)

            query_str = " ".join(args.query)
            if stdin_content:
                query_str = f"{query_str}\n\n{stdin_content}" if query_str else stdin_content

            if args.prompt:
                prompts = prompt_mgr.search(args.prompt)
                if not prompts:
                    console.print(f"[error]Prompt template '{args.prompt}' not found.[/error]")
                    return
                template = prompts[0]
                
                if "{{" in template.template:
                    if not query_str:
                        console.print(f"[error]Prompt template '{template.name}' requires input.[/error]")
                        return
                    from app.prompts.templates import extract_variables, render_template
                    vars_needed = extract_variables(template.template)
                    if vars_needed:
                        values = {vars_needed[0]: query_str}
                        query_str = render_template(template.template, values)
                else:
                    query_str = f"{template.template}\n\n{query_str}"
                
                prompt_mgr.increment_usage(template.id)

            if query_str:
                print_header()
                print_request(query_str)
                
                from app.ui.terminal import TextStreamingLivePanel
                stream_panel = TextStreamingLivePanel()
                
                def handle_stream(text: str):
                    if not stream_panel.live:
                        stream_panel.start()
                    stream_panel.update(text)
                    
                response = client.send_message(query_str, on_status=print_status, on_stream=handle_stream)
                stream_panel.stop()
                print_response(response)
                
                history_repo.save(HistoryItem(
                    id=None, timestamp=datetime.now(), prompt=query_str, response=response.content,
                    category=None, ttft_ms=response.timing.ttft_ms, total_ms=response.timing.total_ms,
                    word_count=response.word_count, char_count=response.char_count, status="success"
                ))
            else:
                run_interactive(client, history_repo, prompt_mgr)

    except Exception as e:
        print_error(e)

if __name__ == "__main__":
    main()
