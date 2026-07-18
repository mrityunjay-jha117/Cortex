"""
nodes/executors.py — Execution logic for every node type.

Each executor receives the node model + the mutable execution context dict.
Returns NodeResult(success, output_key, output_value, next_edge_label).

PyAutoGUI calls are wrapped with FAILSAFE guard.
"""

import base64
import csv
import logging
import sys
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Callable

import pyautogui  # type: ignore
import pyperclip  # type: ignore
from PIL import Image

from cognitive_automator.graph_model import (
    ActionGraph,
    BranchNode,
    CSVDataLoaderNode,
    ClipboardNode,
    CompareNode,
    CompareOp,
    DynamicIterateNode,
    EdgeLabel,
    FileDropNode,
    ForLoopNode,
    GenerativeOCRNode,
    GlobalEndNode,
    GlobalStartNode,
    IterateNode,
    KeyboardAction,
    KeyboardNode,
    LLMConfig,
    LLMExtractionNode,
    LLMGenerativeNode,
    LLMJudgmentNode,
    LLMProvider,
    LocateElementNode,
    LocateAndClickNode,
    MouseNode,
    MouseAction,
    ClipboardAction,
    NavigatorNode,
    WaitNode,
    VisionExtractionNode,
    VisionImageNode,
    WriteFileNode,
    CSVWriterNode,
    ScreenshotterNode,

    ScreenshotMode,
    DetectionMode,
)
from cognitive_automator.llm.structured import (
    run_extraction,
    run_generative,
    run_judgment,
    run_ocr,
    run_vision_extraction,
)
from cognitive_automator.llm.templates import render_prompt

log = logging.getLogger(__name__)

# Enforce PyAutoGUI FAILSAFE at import time — non-negotiable
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15   # Increased for better stability between focus/type transitions


@dataclass
class NodeResult:
    success: bool
    next_edge: EdgeLabel = EdgeLabel.DEFAULT
    error: str = ""
    # Key/value written into the execution context
    output_key: str = ""
    output_value: Any = None
    healed: bool = False


# ---------------------------------------------------------------------------
# Physical IO Executors
# ---------------------------------------------------------------------------

def execute_mouse(node: MouseNode, context: dict[str, Any]) -> NodeResult:
    try:
        # Resolve coordinates — vision override takes priority
        x, y = node.x_coord, node.y_coord
        if node.vision_node_id:
            # Check if vision_node_id exists as a key in context
            if node.vision_node_id in context:
                coords = context[node.vision_node_id]
                if isinstance(coords, (tuple, list)) and len(coords) >= 2:
                    x, y = int(coords[0]), int(coords[1])
                    log.debug("MouseNode resolved vision ID '%s' to (%d, %d)", node.vision_node_id, x, y)
                else:
                    return NodeResult(success=False, 
                                     error=f"Vision node '{node.vision_node_id}' output is not a coordinate: {coords}")
            else:
                # If not a key, maybe it's a node ID? Runtime should have mapped it to context already,
                # but we'll be explicit about the failure.
                return NodeResult(success=False, 
                                 error=f"Vision output key '{node.vision_node_id}' not found in context. "
                                       f"Current keys: {list(context.keys())}")

        # Apply offsets (cumulative with vision if provided)
        # MouseNode is the SOLE place where offsets should be applied.
        x += node.x_offset
        y += node.y_offset

        log.info("MouseNode: action=%s target=(%d, %d)", node.action, x, y)

        if node.action == MouseAction.CLICK:
            pyautogui.click(x, y, button=node.button, duration=node.duration)
            time.sleep(0.3) # Critical delay to ensure input focus is gained
        elif node.action == MouseAction.DOUBLE_CLICK:
            pyautogui.doubleClick(x, y, duration=node.duration)
            time.sleep(0.3)
        elif node.action == MouseAction.RIGHT_CLICK:
            pyautogui.rightClick(x, y, duration=node.duration)
        elif node.action == MouseAction.MOVE_TO:
            pyautogui.moveTo(x, y, duration=max(node.duration, 0.1))
        elif node.action == MouseAction.DRAG_TO:
            pyautogui.dragTo(node.dest_x, node.dest_y, duration=max(node.duration, 0.2),
                             button=node.button)
        elif node.action == MouseAction.SCROLL:
            log.info("MouseNode: scroll amount=%d at (%d, %d)", node.scroll_amount, x, y)
            pyautogui.scroll(node.scroll_amount, x=x, y=y)
        return NodeResult(success=True)
    except pyautogui.FailSafeException:
        raise   # propagate — this is an emergency stop
    except Exception as exc:  # noqa: BLE001
        return NodeResult(success=False, error=str(exc))


