from pydantic import BaseModel
from .enums import EdgeLabel

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    label: EdgeLabel = EdgeLabel.DEFAULT
