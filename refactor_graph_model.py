import os
import shutil

src_file = "cognitive_automator/graph_model.py"
dest_dir = "cognitive_automator/graph_model"

# Create the directory, move old file out of the way
if os.path.exists(src_file):
    os.rename(src_file, "cognitive_automator/graph_model_old.py")

os.makedirs(dest_dir, exist_ok=True)

with open("cognitive_automator/graph_model_old.py", "r", encoding="utf-8") as f:
    content = f.read()

# We'll just define the contents of the new files manually here to ensure correctness.

enums_content = """from enum import Enum

class NodeCategory(str, Enum):
    PHYSICAL = "physical"
    VISION = "vision"
    LLM = "llm"
    FLOW = "flow"
    LOGIC = "logic"
    SYSTEM = "system"

class MouseAction(str, Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE_TO = "move_to"
    DRAG_TO = "drag_to"
    SCROLL = "scroll"

class KeyboardAction(str, Enum):
    TYPEWRITE = "typewrite"
    PRESS = "press"
    HOTKEY = "hotkey"
    PASTE = "paste"
    SELECT_ALL = "select_all"

class ClipboardAction(str, Enum):
    READ = "read"
    WRITE = "write"

class NavigationAction(str, Enum):
    PAGE_UP = "pageup"
    PAGE_DOWN = "pagedown"
    HOME = "home"
    END = "end"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class LLMProvider(str, Enum):
    OPENROUTER = "openrouter"

class CompareOp(str, Enum):
    EQUALS          = "equals"
    NOT_EQUALS      = "not_equals"
    CONTAINS        = "contains"
    NOT_CONTAINS    = "not_contains"
    STARTS_WITH     = "starts_with"
    ENDS_WITH       = "ends_with"
    IS_EMPTY        = "is_empty"
    IS_NOT_EMPTY    = "is_not_empty"
    NUM_GT          = "num_gt"
    NUM_LT          = "num_lt"
    NUM_GTE         = "num_gte"
    NUM_LTE         = "num_lte"
    NUM_EQUALS      = "num_equals"

class OnErrorAction(str, Enum):
    STOP = "stop"
    CONTINUE = "continue"
    RETRY = "retry"

class ScreenshotMode(str, Enum):
    N_TIMES = "n_times"
    UNTIL_END = "until_end"

class DetectionMode(str, Enum):
    NONE = "none"
    SINGLE = "single"
    MULTIPLE = "multiple"

class EdgeLabel(str, Enum):
    DEFAULT = "default"
    TRUE = "true"
    FALSE = "false"
    LOOP_BODY = "loop_body"
    LOOP_END = "loop_end"
    DATA_BIND = "data_bind"
    ERROR = "error"
"""

base_content = """import uuid
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
"""

physical_content = """from typing import Literal
from pydantic import BaseModel, Field
from .enums import NodeCategory, MouseAction, KeyboardAction, ClipboardAction, NavigationAction, ScreenshotMode, DetectionMode
from .base import BaseNode

class MouseNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: MouseAction = MouseAction.CLICK
    x_coord: int = 0
    y_coord: int = 0
    dest_x: int = 0
    dest_y: int = 0
    duration: float = 0.0
    button: str = "left"
    vision_node_id: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    scroll_amount: int = 0

class KeyboardNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: KeyboardAction = KeyboardAction.TYPEWRITE
    text: str = ""
    key: str = ""
    keys: list[str] = Field(default_factory=list)
    interval: float = 0.0

class ClipboardNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: ClipboardAction = ClipboardAction.READ
    write_text: str = ""
    source_output_key: str | None = None

class NavigatorNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    reference_image_b64: str = ""
    x_offset: int = 0
    y_offset: int = 0
    confidence: float = 0.75
    action: NavigationAction = NavigationAction.PAGE_DOWN
    repeat: int = 1

class FileDropNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    file_path: str = ""
    x_coord: int = 0
    y_coord: int = 0
    vision_node_id: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    wait_after_click: float = 1.0
    output_key: str = "dropped_file_path"

class ScreenshotterNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    mode: ScreenshotMode = ScreenshotMode.N_TIMES
    n_times: int = 3
    scroll_amount: int = -1000
    wait_per_scroll: float = 1.0
    output_key: str = "captured_images"
    detection_mode: DetectionMode = DetectionMode.NONE
    reference_image_b64: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    confidence: float = 0.8
    grayscale: bool = False
    wait_after_click: float = 0.5
"""

