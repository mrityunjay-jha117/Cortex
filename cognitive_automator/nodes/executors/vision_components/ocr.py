"""
=============================================================================
 OCR.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *

def execute_generative_ocr(node: GenerativeOCRNode, context: dict[str, Any],
                           llm_config: LLMConfig) -> NodeResult:
    from cognitive_automator.llm.structured import run_ocr
    try:
        text = run_ocr(node, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=text)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
