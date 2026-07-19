"""
=============================================================================
 IPC SERIALIZATION
=============================================================================
This module converts Python objects into raw JSON strings rapidly.
It prepares data to be sent across thread boundaries.

Key Features:
1. Strips unnecessary metadata to keep messages small.
2. Encodes statuses and graph updates for the UI to consume.

Think of this module as the sender encrypting a fast telegram.
=============================================================================
"""

from __future__ import annotations
import json
from cognitive_automator.graph_model import ActionGraph

# Helper function to convert a graph into a tightly packed JSON string (no spaces, no formatting)
def graph_to_json_str(graph: ActionGraph) -> str:
    """Compact JSON string for IPC (Inter-Process Communication)."""
    # dumps converts to string. separators=(",", ":") removes all whitespace making it as small as possible.
    return json.dumps(graph.model_dump_with_types(), separators=(",", ":"))