vision_content = """from typing import Literal, Any
from pydantic import BaseModel, Field
from .enums import NodeCategory, LLMProvider, MouseAction
from .base import BaseNode

class LocateElementNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    reference_image_b64: str = ""
    confidence: float = 0.75
    grayscale: bool = False
    region: tuple[int, int, int, int] | None = None
    timeout_seconds: float = 10.0
    find_all: bool = False
    x_offset: int = 0
    y_offset: int = 0
    x_coord: int | None = None
    y_coord: int | None = None
    use_fallback: bool = False
    auto_heal: bool = False
    fallback_prompt: str = ""
    fallback_provider_override: LLMProvider | None = None
    fallback_model_override: str | None = None
    output_key: str = "located_xy"

class LocateAndClickNode(LocateElementNode):
    action: MouseAction = MouseAction.CLICK
    button: str = "left"
    duration: float = 0.0
    wait_after_click: float = 0.3

class VisionImageNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    file_path: str = ""
    output_key: str = "loaded_image"

class GenerativeOCRNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)
    system_prompt: str = "Extract all text exactly as displayed on screen. Return raw text only, no commentary."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openai/gpt-4o"
    output_key: str = "ocr_text"

class VisionExtractionNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)
    prompt_template: str = "Extract the table from this image."
    system_prompt: str = "You are a precise data extraction assistant. Extract the requested information as valid JSON only."
    output_schema: dict[str, Any] = Field(default_factory=dict)
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2-vl-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 2048
    output_key: str = "vision_data"
"""

llm_content = """from typing import Literal, Any
from pydantic import BaseModel, Field
from .enums import NodeCategory, LLMProvider
from .base import BaseNode

class LLMJudgmentNode(BaseNode):
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "You are a precise classification assistant. Always respond with valid JSON only."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2.5-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 256
    input_context_keys: list[str] = Field(default_factory=list)
    image_context_keys: list[str] = Field(default_factory=list)

class LLMExtractionNode(BaseNode):
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "Extract the requested information as valid JSON."
    output_schema: dict[str, Any] = Field(default_factory=dict)
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2.5-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 2048
    input_context_keys: list[str] = Field(default_factory=list)
    image_context_keys: list[str] = Field(default_factory=list)
    output_key: str = "extracted_data"

class LLMGenerativeNode(BaseNode):
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "You are a helpful writing assistant."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openai/gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    input_context_keys: list[str] = Field(default_factory=list)
    output_key: str = "generated_text"
"""

flow_content = """from typing import Literal
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
"""

system_content = """from typing import Literal
from pydantic import BaseModel, Field
from .enums import NodeCategory
from .base import BaseNode

class CSVDataLoaderNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = ""
    output_key: str = "csv_data"

class GlobalStartNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM

class GlobalEndNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM

class WriteFileNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = "output.txt"
    content_template: str = "{{vision_data}}"
    append: bool = False
    output_key: str = "write_status"

class CSVWriterNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = "output.csv"
    data_source_key: str = ""
    append: bool = True
    output_key: str = "csv_write_status"
"""

edges_content = """from pydantic import BaseModel
from .enums import EdgeLabel

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    label: EdgeLabel = EdgeLabel.DEFAULT
"""

