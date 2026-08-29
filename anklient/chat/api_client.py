import time
from collections.abc import Callable

from openai import OpenAI

from .message import ChatResponse, TimingMetrics


class APIClient:
    """Client that talks to the local ankLIENT Daemon (which hosts the ankLIENT Engine API server)."""

    def __init__(
        self, base_url: str = "http://127.0.0.1:8080/v1", api_key: str = "sk-local"
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def get_memories(self) -> list[dict]:
        import json
        import urllib.request

        req = urllib.request.Request(
            f"{self.client.base_url}/memories",
            headers={"Authorization": f"Bearer {self.client.api_key}"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data.get("data", [])
        except Exception as e:
            raise RuntimeError(f"Failed to fetch memories: {e}")

    def get_projects(self) -> list[dict]:
        import json
        import urllib.request

        req = urllib.request.Request(
            f"{self.client.base_url}/projects",
            headers={"Authorization": f"Bearer {self.client.api_key}"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data.get("data", [])
        except Exception as e:
            raise RuntimeError(f"Failed to fetch projects: {e}")

    def get_usage(self) -> dict:
        """Fetch account usage limits from the daemon."""
        import json
        import urllib.request

        req = urllib.request.Request(
            f"{self.client.base_url}/chatgpt/usage",
            headers={"Authorization": f"Bearer {self.client.api_key}"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            raise RuntimeError(f"Failed to fetch usage: {e}")

    def send_vision(
        self, b64_image: str, prompt: str, mime_type: str = "image/png"
    ) -> str:
        """Upload an image and ask ChatGPT about it."""
        import json
        import urllib.request

        body = json.dumps(
            {"image": b64_image, "prompt": prompt, "mime_type": mime_type}
        ).encode()
        req = urllib.request.Request(
            f"{self.client.base_url}/chatgpt/vision",
            data=body,
            headers={
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode())
                return data.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Vision request failed: {e}")

    def deep_research(self, prompt: str, model: str = "o4-mini-deep-research") -> str:
        """Run a Deep Research query and return the report."""
        import json
        import urllib.request

        body = json.dumps({"prompt": prompt, "model": model}).encode()
        req = urllib.request.Request(
            f"{self.client.base_url}/chatgpt/research",
            data=body,
            headers={
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                data = json.loads(response.read().decode())
                return data.get("report", "")
        except Exception as e:
            raise RuntimeError(f"Deep Research failed: {e}")

    def download_file(self, file_id: str) -> str | None:
        """Get a temporary download URL for a ChatGPT file."""
        import json
        import urllib.request

        req = urllib.request.Request(
            f"{self.client.base_url}/chatgpt/files/{file_id}/download",
            headers={"Authorization": f"Bearer {self.client.api_key}"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data.get("download_url")
        except Exception:
            return None

    def send_message(
        self,
        prompt: str,
        on_status: Callable[[str], None] | None = None,
        on_stream: Callable[[str], None] | None = None,
    ) -> ChatResponse:
        send_start = time.perf_counter()

        if on_status:
            on_status("Sending...")

        try:
            response = self.client.chat.completions.create(
                model="auto",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            first_text = False
            first_response_at = 0.0
            full_content = ""

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    if not first_text:
                        first_text = True
                        first_response_at = time.perf_counter()
                        if on_status:
                            on_status("Receiving response...")

                    text = chunk.choices[0].delta.content
                    full_content += text
                    if on_stream:
                        on_stream(full_content)

            finished_at = time.perf_counter()

            if on_status:
                on_status("Complete")

            ttft_ms = (first_response_at - send_start) * 1000 if first_text else 0
            total_ms = (finished_at - send_start) * 1000

            return ChatResponse(
                content=full_content,
                timing=TimingMetrics(ttft_ms=ttft_ms, total_ms=total_ms),
                word_count=len(full_content.split()),
                char_count=len(full_content),
                saved_images=[],
            )
        except Exception as e:
            raise RuntimeError(
                f"Daemon API Error: {e}. Is the ankLIENT Daemon running?"
            )
