from playwright.sync_api import Browser, sync_playwright

class BrowserConnection:
    def __init__(self, cdp_url: str = "http://127.0.0.1:9222"):
        self.cdp_url = cdp_url
        self._playwright = None
        self.browser: Browser | None = None

    def connect(self):
        if self._playwright is None:
            self._playwright = sync_playwright().start()
        
        try:
            self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to CDP at {self.cdp_url}: {e}")
        return self.browser
    
    def disconnect(self):
        if self.browser:
            self.browser.close()
            self.browser = None
        
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
