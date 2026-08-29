import subprocess


def copy_to_clipboard(text: str):
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

def paste_from_clipboard() -> str:
    process = subprocess.Popen('pbpaste', env={'LANG': 'en_US.UTF-8'}, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    return stdout.decode('utf-8')
