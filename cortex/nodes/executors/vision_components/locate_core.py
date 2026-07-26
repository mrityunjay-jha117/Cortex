"""
=============================================================================
 LOCATE_CORE.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
from typing import Callable, Any
import base64
import time
import pyautogui
from cortex.graph_model import LocateElementNode, LLMConfig
from .locate_core_fallback import handle_locate_fallback

def execute_locate_element(node: LocateElementNode, context: dict[str, Any], 
                           abort_signal: Callable[[], bool] | None = None,
                           emit_info: Callable[[str], None] | None = None,
                           dev_mode: bool = False,
                           llm_config: LLMConfig | None = None) -> NodeResult:
    import io
    from PIL import ImageGrab, Image
    import win32api
    import win32con

    if not node.reference_image_b64:
        return NodeResult(success=False, error="No reference image set on LocateElementNode")

    img_data = base64.b64decode(node.reference_image_b64)
    needle_img = Image.open(io.BytesIO(img_data))

    kwargs = dict(grayscale=node.grayscale, confidence=node.confidence)
    deadline = time.monotonic() + node.timeout_seconds
    primary_success = False
    coords: Any = None

    try:
        v_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        v_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        v_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        v_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        haystack = None
        nw, nh = needle_img.size

        while time.monotonic() < deadline:
            if abort_signal and abort_signal():
                return NodeResult(success=False, error="Aborted")
            
            haystack = ImageGrab.grab(all_screens=True)
            hw, hh = haystack.size
            
            search_haystack = haystack
            if node.region:
                rl, rt, rw, rh = node.region
                pl = int((rl - v_left) * hw / v_width)
                pt = int((rt - v_top) * hh / v_height)
                pw = int(rw * hw / v_width)
                ph = int(rh * hh / v_height)
                
                if pw < nw or ph < nh:
                    log.warning("LocateElement: Region (%dx%d) is smaller than needle (%dx%d). Ignoring region.", pw, ph, nw, nh)
                else:
                    search_haystack = haystack.crop((pl, pt, pl + pw, pt + ph))

            if node.find_all:
                try:
                    matches = list(pyautogui.locateAll(needle_img, search_haystack, **kwargs))
                    if matches:
                        centers = []
                        for m in matches:
                            box_center = pyautogui.center(m)
                            bx, by = box_center.x, box_center.y
                            if node.region:
                                bx += pl
                                by += pt
                            lx = v_left + (bx * v_width / hw)
                            ly = v_top + (by * v_height / hh)
                            centers.append((lx, ly))
                        
                        log.info("LocateElement(find_all): %d matches found", len(centers))
                        primary_success = True
                        coords = centers
                        break
                except (pyautogui.ImageNotFoundException, ValueError):
                    pass
            else:
                try:
                    loc = pyautogui.locate(needle_img, search_haystack, **kwargs)
                    if loc is not None:
                        box_center = pyautogui.center(loc)
                        bx, by = box_center.x, box_center.y
                        if node.region:
                            bx += pl
                            by += pt
                        lx = v_left + (bx * v_width / hw)
                        ly = v_top + (by * v_height / hh)
                        
                        log.info("LocateElement: found at logical (%d, %d)", lx, ly)
                        primary_success = True
                        coords = (lx, ly)
                        break
                except (pyautogui.ImageNotFoundException, ValueError):
                    pass
            
            time.sleep(0.05)

        if primary_success:
            if isinstance(coords, tuple):
                lx, ly = coords
                coords = (lx + node.x_offset, ly + node.y_offset)
            elif isinstance(coords, list):
                coords = [(cx + node.x_offset, cy + node.y_offset) for cx, cy in coords]
            return NodeResult(success=True, output_key=node.output_key, output_value=coords)

        return handle_locate_fallback(node, haystack, v_left, v_top, v_width, v_height, emit_info, dev_mode, llm_config)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
