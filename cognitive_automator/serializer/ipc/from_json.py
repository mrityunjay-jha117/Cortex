"""
=============================================================================
 IPC DESERIALIZATION
=============================================================================
This module parses raw JSON strings back into Python objects rapidly.
It is optimized for passing messages rather than saving to disk.

Key Features:
1. Reconstructs execution results or status updates from background threads.
2. Bypasses heavy validation used in file loading for speed.

Think of this module as the receiver decoding a fast telegram.
=============================================================================
"""

from __future__ import annotations
import json
from cognitive_automator.graph_model import ActionGraph

# Helper function to take a packed JSON string and convert it back to an ActionGraph
def graph_from_json_str(s: str) -> ActionGraph:
    # json.loads parses the string into a dict, and ActionGraph(**...) converts it into the class
    return ActionGraph(**json.loads(s))
