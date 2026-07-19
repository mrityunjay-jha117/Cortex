from ..base import *

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
