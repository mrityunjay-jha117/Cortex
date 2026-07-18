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
