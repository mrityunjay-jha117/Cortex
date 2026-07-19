"""
=============================================================================
SUMMARY OF SERIALIZER MODULE
=============================================================================
This module acts as the "Save/Load Engine" for the Cognitive Automator. 
It takes the complex Python objects (like the `ActionGraph` and its nodes) 
and converts them into text (JSON or YAML) so they can be saved to the hard drive. 
It also does the reverse: reading a file from the hard drive and converting it 
back into running Python code.

Key Features:
1. Supports multiple formats: `.cogauto` (which is technically YAML), `.yaml`, and `.json`.
2. Inter-Process Communication (IPC): Provides fast JSON string methods to pass data quickly between the UI and background workers.

Think of this module as the translator between Python Memory and the Hard Drive.
=============================================================================
"""

from .file_io.save import save_graph
from .file_io.load import load_graph
from .ipc.to_json import graph_to_json_str
from .ipc.from_json import graph_from_json_str
from .factory.new import new_graph
from .constants import COGAUTO_EXTENSION, SCHEMA_VERSION

__all__ = [
    "save_graph",
    "load_graph",
    "graph_to_json_str",
    "graph_from_json_str",
    "new_graph",
    "COGAUTO_EXTENSION",
    "SCHEMA_VERSION"
]
