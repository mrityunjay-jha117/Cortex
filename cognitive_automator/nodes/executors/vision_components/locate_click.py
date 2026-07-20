"""
=============================================================================
 LOCATE_CLICK.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
from typing import Callable
from .locate_core import execute_locate_element

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
        pass
    time.sleep(node.wait_after_click)

def execute_locate_and_click(node: LocateAndClickNode, context: dict[str, Any], 
                           abort_signal: Callable[[], bool] | None = None,
                           emit_info: Callable[[str], None] | None = None,
                           dev_mode: bool = False,
                           llm_config: LLMConfig | None = None) -> NodeResult:
    res = execute_locate_element(node, context, abort_signal, emit_info, dev_mode, llm_config)
    if not res.success:
        return res
    
    try:
        coords = res.output_value
        if not coords:
             return NodeResult(success=False, error="Locate succeeded but no coordinates returned.")
             
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
            
        return res
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=f"Click failed: {exc}")
