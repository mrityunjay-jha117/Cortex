"""
=============================================================================
 KEYBOARD.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
def execute_keyboard(node: KeyboardNode, context: dict[str, Any]) -> NodeResult:
    try:
        from cortex.llm.templates import render_prompt
        
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
            time.sleep(0.2)
        return NodeResult(success=True)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
