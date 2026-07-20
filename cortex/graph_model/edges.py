"""
=============================================================================
 GRAPH EDGES
=============================================================================
This module defines the structures that connect nodes together.
It handles the logic and schema for directional flow between actions.

Key Features:
1. Defines the `GraphEdge` model linking a source node to a target node.
2. Supports typed connections (e.g., branching paths).

Think of this module as the wiring diagram that connects all the functional components.
=============================================================================
"""

from pydantic import BaseModel
from .enums import EdgeLabel

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    label: EdgeLabel = EdgeLabel.DEFAULT
