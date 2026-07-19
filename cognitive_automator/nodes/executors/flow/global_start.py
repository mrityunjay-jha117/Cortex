from ..base import *

def execute_global_start(node: GlobalStartNode, context: dict[str, Any]) -> NodeResult:
    """Entry point marker. Does nothing but pass flow."""
    log.info("Automation started via GlobalStartNode")
    return NodeResult(success=True)
