from rich.markdown import Markdown
from rich.panel import Panel


def create_request_panel(prompt: str) -> Panel:
    return Panel(
        prompt,
        title="REQUEST",
        title_align="left",
        border_style="request.border",
        padding=(1, 2),
    )


def create_response_panel(response: str) -> Panel:
    return Panel(
        Markdown(response),
        title="RESPONSE",
        title_align="left",
        border_style="response.border",
        padding=(1, 2),
    )
