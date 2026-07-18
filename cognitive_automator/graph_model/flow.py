from typing import Literal
from pydantic import BaseModel, Field
from .enums import NodeCategory, CompareOp
from .base import BaseNode

class WaitNode(BaseNode):
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    static_seconds: float | None = 1.0
    wait_for_image_b64: str | None = None
    wait_confidence: float = 0.7
    timeout_seconds: float = 30.0
    poll_interval: float = 0.5

class BranchNode(BaseNode):
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    condition_key: str = ""

class IterateNode(BaseNode):
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    csv_file_path: str = ""
    csv_column: str = ""
    items: list[str] = Field(default_factory=list)
    output_key: str = "loop_item"
    _current_index: int = 0

class DynamicIterateNode(BaseNode):
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    source_key: str = ""
    output_key: str = "loop_item"

class ForLoopNode(BaseNode):
    category: Literal[NodeCategory.LOGIC] = NodeCategory.LOGIC
    start: int = 0
    end: int = 999999
    step: int = 1
    output_key: str = "i"

class SubGraphNode(BaseNode):
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    sub_graph_path: str = ""
    input_mapping: dict[str, str] = Field(default_factory=dict)
    output_mapping: dict[str, str] = Field(default_factory=dict)

class CompareNode(BaseNode):
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    left_operand: str = ""
    operator: CompareOp = CompareOp.EQUALS
    right_operand: str = ""
    case_sensitive: bool = False
