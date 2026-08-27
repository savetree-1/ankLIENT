import time
from app.browser.chatgpt_page import ChatGPTPage
from app.chat.message import ChatResponse, TimingMetrics
from typing import Callable, Optional
import pathlib

class ChatGPTClient:
    def __init__(self, page: ChatGPTPage):
        self.page = page

    def attach_file(self, filepath: str):
        self.page.attach_file(filepath)

    def send_message(self, prompt: str, on_status: Optional[Callable[[str], None]] = None) -> ChatResponse:
        before = self.page.assistant_texts()
        
        # Track existing generated images
        existing_imgs = self.page.page.locator('img[alt^="Generated image"]').all()
        existing_srcs = set(img.get_attribute("src") for img in existing_imgs)

        send_start = time.perf_counter()
        
        if on_status:
            on_status("Sending...")

        self.page.send_prompt(prompt)

        # Wait for the first text (TTFT)
        deadline = time.time() + 180
        first_text = None

        if on_status:
            on_status("Waiting for response...")

        from app.browser.image_status_detector import ImageGenerationStatusDetector, ImageGenerationStatusEvent

        image_generating = False

        while time.time() < deadline:
            texts = self.page.assistant_texts()
            
            if len(texts) > len(before):
                current = texts[-1].strip()
                if current:
                    first_text = current
                    break
            elif texts:
                old = before[-1].strip() if before else ""
                current = texts[-1].strip()
                if current and current != old:
                    first_text = current
                    break
                    
            # Check if an image appeared instead of text!
            new_imgs = self.page.page.locator('img[alt^="Generated image"]').all()
            if len(new_imgs) > len(existing_imgs):
                first_text = "[Image Generated]"
                break
                
            # Check for live image generation status
            if self.page.page.locator('[data-testid="image-gen-loading-state-headline"]').is_visible():
                image_generating = True
                first_text = "[Image Generation In Progress]"
                break
            
            time.sleep(0.1)

        if not first_text:
            raise TimeoutError("No assistant response appeared.")
                
        first_response_at = time.perf_counter()

        if image_generating:
            from app.ui.terminal import ImageGenerationLivePanel
            live_panel = ImageGenerationLivePanel()
            live_panel.start()
            
            def handle_img_status(event: ImageGenerationStatusEvent):
                if event.status_removed:
                    live_panel.update("Waiting for image result...")
                else:
                    live_panel.update(event.status)
                    
            detector = ImageGenerationStatusDetector(self.page.page)
            # Run the detector until it returns (status removed or timeout)
            detector.run(on_event=handle_img_status, timeout_sec=180)
            
            # Now wait for the actual image to appear
            wait_img_deadline = time.time() + 60
            while time.time() < wait_img_deadline:
                new_imgs = self.page.page.locator('img[alt^="Generated image"]').all()
                if len(new_imgs) > len(existing_imgs):
                    break
                live_panel.update("Waiting for image result...")
                time.sleep(0.1)
                
            live_panel.stop()
            answer = "[Image Generated]"
        else:
            if on_status:
                on_status("Receiving response...")
    
            # Wait for stability
            last_text = first_text
            stable_for = 0.0
    
            while time.time() < deadline:
                texts = self.page.assistant_texts()
                new_imgs = self.page.page.locator('img[alt^="Generated image"]').all()
                
                if len(texts) > len(before):
                    current = texts[-1].strip()
                elif len(new_imgs) > len(existing_imgs):
                    current = "[Image Generated]"
                else:
                    current = texts[-1].strip() if texts else ""
                
                if current == last_text:
                    stable_for += 0.1
                else:
                    last_text = current
                    stable_for = 0.0
    
                if stable_for >= 0.8 and not self.page._is_generating():
                    answer = current
                    break
                    
                time.sleep(0.1)
            else:
                answer = last_text

        finished_at = time.perf_counter()
        
        # Check for new generated images by counting
        new_imgs = self.page.page.locator('img[alt^="Generated image"]').all()
        saved_paths = []
        
        if len(new_imgs) > len(existing_imgs):
            newly_added = new_imgs[len(existing_imgs):]
            for img in newly_added:
                src = img.get_attribute("src")
                if src:
                    try:
                        resp = self.page.page.request.get(src)
                        if resp.status == 200:
                            download_dir = pathlib.Path.home() / "Downloads" / "ChatGPT_Generated"
                            download_dir.mkdir(parents=True, exist_ok=True)
                            
                            idx = 1
                            while (download_dir / f"generated_{idx}.png").exists():
                                idx += 1
                                
                            filepath = download_dir / f"generated_{idx}.png"
                            with open(filepath, "wb") as f:
                                f.write(resp.body())
                            saved_paths.append(str(filepath))
                    except Exception:
                        pass

        if on_status:
            on_status("Complete")

        ttft_ms = (first_response_at - send_start) * 1000
        total_ms = (finished_at - send_start) * 1000
        
        return ChatResponse(
            content=answer,
            timing=TimingMetrics(ttft_ms=ttft_ms, total_ms=total_ms),
            word_count=len(answer.split()),
            char_count=len(answer),
            saved_images=saved_paths
        )
