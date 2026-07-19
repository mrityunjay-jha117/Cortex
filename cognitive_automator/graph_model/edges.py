"""
Defines the GraphEdge class, which represents a directional link 
between a source node and a target node.
It utilizes Pydantic for data validation and strict typing.
The edge label is restricted to the predefined 
EdgeLabel enumerations.
"""
from pydantic import BaseModel
from .enums import EdgeLabel

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    label: EdgeLabel = EdgeLabel.DEFAULT