def execute_navigator(node: NavigatorNode, context: dict[str, Any]) -> NodeResult:
    try:
        # 1. Optional Focus Step
        if node.reference_image_b64:
            import base64
            import tempfile
            import os
            img_data = base64.b64decode(node.reference_image_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(img_data)
                tmp_path = f.name
            
            try:
                # Use standard confidence for focusing
                loc = pyautogui.locateOnScreen(tmp_path, confidence=node.confidence, grayscale=False)
                if loc is not None:
                    cx, cy = pyautogui.center(loc)
                    cx += node.x_offset
                    cy += node.y_offset
                    log.info("Navigator: focusing at (%d, %d)", cx, cy)
                    pyautogui.click(cx, cy)
                    time.sleep(0.3) # Wait for focus
                else:
                    log.warning("Navigator: focus image not found, proceeding anyway")
            finally:
                os.unlink(tmp_path)

        # 2. Navigation Step
        log.info("Navigator: action=%s repeat=%d", node.action, node.repeat)
        for _ in range(max(1, node.repeat)):
            pyautogui.press(node.action.value)
            time.sleep(0.1)

        return NodeResult(success=True)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_keyboard(node: KeyboardNode, context: dict[str, Any]) -> NodeResult:
    try:
        from cognitive_automator.llm.templates import render_prompt
        
        # Robust text resolution: prefer 'text' field, fallback to first item in 'keys'
        raw_text = node.text
        if not raw_text and node.keys and node.action in (KeyboardAction.TYPEWRITE, KeyboardAction.PASTE):
            raw_text = node.keys[0]
            
        if node.action == KeyboardAction.TYPEWRITE:
            text = render_prompt(raw_text, context)
            log.info("Keyboard: typewrite '%s'", text[:30] + ("..." if len(text) > 30 else ""))
            pyautogui.typewrite(text, interval=node.interval)
        elif node.action == KeyboardAction.PRESS:
            log.info("Keyboard: press '%s'", node.key)
            pyautogui.press(node.key)
        elif node.action == KeyboardAction.HOTKEY:
            log.info("Keyboard: hotkey %s", node.keys)
            pyautogui.hotkey(*node.keys)
        elif node.action == KeyboardAction.PASTE:
            text = render_prompt(raw_text, context)
            log.info("Keyboard: paste '%s'", text[:30] + ("..." if len(text) > 30 else ""))
            pyperclip.copy(text)
            modifier = "command" if sys.platform == "darwin" else "ctrl"
            pyautogui.hotkey(modifier, "v")
        elif node.action == KeyboardAction.SELECT_ALL:
            log.info("Keyboard: select all")
            modifier = "command" if sys.platform == "darwin" else "ctrl"
            pyautogui.hotkey(modifier, "a")
            time.sleep(0.2)  # Stability delay for OS to register selection
        return NodeResult(success=True)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))



def execute_file_drop(node: FileDropNode, context: dict[str, Any]) -> NodeResult:
    try:
        # Resolve coordinates
        x, y = node.x_coord, node.y_coord
        if node.vision_node_id:
            if node.vision_node_id in context:
                coords = context[node.vision_node_id]
                if isinstance(coords, (tuple, list)) and len(coords) >= 2:
                    x, y = int(coords[0]), int(coords[1])
                else:
                    return NodeResult(success=False, 
                                     error=f"Vision node '{node.vision_node_id}' output is not a coordinate")
            else:
                return NodeResult(success=False, 
                                 error=f"Vision node '{node.vision_node_id}' not found in context")

        # Apply offsets
        x += node.x_offset
        y += node.y_offset

        # 1. Click target to open dialog
        log.debug("FileDrop: clicking target at (%d, %d)", x, y)
        pyautogui.click(x, y)
        time.sleep(node.wait_after_click)

        # 2. Type path and Enter
        # We use hotkey 'ctrl+a' then 'backspace' to ensure field is clear in some apps
        # but usually typing the path directly works.
        from cognitive_automator.llm.templates import render_prompt
        path = render_prompt(node.file_path, context)
        log.debug("FileDrop: typing path %s", path)
        
        # Using write/paste logic for speed
        pyperclip.copy(path)
        modifier = "command" if sys.platform == "darwin" else "ctrl"
        pyautogui.hotkey(modifier, "v")
        time.sleep(0.3)
        pyautogui.press("enter")
        
        return NodeResult(success=True, output_key=node.output_key, output_value=path)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_clipboard(node: ClipboardNode, context: dict[str, Any]) -> NodeResult:
    try:
        if node.action == ClipboardAction.READ:
            text = pyperclip.paste()
            return NodeResult(success=True, output_key="clipboard", output_value=text)
        else:  # WRITE
            text = node.write_text
            if node.source_output_key and node.source_output_key in context:
                text = str(context[node.source_output_key])
            pyperclip.copy(text)
            return NodeResult(success=True)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# Vision Executors
