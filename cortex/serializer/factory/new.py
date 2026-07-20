"""
=============================================================================
 NEW FACTORY
=============================================================================
This module creates fresh, default instances of Action Graphs.
It ensures new projects start with a valid `GlobalStartNode`.

Key Features:
1. Injects mandatory nodes into an empty graph structure.
2. Provides a standard reset point for the UI.

Think of this module as the factory line that builds a new blank canvas.
=============================================================================
"""

from __future__ import annotations
from cortex.graph_model import ActionGraph
from cortex.serializer.utils import _now_iso
from cortex.serializer.constants import SCHEMA_VERSION

# Helper factory function to create a brand new, empty automation graph with default values
def new_graph(name: str = "Untitled Automation") -> ActionGraph:
    graph = ActionGraph() # Create empty graph
    graph.metadata.name = name # Set the display name
    graph.metadata.created_at = _now_iso() # Set the birth time
    graph.metadata.modified_at = graph.metadata.created_at # Modified time is same as birth time initially
    graph.metadata.schema_version = SCHEMA_VERSION # Stamp it with the current software schema version
    return graph
