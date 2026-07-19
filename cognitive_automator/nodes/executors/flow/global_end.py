from ..base import *

def execute_global_end(node: GlobalEndNode, context: dict[str, Any]) -> NodeResult:
    """Exit point marker. Signals completion."""
    log.info("Automation completed via GlobalEndNode")
    return NodeResult(success=True)
