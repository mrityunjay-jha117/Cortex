"""
serializer/ipc/from_json.py — IPC Deserialization

This file provides a highly optimized helper function to decode an `ActionGraph` from a compact JSON string sent over IPC channels.
"""
from __future__ import annotations
import json
from cognitive_automator.graph_model import ActionGraph

# Helper function to take a packed JSON string and convert it back to an ActionGraph
def graph_from_json_str(s: str) -> ActionGraph:
    # json.loads parses the string into a dict, and ActionGraph(**...) converts it into the class
    return ActionGraph(**json.loads(s))
