import time

from playwright.sync_api import Browser, Page

from anklient.interfaces.driver import BrowserDriver

from . import selectors


class ChatGPTPage(BrowserDriver):
    def __init__(self, browser: Browser):
        self.browser = browser
        self.page = self._find_chatgpt_page()

        if not self.page:
            raise RuntimeError(
                "ChatGPT tab not found. Make sure debug Edge is running and ChatGPT is open."
            )

    def _find_chatgpt_page(self) -> Page | None:
        for context in self.browser.contexts:
            for page in context.pages:
                if page.url.startswith("https://chatgpt.com"):
                    return page
        return None

    def _find_send_button(self):
        buttons = self.page.locator("button:visible")
        for i in range(buttons.count()):
            button = buttons.nth(i)
            label = " ".join([
                button.get_attribute("aria-label") or "",
                button.get_attribute("data-testid") or "",
                button.inner_text() or ""
            ]).lower()
            if "send" in label:
                return button
        return None

    def _is_generating(self) -> bool:
        buttons = self.page.locator("button:visible")
        for i in range(buttons.count()):
            button = buttons.nth(i)
            label = " ".join([
                button.get_attribute("aria-label") or "",
                button.get_attribute("data-testid") or "",
                button.inner_text() or ""
            ]).lower()
            if "stop" in label:
                return True
        return False

    def assistant_message_count(self) -> int:
        return self.page.locator(selectors.ASSISTANT_MESSAGES).count()

    def last_assistant_text(self) -> str:
        locator = self.page.locator(selectors.ASSISTANT_MESSAGES)
        if locator.count() > 0:
            return locator.last.inner_text()
        return ""

    def get_editor(self):
            
        editor = self.page.locator(selectors.EDITOR).first
        try:
            editor.wait_for(state="visible", timeout=5000)
        except Exception:
            raise RuntimeError("ChatGPT editor not found.")
        return editor

    def send_prompt(self, prompt: str) -> None:
        editor = self.get_editor()
        editor.click()
        editor.fill(prompt)
        time.sleep(0.15)
        
        send_btn = self._find_send_button()
        if send_btn is None:
            raise RuntimeError("Send button not found.")
        send_btn.click()

    def wait_for_response(self, timeout_sec: int = 180) -> str:
        # Before returning, we must wait for a response to stabilize.
        # This implementation expects the caller to capture the "before" state.
        pass

    def attach_file(self, filepath: str) -> None:
        import os
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_input = self.page.locator('input[type="file"]').first
        if file_input.count() == 0:
            raise RuntimeError("Attachment input not found on the page.")
            
        file_input.set_input_files(filepath)


