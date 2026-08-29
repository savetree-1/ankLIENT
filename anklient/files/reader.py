import sys


def read_stdin() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def read_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
