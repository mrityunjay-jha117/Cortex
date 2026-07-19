"""
serializer/ipc/to_json.py — IPC Serialization

This file provides a highly optimized helper function to encode an `ActionGraph` into a compact, whitespace-free JSON string for IPC transmission.
"""
from __future__ import annotations
import json
from cognitive_automator.graph_model import ActionGraph

# Helper function to convert a graph into a tightly packed JSON string (no spaces, no formatting)
def graph_to_json_str(graph: ActionGraph) -> str:
    """Compact JSON string for IPC (Inter-Process Communication)."""
    # dumps converts to string. separators=(",", ":") removes all whitespace making it as small as possible.
    return json.dumps(graph.model_dump_with_types(), separators=(",", ":"))