# ---------------------------------------------------------------------------

def execute_locate_element(node: LocateElementNode, context: dict[str, Any], 
                           abort_signal: Callable[[], bool] | None = None,
                           emit_info: Callable[[str], None] | None = None,
                           dev_mode: bool = False,
                           llm_config: LLMConfig | None = None) -> NodeResult:
    import tempfile
    import os
    import win32api
    import win32con
    import ctypes
    from PIL import ImageGrab

    if not node.reference_image_b64:
        return NodeResult(success=False, error="No reference image set on LocateElementNode")

    img_data = base64.b64decode(node.reference_image_b64)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(img_data)
        tmp_path = f.name

    kwargs = dict(grayscale=node.grayscale, confidence=node.confidence)
    # Only add region if it's actually set, and it must be scaled to physical pixels
    # since haystack is captured in physical pixels.
    # For now, if region is null, we pass nothing.
    
    deadline = time.monotonic() + node.timeout_seconds
    
    primary_success = False
    coords = None

    try:
        # Get virtual screen metrics (logical)
        v_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        v_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        v_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        v_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        haystack = None
        needle_img = Image.open(tmp_path)
        nw, nh = needle_img.size

        while time.monotonic() < deadline:
            if abort_signal and abort_signal():
                return NodeResult(success=False, error="Aborted")
            
            # Capture current virtual desktop (physical pixels)
            haystack = ImageGrab.grab(all_screens=True)
            hw, hh = haystack.size
            
            # If node has a region, scale it from logical to physical for PIL crop
            search_haystack = haystack
            if node.region:
                rl, rt, rw, rh = node.region
                # Scale logical -> physical
                # (Assuming logical virtual space maps linearly to physical haystack)
                pl = int((rl - v_left) * hw / v_width)
                pt = int((rt - v_top) * hh / v_height)
                pw = int(rw * hw / v_width)
                ph = int(rh * hh / v_height)
                
                # Ensure the region is within haystack bounds and larger than needle
                if pw < nw or ph < nh:
                    log.warning("LocateElement: Region (%dx%d) is smaller than needle (%dx%d). Ignoring region.", pw, ph, nw, nh)
                else:
                    search_haystack = haystack.crop((pl, pt, pl + pw, pt + ph))
                    # Note: We must adjust found coordinates by (pl, pt) later

            if node.find_all:
                try:
                    matches = list(pyautogui.locateAll(needle_img, search_haystack, **kwargs))
                    if matches:
                        centers = []
                        for m in matches:
                            box_center = pyautogui.center(m)
                            # Adjust for region crop if active
                            bx, by = box_center.x, box_center.y
                            if node.region:
                                bx += pl
                                by += pt
                            # Scale physical -> logical virtual
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
                        # Adjust for region crop if active
                        bx, by = box_center.x, box_center.y
                        if node.region:
                            bx += pl
                            by += pt
                        # Scale physical -> logical virtual
                        lx = v_left + (bx * v_width / hw)
                        ly = v_top + (by * v_height / hh)
                        
                        log.info("LocateElement: found at logical (%d, %d)", lx, ly)
                        primary_success = True
                        coords = (lx, ly)
                        break
                except (pyautogui.ImageNotFoundException, ValueError):
                    pass
            
            time.sleep(0.3)

        # Cleanup primary temp file
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        if primary_success:
            # Apply manual offsets to the primary search result
            if isinstance(coords, tuple):
                lx, ly = coords
                coords = (lx + node.x_offset, ly + node.y_offset)
            elif isinstance(coords, list):
                coords = [(cx + node.x_offset, cy + node.y_offset) for cx, cy in coords]
            
            return NodeResult(success=True, output_key=node.output_key, output_value=coords)

        # --- Fallback Mechanism ---
        if node.use_fallback and not dev_mode and llm_config:
            prompt = node.fallback_prompt or f"detect {node.label or 'the element'}"
            provider = node.fallback_provider_override or llm_config.fallback_provider
            model = node.fallback_model_override or llm_config.fallback_model
            
            log.info("LocateElement primary failed. Attempting AI Fallback [v3] [Provider: %s, Model: %s] with prompt: '%s'", 
                     provider, model, prompt)
            
            # Use the already captured haystack if available, else capture fresh
            if not haystack:
                haystack = ImageGrab.grab(all_screens=True)
            
            sw_phys, sh_phys = haystack.size
            buffered = BytesIO()
            haystack.save(buffered, format="PNG")
            screenshot_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            try:
                fb_data = run_vlm_fallback(screenshot_b64, prompt, provider, model, llm_config)
                if fb_data:
                    nx_click, ny_click = fb_data["click"]
                    nx_center, ny_center = fb_data["center"]
                    xmin, ymin, xmax, ymax = fb_data["bbox_raw"]
                    
                    log.debug("AI Fallback RAW: click=%s center=%s bbox=%s", 
                              (nx_click, ny_click), (nx_center, ny_center), fb_data["bbox_raw"])

                    # 1. Calculate logical coordinates for interaction
                    # We use nx_click (internal point) as the base for the click
                    cx = int(v_left + (nx_click * v_width / 1000.0))
                    cy = int(v_top + (ny_click * v_height / 1000.0))
                    
                    healed_flag = False
                    
                    # --- Self-Healing Mechanism ---
                    if node.auto_heal:
                        log.info("Self-healing: Updating node with AI bounding box...")
                        try:
                            # Update logical center for future TEMPLATE searches
                            node.x_coord = int(v_left + (nx_center * v_width / 1000.0))
                            node.y_coord = int(v_top + (ny_center * v_height / 1000.0))
                            
                            # Physical bbox crop
                            left_p = int(xmin * sw_phys / 1000.0)
                            top_p = int(ymin * sh_phys / 1000.0)
                            right_p = int(xmax * sw_phys / 1000.0)
                            bottom_p = int(ymax * sh_phys / 1000.0)
                            
                            new_patch = haystack.crop((max(0, left_p-2), max(0, top_p-2), 
                                                       min(sw_phys, right_p+2), min(sh_phys, bottom_p+2)))
                            
                            patch_buf = BytesIO()
                            new_patch.save(patch_buf, format="PNG")
                            node.reference_image_b64 = base64.b64encode(patch_buf.getvalue()).decode("utf-8")
                            
                            log.info("Self-healing SUCCESSFUL: Node healed at logical (%d, %d).", 
                                     node.x_coord, node.y_coord)
                            healed_flag = True
                        except Exception as heal_exc:
                            log.error("Self-healing FAILED: %s", heal_exc)

                    # Apply manual offsets to the internal click point
                    cx += node.x_offset
                    cy += node.y_offset

                    log.info("AI Fallback SUCCESS: Element found. Final logical coordinates at (%d, %d).", cx, cy)
                    if emit_info:
                        emit_info("AI Fallback completed successfully.")
                    return NodeResult(success=True, output_key=node.output_key, output_value=(cx, cy), healed=healed_flag)
                else:
                    log.warning("AI Fallback FAILED: AI could not locate the element.")
            except Exception as fb_exc:
                log.error("AI Fallback CRITICAL ERROR: %s", fb_exc, exc_info=True)

        return NodeResult(success=False, error=f"Element not found within {node.timeout_seconds}s")
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_locate_and_click(node: LocateAndClickNode, context: dict[str, Any], 
                           abort_signal: Callable[[], bool] | None = None,
                           emit_info: Callable[[str], None] | None = None,
                           dev_mode: bool = False,
                           llm_config: LLMConfig | None = None) -> NodeResult:
    # 1. Run Locate logic
    res = execute_locate_element(node, context, abort_signal, emit_info, dev_mode, llm_config)
    if not res.success:
        return res
    
    # 2. Perform Mouse Action
    try:
        coords = res.output_value
        if not coords:
             return NodeResult(success=False, error="Locate succeeded but no coordinates returned.")
             
        # If find_all was used, we click ALL matches
        if isinstance(coords, list):
            log.info("LocateAndClick: performing %s on %d matches", node.action, len(coords))
            for i, (lx, ly) in enumerate(coords):
                if abort_signal and abort_signal():
                    return NodeResult(success=False, error="Aborted during multi-click")
                _perform_mouse_action(node, int(lx), int(ly))
                if i < len(coords) - 1:
                    time.sleep(node.wait_after_click)
        else:
            lx, ly = coords
            log.info("LocateAndClick: performing %s at logical (%d, %d)", node.action, lx, ly)
            _perform_mouse_action(node, int(lx), int(ly))
            
        return res # preserve output_key/value/healed from locate result
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=f"Click failed: {exc}")

