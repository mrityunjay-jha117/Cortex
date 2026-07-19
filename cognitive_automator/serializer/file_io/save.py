"""
serializer/file_io/save.py — Save Graph Function

This file contains the core logic for converting a running `ActionGraph` Python object into a serialized format (JSON or YAML) and writing it to the disk.
"""
from __future__ import annotations
import json
from pathlib import Path
import yaml
from cognitive_automator.graph_model import ActionGraph
from cognitive_automator.serializer.utils import _now_iso

# Public function to save a Python ActionGraph object to a physical file on the disk
def save_graph(graph: ActionGraph, path: str | Path) -> None:
    """
    Save an ActionGraph to disk.
    • .cogauto or .yaml → YAML format (easy for humans to read and track in Git)
    • .json           → JSON format (compact and fast)
    """
    # Convert the raw string path into a robust pathlib.Path object
    path = Path(path)
    
    # Automatically update the 'modified_at' timestamp right before saving
    graph.metadata.modified_at = _now_iso()
    # If the graph has never been saved before (no created_at date), set it now
    if not graph.metadata.created_at:
        graph.metadata.created_at = graph.metadata.modified_at

    # This is a critical step: It calls our custom function in ActionGraph to convert the graph 
    # to a dictionary, ensuring it injects the `_type` property so we know what class each node is.
    data = graph.model_dump_with_types()
    
    # Ensure the target directory exists. If it doesn't, create it automatically.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Check the file extension. If it's our custom extension or standard YAML, save as YAML.
    if path.suffix in (".cogauto", ".yaml", ".yml"):
        # Open the file in write mode ("w") with UTF-8 encoding to support emojis and international text
        with path.open("w", encoding="utf-8") as f:
            # Dump the dictionary as YAML. 
            # allow_unicode=True keeps special characters readable.
            # sort_keys=False keeps our dictionary order intact.
            # default_flow_style=False forces standard block YAML instead of inline JSON-like arrays.
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    else:
        # If it's any other extension (usually .json), save it as standard JSON
        with path.open("w", encoding="utf-8") as f:
            # Dump the dictionary as JSON with a 2-space indent for readability
            json.dump(data, f, indent=2, ensure_ascii=False)
