"""
serializer/factory/new.py — Graph Factory

This file provides a helper factory function to create a brand new, empty automation graph populated with default metadata and timestamps.
"""
from __future__ import annotations
from cognitive_automator.graph_model import ActionGraph
from cognitive_automator.serializer.utils import _now_iso
from cognitive_automator.serializer.constants import SCHEMA_VERSION

# Helper factory function to create a brand new, empty automation graph with default values
def new_graph(name: str = "Untitled Automation") -> ActionGraph:
    graph = ActionGraph() # Create empty graph
    graph.metadata.name = name # Set the display name
    graph.metadata.created_at = _now_iso() # Set the birth time
    graph.metadata.modified_at = graph.metadata.created_at # Modified time is same as birth time initially
    graph.metadata.schema_version = SCHEMA_VERSION # Stamp it with the current software schema version
    return graph