def _perform_mouse_action(node: LocateAndClickNode, x: int, y: int) -> None:
    if node.action == MouseAction.CLICK:
        pyautogui.click(x, y, button=node.button, duration=node.duration)
    elif node.action == MouseAction.DOUBLE_CLICK:
        pyautogui.doubleClick(x, y, duration=node.duration)
    elif node.action == MouseAction.RIGHT_CLICK:
        pyautogui.rightClick(x, y, duration=node.duration)
    elif node.action == MouseAction.MOVE_TO:
        pyautogui.moveTo(x, y, duration=max(node.duration, 0.1))
    elif node.action == MouseAction.SCROLL:
        # Note: LocateAndClickNode doesn't have scroll_amount in model yet, 
        # but we could add it if needed. For now we use 0 or skip.
        pass
    time.sleep(node.wait_after_click)


def run_vlm_fallback(img_b64: str, prompt: str,
                     provider: LLMProvider, model: str, config: LLMConfig) -> dict[str, tuple[float, float]] | None:
    """Calls VLM to detect object and returns normalized 'click', 'center', and 'bbox_raw'."""
    from cognitive_automator.llm.client import create_client
    import json
    import re

    system_prompt = (
        "You are an expert UI automation assistant. Your task is to locate elements on a screen and determine the exact click point for interaction.\n"
        "When asked to find an element, return a JSON list of objects containing:\n"
        "- \"bbox_2d\": [ymin, xmin, ymax, xmax] (normalized 0-1000)\n"
        "- \"point\": [y, x] (normalized 0-1000) - The EXACT point to click for interaction. Usually the center, but adjust if the description implies a specific part.\n"
        "- \"label\": element description.\n"
        "Example: [{\"bbox_2d\": [100, 200, 300, 400], \"point\": [200, 300], \"label\": \"login button\"}]"
    )

    client = create_client(
        provider=provider,
        model=model,
        temperature=0.0,
        max_tokens=512,
        timeout=config.request_timeout,
        openrouter_api_key_env=config.openrouter_api_key_env,
    )

    response = client.complete(
        user_prompt=f"Task: {prompt}\nReturn the bounding box and exact click point for this element.",
        system_prompt=system_prompt,
        images_b64=[img_b64]
    )

    text = response.text.strip()
    log.debug("VLM Fallback Raw Response: %s", text)

    # Clean markdown
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)

    try:
        data = json.loads(text)
        if not isinstance(data, list) or len(data) == 0:
            return None
        
        item = data[0]
        point = item.get("point")
        bbox = item.get("bbox_2d")

        if not bbox or len(bbox) != 4:
            return None
            
        xmin, ymin, xmax, ymax = bbox
        cx_norm = (xmin + xmax) / 2.0
        cy_norm = (ymin + ymax) / 2.0

        if point and len(point) == 2:
            px_norm, py_norm = point
            click_pt = (float(px_norm), float(py_norm))
        else:
            click_pt = (float(cx_norm), float(cy_norm))
            
        return {
            "click": click_pt,
            "center": (float(cx_norm), float(cy_norm)),
            "bbox_raw": (float(xmin), float(ymin), float(xmax), float(ymax))
        }
    except Exception as e:
        log.error("Failed to parse VLM fallback response: %s", e)
        return None


