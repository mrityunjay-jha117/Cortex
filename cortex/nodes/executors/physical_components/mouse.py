"""
=============================================================================
 MOUSE.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
import time
import pyautogui
from typing import Any
from cortex.graph_model import MouseNode, MouseAction

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
                return NodeResult(success=False, 
                                 error=f"Vision output key '{node.vision_node_id}' not found in context. "
                                       f"Current keys: {list(context.keys())}")

        # Apply offsets
        x += node.x_offset
        y += node.y_offset

        log.info("MouseNode: action=%s target=(%d, %d)", node.action, x, y)

        if node.action == MouseAction.CLICK:
            pyautogui.click(x, y, button=node.button, duration=node.duration)
            time.sleep(0.3)
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
        raise
    except Exception as exc:  # noqa: BLE001
        return NodeResult(success=False, error=str(exc))
