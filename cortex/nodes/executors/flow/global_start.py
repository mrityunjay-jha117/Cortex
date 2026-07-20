"""
=============================================================================
 GLOBAL START EXECUTOR
=============================================================================
This module defines the entry point for the action graph execution.
It initializes context variables before any real work begins.

Key Features:
1. Acts as the mandatory first node in any valid graph.
2. Bootstraps the runtime state dictionary.

Think of this module as the starting pistol for the automation race.
=============================================================================
"""

from ..base import *

def execute_global_start(node: GlobalStartNode, context: dict[str, Any]) -> NodeResult:
    """Entry point marker. Does nothing but pass flow."""
    log.info("Automation started via GlobalStartNode")
    return NodeResult(success=True)
