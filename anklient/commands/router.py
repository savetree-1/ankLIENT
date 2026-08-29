import shlex
from collections.abc import Callable


class CommandRouter:
    def __init__(self):
        self.commands: dict[str, Callable] = {}

    def register(self, name: str, handler: Callable):
        self.commands[name] = handler

    def is_command(self, text: str) -> bool:
        return text.startswith("/")

    def execute(self, text: str, context: dict) -> bool:
        """Executes a command. Returns True if handled, False otherwise."""
        if not self.is_command(text):
            return False

        parts = shlex.split(text)
        cmd_name = parts[0][1:].lower()  # remove '/'
        args = parts[1:]

        if cmd_name in self.commands:
            self.commands[cmd_name](context, *args)
            return True
        else:
            print(f"Unknown command: /{cmd_name}. Type /help for available commands.")
            return True
