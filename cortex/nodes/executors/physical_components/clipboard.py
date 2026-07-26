"""
=============================================================================
 CLIPBOARD.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
import pyperclip
from typing import Any
from cortex.graph_model import ClipboardNode, ClipboardAction

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
