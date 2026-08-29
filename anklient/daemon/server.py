import asyncio
import logging

from anklient.engine.config import Config
from anklient.engine.service import run_service


async def start_daemon(cdp_port: int = 9222, api_port: int = 8080):
    """
    Boots up the background API and MCP server using the embedded engine.
    """
    print(f"Starting ankLIENT Daemon on port {api_port}...")
    
    config = Config.load()
    config.server.port = api_port
    config.chrome.cdp_port = cdp_port
    config.log.level = "INFO"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

    await run_service(config)

if __name__ == "__main__":
    asyncio.run(start_daemon())