def execute_vision_image(node: VisionImageNode, context: dict[str, Any]) -> NodeResult:
    """Loads an image file and returns base64."""
    import base64
    import os
    try:
        path = render_prompt(node.file_path, context)
        if not os.path.exists(path):
            return NodeResult(success=False, error=f"Image file not found: {path}")
        
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        
        log.info("VisionImageNode: Loaded %s", path)
        return NodeResult(success=True, output_key=node.output_key, output_value=encoded)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_generative_ocr(node: GenerativeOCRNode, context: dict[str, Any],
                           llm_config: LLMConfig) -> NodeResult:
    try:
        text = run_ocr(node, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=text)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_vision_extraction(node: VisionExtractionNode, context: dict[str, Any],
                              llm_config: LLMConfig) -> NodeResult:
    try:
        data = run_vision_extraction(node, context, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=data)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# LLM Executors
# ---------------------------------------------------------------------------

def execute_judgment(node: LLMJudgmentNode, context: dict[str, Any],
                     llm_config: LLMConfig) -> NodeResult:
    try:
        result = run_judgment(node, context, llm_config)
        bool_result: bool = result["result"]
        log.info("LLMJudgment: result=%s confidence=%.2f reasoning=%s",
                 bool_result, result.get("confidence", 1.0), result.get("reasoning", "")[:80])
        next_edge = EdgeLabel.TRUE if bool_result else EdgeLabel.FALSE
        return NodeResult(
            success=True,
            next_edge=next_edge,
            output_key="judgment_result",
            output_value=result,
        )
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_extraction(node: LLMExtractionNode, context: dict[str, Any],
                       llm_config: LLMConfig) -> NodeResult:
    try:
        data = run_extraction(node, context, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=data)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_generative(node: LLMGenerativeNode, context: dict[str, Any],
                       llm_config: LLMConfig) -> NodeResult:
    try:
        text = run_generative(node, context, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=text)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# Flow Executors
