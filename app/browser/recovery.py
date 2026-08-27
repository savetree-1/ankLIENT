from app.browser.connection import BrowserConnection
from app.browser.chatgpt_page import ChatGPTPage
import time

def recover_connection(cdp_url: str = "http://127.0.0.1:9222") -> tuple[BrowserConnection, ChatGPTPage]:
    """Attempts to recover the browser connection and page state."""
    conn = BrowserConnection(cdp_url)
    conn.connect()
    
    try:
        page = ChatGPTPage(conn.browser)
        # Try to find editor to ensure page is ready
        page.get_editor()
        return conn, page
    except Exception as e:
        conn.disconnect()
        raise RuntimeError(f"Recovery failed: {e}")
