"""
Pydantic's Field function helps enforce type safety and data constraints.
For example, `age: int = Field(default=18, ge=18)` enforces that the value must be greater than or equal to 18, throwing a validation error for something like `Student(age=10)`.

In this class, we use `default_factory=lambda: str(uuid.uuid4())` to guarantee that every newly instantiated node receives a globally unique ID.
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
