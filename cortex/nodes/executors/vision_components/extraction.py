"""
=============================================================================
 EXTRACTION.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *

def execute_vision_extraction(node: VisionExtractionNode, context: dict[str, Any],
                              llm_config: LLMConfig) -> NodeResult:
    from cortex.llm.structured import run_vision_extraction
    try:
        data = run_vision_extraction(node, context, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=data)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
