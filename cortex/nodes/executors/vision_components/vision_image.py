"""
=============================================================================
 VISION_IMAGE.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *

def execute_vision_image(node: VisionImageNode, context: dict[str, Any]) -> NodeResult:
    import base64
    import os
    from cortex.llm.templates import render_prompt
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