# ---------------------------------------------------------------------------

def execute_wait(node: WaitNode, context: dict[str, Any],
                 abort_signal: Callable[[], bool] | None = None,
                 emit_info: Callable[[str], None] | None = None,
                 dev_mode: bool = False,
                 llm_config: LLMConfig | None = None) -> NodeResult:
    try:
        if node.wait_for_image_b64:
            import base64
            import tempfile
            import os
            
            log.info("WaitNode: Waiting for image to appear (timeout=%.1fs)", node.timeout_seconds)
            
            img_data = base64.b64decode(node.wait_for_image_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(img_data)
                tmp_path = f.name
            
            deadline = time.monotonic() + node.timeout_seconds
            found = False
            try:
                while time.monotonic() < deadline:
                    if abort_signal and abort_signal():
                        return NodeResult(success=False, error="Aborted")
                    loc = pyautogui.locateOnScreen(tmp_path, confidence=node.wait_confidence,
                                                    grayscale=False)
                    if loc:
                        log.info("WaitNode: Image found successfully.")
                        found = True
                        break
                    time.sleep(node.poll_interval)
                
                if found:
                    return NodeResult(success=True)

                # --- Fallback for WaitNode ---
                # Check if LocateElement style fallback should be tried here too
                # For now, let's keep it consistent if the user enables it on a linked LocateNode
                # but WaitNode doesn't have a 'use_fallback' field yet in graph_model.
                # If we want WaitNode to support it, we'd need to add the field there too.
                # However, if LocateElement is used as a 'wait' (with its timeout), it already has it.

                return NodeResult(success=False, error="Timed out waiting for image")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        else:
            remaining = node.static_seconds or 1.0
            log.info("WaitNode: Sleeping for %.1f seconds", remaining)
            while remaining > 0:
                if abort_signal and abort_signal():
                    return NodeResult(success=False, error="Aborted")
                step = min(remaining, 0.1)
                time.sleep(step)
                remaining -= step
            return NodeResult(success=True)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_branch(node: BranchNode, context: dict[str, Any]) -> NodeResult:
    value = context.get(node.condition_key)
    if value is None:
        return NodeResult(success=False,
                          error=f"BranchNode: condition key '{node.condition_key}' not in context")
    is_true = bool(value) if not isinstance(value, dict) else bool(value.get("result", False))
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if is_true else EdgeLabel.FALSE)


def execute_iterate(node: IterateNode, context: dict[str, Any]) -> NodeResult:
    """
    Manages loop state in the context under '_iterate_{node_id}'.
    Returns LOOP_BODY edge while items remain, LOOP_END when exhausted.
    """
    state_key = f"_iterate_{node.id}"
    state = context.get(state_key, {"index": 0, "items": None})

    if state["items"] is None:
        # First call: load items
        if node.csv_file_path:
            items = _load_csv_column(node.csv_file_path, node.csv_column)
        else:
            items = list(node.items)
        state["items"] = items
        state["index"] = 0

    items: list[str] = state["items"]
    idx: int = state["index"]

    if idx >= len(items):
        # Reset state for potential re-run
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    current_item = items[idx]
    state["index"] = idx + 1
    context[state_key] = state

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_item,
    )


def execute_dynamic_iterate(node: DynamicIterateNode, context: dict[str, Any]) -> NodeResult:
    """
    Iterates over a runtime list in context[source_key].
    Items can be (cx, cy) tuples (from LocateAll) or strings (from OCR/LLM).
    Returns LOOP_BODY with the current item, LOOP_END when exhausted.
    """
    state_key = f"_dyn_iterate_{node.id}"
    state = context.get(state_key, {"index": 0, "items": None})

    if state["items"] is None:
        raw = context.get(node.source_key, [])
        state["items"] = list(raw) if isinstance(raw, (list, tuple)) else [raw]
        state["index"] = 0

    items: list = state["items"]
    idx: int = state["index"]

    if idx >= len(items):
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    current_item = items[idx]
    state["index"] = idx + 1
    context[state_key] = state

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_item,
    )


