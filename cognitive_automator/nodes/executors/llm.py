"""
nodes/executors/llm.py — LLM Executor Definitions

This file contains the runtime execution logic for AI-based nodes.
It wraps the underlying LLM client calls (Judgment, Extraction, Generative) inside the standard node execution pattern, safely handling API exceptions and formatting the results into `NodeResult` objects to inject AI outputs directly into the graph's execution context.
"""
from .base import *
def execute_judgment(node: LLMJudgmentNode, context: dict[str, Any],
                     llm_config: LLMConfig) -> NodeResult:
    try:
        result = run_judgment(node, context, llm_config)
        bool_result: bool = result["result"]
        log.info("LLMJudgment: result=%s confidence=%.2f reasoning=%s",
                 bool_result, result.get("confidence", 1.0), result.get("reasoning", "")[:80])
        next_edge = EdgeLabel.TRUE if bool_result else EdgeLabel.FALSE
        return NodeResult(
            success=True,
            next_edge=next_edge,
            output_key="judgment_result",
            output_value=result,
        )
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_extraction(node: LLMExtractionNode, context: dict[str, Any],
                       llm_config: LLMConfig) -> NodeResult:
    try:
        data = run_extraction(node, context, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=data)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_generative(node: LLMGenerativeNode, context: dict[str, Any],
                       llm_config: LLMConfig) -> NodeResult:
    try:
        text = run_generative(node, context, llm_config)
        return NodeResult(success=True, output_key=node.output_key, output_value=text)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
