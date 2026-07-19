"""
serializer/file_io/load.py — Load Graph Function

This file contains the core logic for loading a saved automation graph (JSON or YAML) from disk and reconstructing it into an `ActionGraph` Python object.
"""
from __future__ import annotations
import json
from pathlib import Path
import yaml
from cognitive_automator.graph_model import ActionGraph

# Public function to load a saved file from disk and convert it back into an ActionGraph object
def load_graph(path: str | Path) -> ActionGraph:
    """
    Load an ActionGraph from a .cogauto / .yaml / .json file.
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
        if path.suffix in (".cogauto", ".yaml", ".yml"):
            data = yaml.safe_load(f) # safe_load prevents arbitrary Python code execution from malicious YAML files
        else:
            data = json.load(f)
    
    # Feed the raw dictionary directly into Pydantic. Pydantic's `parse_nodes` validator will take over from here!
    return ActionGraph(**data)
