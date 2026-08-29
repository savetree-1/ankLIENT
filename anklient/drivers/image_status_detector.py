import time
from collections.abc import Callable
from dataclasses import dataclass

from playwright.sync_api import Page


@dataclass
class ImageGenerationStatusEvent:
    status: str | None
    status_removed: bool
    timestamp: float

class ImageGenerationStatusDetector:
    def __init__(self, page: Page):
        self.page = page
        self.selector = '[data-testid="image-gen-loading-state-headline"]'

    def run(self, on_event: Callable[[ImageGenerationStatusEvent], None], timeout_sec: int = 180):
        """
        Observes the DOM for image generation status changes.
        Emits events when the status text changes, and a final event when it's removed.
        Returns when the status element disappears or timeout is reached.
        """
        previous_status = None
        deadline = time.time() + timeout_sec
        missing_count = 0
        
        while time.time() < deadline:
            element = self.page.locator(self.selector)
            
            if element.count() > 0 and element.first.is_visible():
                missing_count = 0
                status = element.first.text_content()
                if status:
                    status = status.strip()
                    
                if status and status != previous_status:
                    on_event(ImageGenerationStatusEvent(
                        status=status,
                        status_removed=False,
                        timestamp=time.time()
                    ))
                    previous_status = status
            else:
                # The element is missing. It could be a React re-mount flicker, or it could be finished.
                # We wait up to 1.5 seconds (15 loops) to confirm it is completely gone.
                missing_count += 1
                if missing_count > 15:
                    on_event(ImageGenerationStatusEvent(
                        status=None,
                        status_removed=True,
                        timestamp=time.time()
                    ))
                    return
            
            time.sleep(0.1)
