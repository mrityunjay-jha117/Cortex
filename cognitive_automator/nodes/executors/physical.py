from .base import *
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