def execute_for_loop(node: ForLoopNode, context: dict[str, Any], graph: ActionGraph) -> NodeResult:
    """
    C++ style counter loop: for (int i = start; i < end; i += step)
    Data is resolved from incoming DATA_BIND edges.
    """
    state_key = f"_for_{node.id}"
    current_val = context.get(state_key)

    # Resolve data sources from graph edges
    data_sources = [e.source_id for e in graph.edges if e.target_id == node.id and e.label == EdgeLabel.DATA_BIND]
    
    # Cap the loop end based on data length if sources exist
    loop_end = node.end
    for src_id in data_sources:
        src_node = graph.nodes.get(src_id)
        if src_node and hasattr(src_node, "output_key"):
            key = src_node.output_key
            if key in context:
                data = context[key]
                if isinstance(data, (list, dict)):
                    loop_end = min(loop_end, len(data))

    if current_val is None:
        current_val = node.start
    
    # Condition check (continues while i < loop_end)
    should_continue = False
    if node.step > 0:
        should_continue = current_val < loop_end
    else:
        should_continue = current_val > loop_end

    if not should_continue:
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    # Prepare for next pass
    next_val = current_val + node.step
    context[state_key] = next_val

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_val,
    )


def execute_csv_data_loader(node: CSVDataLoaderNode, context: dict[str, Any]) -> NodeResult:
    """Loads CSV into list of dicts."""
    try:
        import csv
        if not node.file_path:
            raise ValueError("CSVDataLoader: file_path is empty")
            
        with open(node.file_path, newline="", encoding="utf-8-sig") as f:
            # Use a list to strip headers immediately
            reader = csv.reader(f)
            headers = [h.strip() for h in next(reader)]
            
            data = []
            for row in reader:
                # Zip headers with stripped values
                data.append({headers[i]: str(row[i]).strip() for i in range(len(headers)) if i < len(row)})
            
        log.info("CSVDataLoader: Loaded %d rows from %s", len(data), node.file_path)
        log.info("CSV Attributes found: %s", ", ".join(headers))
        return NodeResult(success=True, output_key=node.output_key, output_value=data)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_compare(node: CompareNode, context: dict[str, Any]) -> NodeResult:
    """
    Resolves both operands from context (supports {{key}} templates),
    applies the operator, and returns TRUE or FALSE edge.
    """
    def _resolve(template: str) -> str:
        from cognitive_automator.llm.templates import render_prompt
        return render_prompt(template, context)

    left = _resolve(node.left_operand)
    right = _resolve(node.right_operand)

    op = node.operator
    cs = node.case_sensitive

    try:
        if op == CompareOp.IS_EMPTY:
            passed = left.strip() == ""
        elif op == CompareOp.IS_NOT_EMPTY:
            passed = left.strip() != ""
        elif op in (CompareOp.NUM_GT, CompareOp.NUM_LT,
                    CompareOp.NUM_GTE, CompareOp.NUM_LTE, CompareOp.NUM_EQUALS):
            lv, rv = float(left), float(right)
            passed = {
                CompareOp.NUM_GT:     lv > rv,
                CompareOp.NUM_LT:     lv < rv,
                CompareOp.NUM_GTE:    lv >= rv,
                CompareOp.NUM_LTE:    lv <= rv,
                CompareOp.NUM_EQUALS: lv == rv,
            }[op]
        else:
            # String operators
            left_val, right_val = (left, right) if cs else (left.lower(), right.lower())
            passed = {
                CompareOp.EQUALS:      left_val == right_val,
                CompareOp.NOT_EQUALS:  left_val != right_val,
                CompareOp.CONTAINS:    right_val in left_val,
                CompareOp.NOT_CONTAINS: right_val not in left_val,
                CompareOp.STARTS_WITH: left_val.startswith(right_val),
                CompareOp.ENDS_WITH:   left_val.endswith(right_val),
            }[op]
    except (ValueError, KeyError) as exc:
        return NodeResult(success=False, error=f"CompareNode error: {exc}")

    log.debug("CompareNode: %r %s %r → %s", left, op.value, right, passed)
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if passed else EdgeLabel.FALSE)


