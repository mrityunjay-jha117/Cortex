"""
=============================================================================
 GLOBAL END EXECUTOR
=============================================================================
This module defines the termination point of the entire action graph.
It signals the runtime engine to gracefully shut down execution.

Key Features:
1. Finalizes state and ensures outputs are committed.
2. Halts the main execution loop.

Think of this module as the checkered flag at the end of the race.
=============================================================================
"""

from ..base import *

def execute_global_end(node: GlobalEndNode, context: dict[str, Any]) -> NodeResult:
    """Exit point marker. Signals completion."""
    log.info("Automation completed via GlobalEndNode")
    return NodeResult(success=True)
