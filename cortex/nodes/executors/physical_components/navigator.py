"""
=============================================================================
 NAVIGATOR.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
def execute_navigator(node: NavigatorNode, context: dict[str, Any]) -> NodeResult:
    try:
        if node.reference_image_b64:
            import base64
            import io
            from PIL import Image
            img_data = base64.b64decode(node.reference_image_b64)
            needle_img = Image.open(io.BytesIO(img_data))
            
            try:
                loc = pyautogui.locateOnScreen(needle_img, confidence=node.confidence, grayscale=False)
                if loc is not None:
                    cx, cy = pyautogui.center(loc)
                    cx += node.x_offset
                    cy += node.y_offset
                    log.info("Navigator: focusing at (%d, %d)", cx, cy)
                    pyautogui.click(cx, cy)
                    time.sleep(0.1)
                else:
                    log.warning("Navigator: focus image not found, proceeding anyway")
            except pyautogui.ImageNotFoundException:
                log.warning("Navigator: focus image not found, proceeding anyway")

        log.info("Navigator: action=%s repeat=%d", node.action, node.repeat)
        for _ in range(max(1, node.repeat)):
            pyautogui.press(node.action.value)
            time.sleep(0.1)

        return NodeResult(success=True)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
