from .base import *
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
