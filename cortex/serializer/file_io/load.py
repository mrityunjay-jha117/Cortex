"""
=============================================================================
 FILE IO LOAD
=============================================================================
This module handles reading `.cortex`, JSON, or YAML files from disk.
It parses text and uses Pydantic to reconstruct the full Action Graph.

Key Features:
1. Dynamically maps string representations back into precise Node classes.
2. Handles file parsing errors and validates structural integrity.

Think of this module as the librarian pulling the blueprints out of storage.
=============================================================================
"""

from __future__ import annotations
import json
from pathlib import Path
import yaml
from cortex.graph_model import ActionGraph

# Public function to load a saved file from disk and convert it back into an ActionGraph object
def load_graph(path: str | Path) -> ActionGraph:
    """
    Load an ActionGraph from a .cortex / .yaml / .json file.
    Runs full Pydantic validation on load.
    """
    # Convert the string path into a Path object
    path = Path(path)
    # Check if the file actually exists before trying to open it
    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")

    # Open the file in read mode ("r") with UTF-8 encoding
    with path.open("r", encoding="utf-8") as f:
        # Determine if we should parse it as YAML or JSON based on the file extension
        if path.suffix in (".cortex", ".yaml", ".yml"):
            data = yaml.safe_load(f) # safe_load prevents arbitrary Python code execution from malicious YAML files
        else:
            data = json.load(f)
    
    # Feed the raw dictionary directly into Pydantic. Pydantic's `parse_nodes` validator will take over from here!
    return ActionGraph(**data)