graph_content = """from typing import Any
import uuid
import networkx as nx
from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import EdgeLabel, LLMProvider
from .edges import GraphEdge
from .base import BaseNode
from .physical import MouseNode, KeyboardNode, ClipboardNode, NavigatorNode, FileDropNode, ScreenshotterNode
from .vision import LocateElementNode, LocateAndClickNode, VisionImageNode, GenerativeOCRNode, VisionExtractionNode
from .llm import LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode
from .flow import WaitNode, BranchNode, IterateNode, DynamicIterateNode, ForLoopNode, SubGraphNode, CompareNode
from .system import CSVDataLoaderNode, GlobalStartNode, GlobalEndNode, WriteFileNode, CSVWriterNode

AnyNode = (
    MouseNode | KeyboardNode | ClipboardNode | NavigatorNode | FileDropNode |
    LocateElementNode | LocateAndClickNode | VisionImageNode | GenerativeOCRNode | VisionExtractionNode | ScreenshotterNode |
    LLMJudgmentNode | LLMExtractionNode | LLMGenerativeNode |
    WaitNode | BranchNode | IterateNode | DynamicIterateNode | ForLoopNode | SubGraphNode |
    CompareNode | WriteFileNode | CSVDataLoaderNode | CSVWriterNode | GlobalStartNode | GlobalEndNode
)

class GraphMetadata(BaseModel):
    name: str = "Untitled Automation"
    description: str = ""
    version: str = "1.0.0"
    schema_version: int = 1
    author: str = ""
    created_at: str = ""
    modified_at: str = ""
    tags: list[str] = Field(default_factory=list)

class LLMConfig(BaseModel):
    default_provider: LLMProvider = LLMProvider.OPENROUTER
    fallback_provider: LLMProvider = LLMProvider.OPENROUTER
    fallback_model: str = "qwen/qwen3-vl-32b-instruct"
    openrouter_api_key_env: str = "OPENROUTER_API_KEY"
    request_timeout: float = 30.0
    max_retries: int = 3

class ActionGraph(BaseModel):
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    nodes: dict[str, AnyNode] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)
    entry_node_id: str | None = None

    @field_validator("nodes", mode="before")
    @classmethod
    def parse_nodes(cls, v: Any) -> dict[str, AnyNode]:
        if not isinstance(v, dict):
            return v
        parsed: dict[str, AnyNode] = {}
        type_map: dict[str, type] = {
            "MouseNode": MouseNode,
            "KeyboardNode": KeyboardNode,
            "ClipboardNode": ClipboardNode,
            "NavigatorNode": NavigatorNode,
            "FileDropNode": FileDropNode,
            "LocateElementNode": LocateElementNode,
            "LocateAndClickNode": LocateAndClickNode,
            "VisionImageNode": VisionImageNode,
            "GenerativeOCRNode": GenerativeOCRNode,
            "VisionExtractionNode": VisionExtractionNode,
            "ScreenshotterNode": ScreenshotterNode,
            "LLMJudgmentNode": LLMJudgmentNode,
            "LLMExtractionNode": LLMExtractionNode,
            "LLMGenerativeNode": LLMGenerativeNode,
            "WaitNode": WaitNode,
            "BranchNode": BranchNode,
            "IterateNode": IterateNode,
            "DynamicIterateNode": DynamicIterateNode,
            "ForLoopNode": ForLoopNode,
            "SubGraphNode": SubGraphNode,
            "CompareNode": CompareNode,
            "WriteFileNode": WriteFileNode,
            "CSVDataLoaderNode": CSVDataLoaderNode,
            "CSVWriterNode": CSVWriterNode,
            "GlobalStartNode": GlobalStartNode,
            "GlobalEndNode": GlobalEndNode,
        }
        for node_id, node_data in v.items():
            if isinstance(node_data, BaseNode):
                parsed[node_id] = node_data
                continue
            node_type_name = node_data.get("_type", node_data.get("type", ""))
            node_cls = type_map.get(node_type_name)
            if node_cls is None:
                raise ValueError(f"Unknown node type '{node_type_name}' for node id '{node_id}'")
            parsed[node_id] = node_cls(**{k: v2 for k, v2 in node_data.items() if k not in ("_type", "type")})
        return parsed

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> "ActionGraph":
        node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(f"Edge source '{edge.source_id}' not in nodes")
            if edge.target_id not in node_ids:
                raise ValueError(f"Edge target '{edge.target_id}' not in nodes")
        G = self._build_nx_graph(exclude_loop_edges=True)
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Action Graph contains an unsupported cycle. Use IterateNode for loops.")
        if self.entry_node_id and self.entry_node_id not in node_ids:
            raise ValueError(f"entry_node_id '{self.entry_node_id}' not in nodes")
        return self

    def _build_nx_graph(self, exclude_loop_edges: bool = False) -> nx.DiGraph:
        G: nx.DiGraph = nx.DiGraph()
        G.add_nodes_from(self.nodes.keys())
        for edge in self.edges:
            if exclude_loop_edges and edge.label in (
            EdgeLabel.LOOP_BODY, EdgeLabel.LOOP_END,
            EdgeLabel.TRUE, EdgeLabel.FALSE,
        ):
                continue
            G.add_edge(edge.source_id, edge.target_id, label=edge.label.value)
        return G

    def to_nx(self) -> nx.DiGraph:
        return self._build_nx_graph(exclude_loop_edges=False)

    def add_node(self, node: AnyNode) -> None:
        self.nodes[node.id] = node
        if self.entry_node_id is None or isinstance(node, GlobalStartNode):
            self.entry_node_id = node.id

    def duplicate_node(self, node_id: str) -> str | None:
        node = self.nodes.get(node_id)
        if not node:
            return None
        new_node = node.model_copy(deep=True, update={"id": str(uuid.uuid4())})
        new_node.x += 40
        new_node.y += 40
        self.nodes[new_node.id] = new_node
        return new_node.id

    def add_edge(self, source_id: str, target_id: str, label: EdgeLabel = EdgeLabel.DEFAULT) -> None:
        self.edges.append(GraphEdge(source_id=source_id, target_id=target_id, label=label))

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.edges = [e for e in self.edges if e.source_id != node_id and e.target_id != node_id]
        if self.entry_node_id == node_id:
            self.entry_node_id = next(iter(self.nodes), None)

    def model_dump_with_types(self) -> dict[str, Any]:
        d = self.model_dump(mode="json")
        for node_id, node in self.nodes.items():
            d["nodes"][node_id]["_type"] = type(node).__name__
        return d
"""

init_content = """from .enums import *
from .base import *
from .physical import *
from .vision import *
from .llm import *
from .flow import *
from .system import *
from .edges import *
from .graph import *
"""

files = {
    "enums.py": enums_content,
    "base.py": base_content,
    "physical.py": physical_content,
    "vision.py": vision_content,
    "llm.py": llm_content,
    "flow.py": flow_content,
    "system.py": system_content,
    "edges.py": edges_content,
    "graph.py": graph_content,
    "__init__.py": init_content
}

for fname, fcontent in files.items():
    with open(os.path.join(dest_dir, fname), "w", encoding="utf-8") as f:
        f.write(fcontent)
