"""
=============================================================================
 FILE_DROP.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
import pyperclip
import sys
import pyautogui
import time
from typing import Any
from cortex.graph_model import FileDropNode

def execute_file_drop(node: FileDropNode, context: dict[str, Any]) -> NodeResult:
    try:
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

        x += node.x_offset
        y += node.y_offset

        log.debug("FileDrop: clicking target at (%d, %d)", x, y)
        pyautogui.click(x, y)
        time.sleep(node.wait_after_click)

        from cortex.llm.templates import render_prompt
        path = render_prompt(node.file_path, context)
        log.debug("FileDrop: typing path %s", path)
        
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
