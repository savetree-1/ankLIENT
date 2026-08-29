from collections.abc import AsyncGenerator

from anklient.engine.cdp_driver import CDPDriver
from anklient.interfaces.driver import BrowserDriver


class RawCDPAdapter(BrowserDriver):
    """Adapter wrapping the embedded engine's CDPDriver to match our interface."""

    def __init__(self, port: int = 9222):
        self.driver = CDPDriver(cdp_port=port, tab_mode="owned")

    async def connect(self) -> None:
        await self.driver.connect()

    async def close(self) -> None:
        pass

    async def send_message(self, text: str) -> AsyncGenerator[str, None]:
        await self.driver.ensure_token()
        async for chunk in self.driver.send_and_stream(text):
            if chunk.delta:
                yield chunk.delta

    async def get_memories(self) -> list[dict]:
        return await self.driver.get_memories()

    async def get_projects(self) -> list[dict]:
        return await self.driver.get_projects()
