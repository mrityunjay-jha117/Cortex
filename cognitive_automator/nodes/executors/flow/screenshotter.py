"""
=============================================================================
 SCREENSHOT EXECUTOR
=============================================================================
This module handles the capture of the host machine's screen.
It stores the visual data for later processing by vision or LLM nodes.

Key Features:
1. Interacts with OS APIs to capture the display buffer.
2. Can crop images based on defined region-of-interest bounding boxes.

Think of this module as the polaroid camera snapping the current state of the screen.
=============================================================================
"""

from ..base import *

def execute_screenshotter(node: ScreenshotterNode, context: dict[str, Any]) -> NodeResult:
    """Captures a sequence of screenshots by scrolling and optionally performs actions on detection."""
    import base64
    import tempfile
    import os
    from io import BytesIO
    from PIL import ImageChops  # type: ignore
    
    needle_img = None
    try:
        images: list[str] = []
        last_img_hash = None
        
        log.info("Screenshotter: mode=%s, detection=%s", node.mode, node.detection_mode)
        
        # Prepare detection image if needed
        if node.detection_mode != DetectionMode.NONE and node.reference_image_b64:
            from PIL import Image
            img_data = base64.b64decode(node.reference_image_b64)
            needle_img = Image.open(BytesIO(img_data))

        # Max limit to prevent infinite loops in UNTIL_END mode
        max_limit = node.n_times if node.mode == ScreenshotMode.N_TIMES else 50
        
        for i in range(max_limit):
            # 1. Capture current screen
            img = pyautogui.screenshot()
            
            # 2. Compare if mode is UNTIL_END
            if node.mode == ScreenshotMode.UNTIL_END:
                if last_img_hash:
                    diff = ImageChops.difference(img, last_img_hash)
                    if not diff.getbbox():
                        log.info("Screenshotter: Page end reached")
                        break
                last_img_hash = img

            # 3. Optional Detection and Action
            if needle_img:
                try:
                    if node.detection_mode == DetectionMode.SINGLE:
                        loc = pyautogui.locateOnScreen(needle_img, confidence=node.confidence, grayscale=node.grayscale)
                        if loc:
                            cx, cy = pyautogui.center(loc)
                            pyautogui.click(cx + node.x_offset, cy + node.y_offset)
                            log.info("Screenshotter: Clicked match at (%d, %d)", cx + node.x_offset, cy + node.y_offset)
                            time.sleep(node.wait_after_click)
                    elif node.detection_mode == DetectionMode.MULTIPLE:
                        # Robust "Click each as it appears": re-scan after each click
                        for _ in range(20): # Safety limit for one page
                            loc = pyautogui.locateOnScreen(needle_img, confidence=node.confidence, grayscale=node.grayscale)
                            if not loc:
                                break
                            cx, cy = pyautogui.center(loc)
                            pyautogui.click(cx + node.x_offset, cy + node.y_offset)
                            log.info("Screenshotter: Clicked match at (%d, %d)", cx + node.x_offset, cy + node.y_offset)
                            time.sleep(node.wait_after_click)
                            # Small extra wait to let UI settle
                            time.sleep(0.2)
                except Exception as detect_exc:
                    log.warning("Screenshotter: Detection error in step %d: %s", i, detect_exc)

            # 4. Store base64
            buf = BytesIO()
            img.save(buf, format="PNG")
            images.append(base64.b64encode(buf.getvalue()).decode())
            
            # 5. Scroll and wait
            log.debug("Screenshotter: step %d, scrolling %d", i+1, node.scroll_amount)
            pyautogui.scroll(node.scroll_amount)
            time.sleep(max(node.wait_per_scroll, 0.2))

        log.info("Screenshotter: captured %d images", len(images))
        return NodeResult(success=True, output_key=node.output_key, output_value=images)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
    finally:
        pass