def execute_global_start(node: GlobalStartNode, context: dict[str, Any]) -> NodeResult:
    """Entry point marker. Does nothing but pass flow."""
    log.info("Automation started via GlobalStartNode")
    return NodeResult(success=True)


def execute_global_end(node: GlobalEndNode, context: dict[str, Any]) -> NodeResult:
    """Exit point marker. Signals completion."""
    log.info("Automation completed via GlobalEndNode")
    return NodeResult(success=True)


def execute_write_file(node: WriteFileNode, context: dict[str, Any]) -> NodeResult:
    """Writes rendered content to a file."""
    try:
        content = render_prompt(node.content_template, context)
        mode = "a" if node.append else "w"
        
        # If content is a dict/list, format as JSON for convenience
        if isinstance(content, (dict, list)):
            import json
            content = json.dumps(content, indent=2)
            
        with open(node.file_path, mode, encoding="utf-8") as f:
            f.write(content)
            if node.append and not content.endswith("\n"):
                f.write("\n")
                
        log.info("WriteFile: saved to %s", node.file_path)
        return NodeResult(success=True, output_key=node.output_key, output_value="success")
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_csv_writer(node: CSVWriterNode, context: dict[str, Any]) -> NodeResult:
    """Writes data (dict or list[dict]) to a CSV file."""
    try:
        import os
        data = context.get(node.data_source_key)
        if data is None:
            return NodeResult(success=False, error=f"Data source key '{node.data_source_key}' not found in context")
            
        # Standardize to list of dicts
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return NodeResult(success=False, error=f"Data at '{node.data_source_key}' must be a dict or list of dicts")
            
        if not data:
            log.warning("CSVWriter: No data to write")
            return NodeResult(success=True)
            
        file_exists = os.path.isfile(node.file_path)
        mode = "a" if node.append else "w"
        
        # Extract headers from first row
        headers = list(data[0].keys())
        
        with open(node.file_path, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            # Write header if new file or overwriting
            if not file_exists or not node.append:
                writer.writeheader()
            writer.writerows(data)
            
        log.info("CSVWriter: wrote %d rows to %s", len(data), node.file_path)
        return NodeResult(success=True, output_key=node.output_key, output_value="success")
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_screenshotter(node: ScreenshotterNode, context: dict[str, Any]) -> NodeResult:
    """Captures a sequence of screenshots by scrolling and optionally performs actions on detection."""
    import base64
    import tempfile
    import os
    from io import BytesIO
    from PIL import ImageChops  # type: ignore
    
    tmp_path = None
    try:
        images: list[str] = []
        last_img_hash = None
        
        log.info("Screenshotter: mode=%s, detection=%s", node.mode, node.detection_mode)
        
        # Prepare detection image if needed
        if node.detection_mode != DetectionMode.NONE and node.reference_image_b64:
            img_data = base64.b64decode(node.reference_image_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(img_data)
                tmp_path = f.name

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
            if tmp_path:
                try:
                    if node.detection_mode == DetectionMode.SINGLE:
                        loc = pyautogui.locateOnScreen(tmp_path, confidence=node.confidence, grayscale=node.grayscale)
                        if loc:
                            cx, cy = pyautogui.center(loc)
                            pyautogui.click(cx + node.x_offset, cy + node.y_offset)
                            log.info("Screenshotter: Clicked match at (%d, %d)", cx + node.x_offset, cy + node.y_offset)
                            time.sleep(node.wait_after_click)
                    elif node.detection_mode == DetectionMode.MULTIPLE:
                        # Robust "Click each as it appears": re-scan after each click
                        for _ in range(20): # Safety limit for one page
                            loc = pyautogui.locateOnScreen(tmp_path, confidence=node.confidence, grayscale=node.grayscale)
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
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _load_csv_column(path: str, column: str) -> list[str]:
    if path.lower().endswith((".xlsx", ".xls")):
        return _load_excel_column(path, column)
    items: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if column and column in row:
                items.append(row[column])
            elif not column:
                items.append(next(iter(row.values()), ""))
    return items


def _load_excel_column(path: str, column: str) -> list[str]:
    try:
        import openpyxl  # type: ignore
    except ImportError:
        raise ImportError(
            "openpyxl is required to read Excel files. Install it with: pip install openpyxl"
        )
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    items: list[str] = []
    headers: list[str] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):  # type: ignore[union-attr]
        if i == 0:
            headers = [str(c) if c is not None else "" for c in row]
            continue
        if column and column in headers:
            val = row[headers.index(column)]
        elif not column and row:
            val = row[0]
        else:
            continue
        items.append(str(val) if val is not None else "")
    wb.close()
    return items
