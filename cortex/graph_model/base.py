"""
=============================================================================
 BASE GRAPH NODES
=============================================================================
This module defines the foundational classes for all nodes in the action graph.
It sets up the Pydantic models that every specific node inherits from.

Key Features:
1. Defines the `BaseNode` with common properties like `id`, `x`, `y`, and `title`.
2. Establishes the standard interface for node serialization and properties.

Think of this module as the generic clay from which every specific node is sculpted.
=============================================================================
"""

import uuid
from pydantic import BaseModel, Field
from .enums import NodeCategory, OnErrorAction

class BaseNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    category: NodeCategory
    x: float = 0.0
    y: float = 0.0
    enabled: bool = True
    note: str = ""
    color: str | None = None
    retry_count: int = 2
    retry_delay: float = 1.0
    on_error: OnErrorAction = OnErrorAction.STOP
