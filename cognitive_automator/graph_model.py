"""
graph_model.py — Core Pydantic v2 models for the Action Graph.

Every node type is defined here. NetworkX DiGraph is the execution container.
All edges are typed; validation ensures no orphan nodes and no disallowed cycles.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Literal

import networkx as nx
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

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
    # String
    EQUALS          = "equals"
    NOT_EQUALS      = "not_equals"
    CONTAINS        = "contains"
    NOT_CONTAINS    = "not_contains"
    STARTS_WITH     = "starts_with"
    ENDS_WITH       = "ends_with"
    IS_EMPTY        = "is_empty"
    IS_NOT_EMPTY    = "is_not_empty"
    # Numeric
    NUM_GT          = "num_gt"
    NUM_LT          = "num_lt"
    NUM_GTE         = "num_gte"
    NUM_LTE         = "num_lte"
    NUM_EQUALS      = "num_equals"


class OnErrorAction(str, Enum):
    STOP = "stop"
    CONTINUE = "continue"
    RETRY = "retry"


# ---------------------------------------------------------------------------
# Base Node
# ---------------------------------------------------------------------------

class BaseNode(BaseModel):
    """All node types inherit from this."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    category: NodeCategory
    x: float = 0.0          # canvas position
    y: float = 0.0
    enabled: bool = True
    note: str = ""           # user annotation
    color: str | None = None # custom HEX color override
    retry_count: int = 2
    retry_delay: float = 1.0
    on_error: OnErrorAction = OnErrorAction.STOP


# ---------------------------------------------------------------------------
# Physical IO Nodes
# ---------------------------------------------------------------------------

class MouseNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: MouseAction = MouseAction.CLICK
    x_coord: int = 0
    y_coord: int = 0
    # Drag destination (only for DRAG_TO)
    dest_x: int = 0
    dest_y: int = 0
    duration: float = 0.0       # seconds for smooth movement
    button: str = "left"        # left / right / middle
    # If set, override x/y with Vision node output
    vision_node_id: str | None = None
    x_offset: int = 0           # applied on top of vision output
    y_offset: int = 0
    scroll_amount: int = 0      # for SCROLL action: positive=up, negative=down


class KeyboardNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: KeyboardAction = KeyboardAction.TYPEWRITE
    text: str = ""              # for TYPEWRITE
    key: str = ""               # for PRESS
    keys: list[str] = Field(default_factory=list)  # for HOTKEY
    interval: float = 0.0       # seconds between keystrokes


class ClipboardNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: ClipboardAction = ClipboardAction.READ
    write_text: str = ""        # for WRITE action (static text)
    # If WRITE and this is set, pull text from a prior node's output key
    source_output_key: str | None = None


class NavigatorNode(BaseNode):
    """
    Combined node for focusing (via optional image) and navigation (PageUp/Down, etc).
    If reference_image_b64 is set, it locates and clicks it before navigating.
    """
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    reference_image_b64: str = ""   # optional base64 PNG
    x_offset: int = 0
    y_offset: int = 0
    confidence: float = 0.75
    action: NavigationAction = NavigationAction.PAGE_DOWN
    repeat: int = 1                 # number of times to perform navigation


class FileDropNode(BaseNode):
    """
    Smart Upload: Clicks a target to open a file dialog, then types the path.
    """
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    file_path: str = ""
    x_coord: int = 0
    y_coord: int = 0
    vision_node_id: str | None = None  # if set, use vision output instead of x/y
    x_offset: int = 0                  # applied on top of vision output
    y_offset: int = 0
    wait_after_click: float = 1.0     # seconds to wait for dialog to open
    output_key: str = "dropped_file_path"


class ForLoopNode(BaseNode):
    """
    C++ style counter loop: for (int i = start; i < end; i += step)
    Iterates from start to end. Data is pulled from incoming data_bind edges.
    """
    category: Literal[NodeCategory.LOGIC] = NodeCategory.LOGIC
    start: int = 0
    end: int = 999999
    step: int = 1
    output_key: str = "i"


class CSVDataLoaderNode(BaseNode):
    """
    Loads a CSV file into a list of dictionaries in the context.
    Each dictionary represents a row, with column names as keys.
    """
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = ""
    output_key: str = "csv_data"


class GlobalStartNode(BaseNode):
    """Entry point marker for the entire automation."""
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM


class GlobalEndNode(BaseNode):
    """Exit point marker for the entire automation."""
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM


# ---------------------------------------------------------------------------
# Vision Nodes
# ---------------------------------------------------------------------------

class LocateElementNode(BaseNode):
    """
    Uses pyautogui.locateOnScreen with grayscale=True for 30% speed boost.
    Stores reference image as base64-encoded PNG in the graph file.
    When find_all=True, locates every match on screen and clicks each one.
    """
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    reference_image_b64: str = ""   # base64 PNG
    confidence: float = 0.75
    grayscale: bool = False
    region: tuple[int, int, int, int] | None = None  # (left, top, w, h) search area
    timeout_seconds: float = 10.0
    find_all: bool = False           # click every match instead of just the first
    x_offset: int = 0                # pixels from center
    y_offset: int = 0                # pixels from center

    # Last known coordinates (updated by Auto-Heal)
    x_coord: int | None = None
    y_coord: int | None = None

    # --- AI Fallback Mechanism ---
    use_fallback: bool = False
    auto_heal: bool = False        # If True, update coordinates and image if AI fallback succeeds
    fallback_prompt: str = ""
    fallback_provider_override: LLMProvider | None = None
    fallback_model_override: str | None = None

    # Output: (cx, cy) when find_all=False; list[(cx,cy)] when find_all=True
    output_key: str = "located_xy"


class LocateAndClickNode(LocateElementNode):
    """
    Combines LocateElementNode and MouseNode.
    First finds the image, then performs a mouse action on it.
    """
    action: MouseAction = MouseAction.CLICK
    button: str = "left"
    duration: float = 0.0
    wait_after_click: float = 0.3


class VisionImageNode(BaseNode):
    """
    Loads an image from a file path and stores it in the context as a base64 string.
    Useful for testing LLM extraction on specific saved images.
    """
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    file_path: str = ""
    output_key: str = "loaded_image"


class GenerativeOCRNode(BaseNode):
    """
    Captures a screen bounding box and sends it to a Vision LLM for text extraction.
    Vastly superior to Tesseract for modern Windows UI rendering.
    """
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)   # left, top, right, bottom
    system_prompt: str = (
        "Extract all text exactly as displayed on screen. "
        "Return raw text only, no commentary."
    )
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openai/gpt-4o"
    output_key: str = "ocr_text"


class VisionExtractionNode(BaseNode):
    """
    Extracts structured JSON from a screen region using Vision LLM.
    Vastly superior to OCR-then-LLM for complex spatial layouts (tables).
    """
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)
    prompt_template: str = "Extract the table from this image."
    system_prompt: str = (
        "You are a precise data extraction assistant. "
        "Extract the requested information as valid JSON only."
    )
    output_schema: dict[str, Any] = Field(default_factory=dict)
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2-vl-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 2048
    output_key: str = "vision_data"


# ---------------------------------------------------------------------------
# LLM Logic Nodes
# ---------------------------------------------------------------------------

class LLMJudgmentNode(BaseNode):
    """
    Boolean routing node. Uses structured JSON output to guarantee determinism.
    Output schema: {"result": bool, "confidence": float, "reasoning": str}
    """
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""   # Jinja2 template, variables from execution context
    system_prompt: str = (
        "You are a precise classification assistant. "
        "Always respond with valid JSON only."
    )
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2.5-72b-instruct"
    temperature: float = 0.0    # deterministic
    max_tokens: int = 256
    input_context_keys: list[str] = Field(default_factory=list)
    image_context_keys: list[str] = Field(default_factory=list) # Keys containing base64 images
    # Edges: true_edge and false_edge are set in the graph, not here


class LLMExtractionNode(BaseNode):
    """
    Extracts structured JSON from unstructured text.
    User defines the output schema as a JSON Schema dict.
    """
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "Extract the requested information as valid JSON."
    output_schema: dict[str, Any] = Field(default_factory=dict)
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2.5-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 2048
    input_context_keys: list[str] = Field(default_factory=list)
    image_context_keys: list[str] = Field(default_factory=list) # Keys containing base64 images
    output_key: str = "extracted_data"


class LLMGenerativeNode(BaseNode):
    """
    Generates freeform text (e.g., email draft) to be typed into a UI field.
    """
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "You are a helpful writing assistant."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openai/gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    input_context_keys: list[str] = Field(default_factory=list)
    output_key: str = "generated_text"


# ---------------------------------------------------------------------------
# Flow Control Nodes
# ---------------------------------------------------------------------------

class WaitNode(BaseNode):
    """Static sleep OR poll for a screen element to appear."""
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    static_seconds: float | None = 1.0
    # If set, waits for a LocateElementNode match instead of static sleep
    wait_for_image_b64: str | None = None
    wait_confidence: float = 0.7
    timeout_seconds: float = 30.0
    poll_interval: float = 0.5


class BranchNode(BaseNode):
    """Reads a boolean from context and routes to true_edge or false_edge."""
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    condition_key: str = ""     # key in execution context holding bool value
    # true_edge and false_edge are encoded as graph edges, not node fields


class IterateNode(BaseNode):
    """
    For-each loop. Reads items from a CSV file or a list in context.
    Emits one item per cycle into output_key.
    """
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    csv_file_path: str = ""
    csv_column: str = ""        # column name, empty = first column
    items: list[str] = Field(default_factory=list)   # static list alternative
    output_key: str = "loop_item"
    # Internal state managed by runtime (not persisted)
    _current_index: int = 0


class DynamicIterateNode(BaseNode):
    """
    For-each loop over a runtime list stored in the execution context.
    Items are typically (cx, cy) tuples from LocateElementNode(find_all=True)
    or string lists from LLM/OCR extraction.
    Emits LOOP_BODY while items remain, LOOP_END when exhausted.
    """
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    source_key: str = ""           # context key holding the list to iterate over
    output_key: str = "loop_item"  # context key for the current item each iteration


class SubGraphNode(BaseNode):
    """Embeds a nested ActionGraph for modular reuse."""
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    sub_graph_path: str = ""    # path to .cogauto file
    input_mapping: dict[str, str] = Field(default_factory=dict)
    output_mapping: dict[str, str] = Field(default_factory=dict)


class CompareNode(BaseNode):
    """
    Pure-logic comparison node. No LLM required.
    Resolves {{key}} templates from execution context for both operands,
    then applies the operator and routes to TRUE or FALSE edge.
    """
    category: Literal[NodeCategory.FLOW] = NodeCategory.FLOW
    left_operand: str = ""          # literal or {{context_key}}
    operator: CompareOp = CompareOp.EQUALS
    right_operand: str = ""         # literal or {{context_key}} (unused for IS_EMPTY ops)
    case_sensitive: bool = False    # applies to string operators only


class WriteFileNode(BaseNode):
    """
    Writes data to a file. Supports Jinja2 templates for content.
    """
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = "output.txt"
    content_template: str = "{{vision_data}}"
    append: bool = False
    output_key: str = "write_status"


class CSVWriterNode(BaseNode):
    """
    Writes data (dict or list of dicts) to a CSV file.
    If the file exists, it appends or overwrites based on config.
    """
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = "output.csv"
    data_source_key: str = ""   # context key holding the data (dict or list[dict])
    append: bool = True
    output_key: str = "csv_write_status"


class ScreenshotMode(str, Enum):
    N_TIMES = "n_times"
    UNTIL_END = "until_end"


class DetectionMode(str, Enum):
    NONE = "none"
    SINGLE = "single"    # click first match
    MULTIPLE = "multiple"  # click all matches


class ScreenshotterNode(BaseNode):
    """
    Captures multiple screenshots sequentially by scrolling down.
    Can also detect and click on specific images during the process.
    Returns a list of base64 images to the context.
    """
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    mode: ScreenshotMode = ScreenshotMode.N_TIMES
    n_times: int = 3             # used if mode is N_TIMES
    scroll_amount: int = -1000   # negative = scroll down
    wait_per_scroll: float = 1.0 # seconds to wait for page to render
    output_key: str = "captured_images"

    # --- Optional Image Detection during Scroll ---
    detection_mode: DetectionMode = DetectionMode.NONE
    reference_image_b64: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    confidence: float = 0.8
    grayscale: bool = False
    wait_after_click: float = 0.5


# ---------------------------------------------------------------------------
# Union type for all nodes
# ---------------------------------------------------------------------------

AnyNode = (
    MouseNode | KeyboardNode | ClipboardNode | NavigatorNode | FileDropNode |
    LocateElementNode | LocateAndClickNode | VisionImageNode | GenerativeOCRNode | VisionExtractionNode | ScreenshotterNode |
    LLMJudgmentNode | LLMExtractionNode | LLMGenerativeNode |
    WaitNode | BranchNode | IterateNode | DynamicIterateNode | ForLoopNode | SubGraphNode |
    CompareNode | WriteFileNode | CSVDataLoaderNode | CSVWriterNode | GlobalStartNode | GlobalEndNode
)


# ---------------------------------------------------------------------------
# Edge model
# ---------------------------------------------------------------------------

class EdgeLabel(str, Enum):
    DEFAULT = "default"
    TRUE = "true"
    FALSE = "false"
    LOOP_BODY = "loop_body"
    LOOP_END = "loop_end"
    DATA_BIND = "data_bind"
    ERROR = "error"


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    label: EdgeLabel = EdgeLabel.DEFAULT


# ---------------------------------------------------------------------------
# ActionGraph — the top-level model
# ---------------------------------------------------------------------------

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
    """Global LLM config; nodes can override individually."""
    default_provider: LLMProvider = LLMProvider.OPENROUTER
    fallback_provider: LLMProvider = LLMProvider.OPENROUTER
    fallback_model: str = "qwen/qwen3-vl-32b-instruct"
    openrouter_api_key_env: str = "OPENROUTER_API_KEY"
    request_timeout: float = 30.0
    max_retries: int = 3


class ActionGraph(BaseModel):
    """
    Top-level serialisable graph model.
    Nodes stored as a dict keyed by id; edges as a list.
    NetworkX DiGraph is reconstructed at runtime — not serialised.
    """
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    nodes: dict[str, AnyNode] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)
    entry_node_id: str | None = None

    @field_validator("nodes", mode="before")
    @classmethod
    def parse_nodes(cls, v: Any) -> dict[str, AnyNode]:
        """Deserialise discriminated union by category + node type."""
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
                parsed[node_id] = node_data  # type: ignore[assignment]
                continue
            node_type_name = node_data.get("_type", node_data.get("type", ""))
            node_cls = type_map.get(node_type_name)
            if node_cls is None:
                raise ValueError(f"Unknown node type '{node_type_name}' for node id '{node_id}'")
            parsed[node_id] = node_cls(**{k: v2 for k, v2 in node_data.items() if k not in ("_type", "type")})
        return parsed

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> "ActionGraph":
        """Ensure all edge endpoints exist and the graph has no disallowed cycles."""
        node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(f"Edge source '{edge.source_id}' not in nodes")
            if edge.target_id not in node_ids:
                raise ValueError(f"Edge target '{edge.target_id}' not in nodes")
        # Build NetworkX graph and check for cycles (IterateNodes create intentional cycles
        # via LOOP_BODY/LOOP_END edges; we skip those in cycle detection)
        G = self._build_nx_graph(exclude_loop_edges=True)
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Action Graph contains an unsupported cycle. "
                             "Use IterateNode for loops.")
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
        self.nodes[node.id] = node  # type: ignore[assignment]
        if self.entry_node_id is None or isinstance(node, GlobalStartNode):
            self.entry_node_id = node.id

    def duplicate_node(self, node_id: str) -> str | None:
        """Clone a node with all parameters but a new ID. Offsets position slightly."""
        node = self.nodes.get(node_id)
        if not node:
            return None
        new_node = node.model_copy(deep=True, update={"id": str(uuid.uuid4())})
        new_node.x += 40
        new_node.y += 40
        # add_node would set it as entry if entry is None, which is fine
        self.nodes[new_node.id] = new_node  # type: ignore[assignment]
        return new_node.id

    def add_edge(self, source_id: str, target_id: str,
                 label: EdgeLabel = EdgeLabel.DEFAULT) -> None:
        self.edges.append(GraphEdge(source_id=source_id, target_id=target_id, label=label))

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.edges = [e for e in self.edges
                      if e.source_id != node_id and e.target_id != node_id]
        if self.entry_node_id == node_id:
            self.entry_node_id = next(iter(self.nodes), None)

    def model_dump_with_types(self) -> dict[str, Any]:
        """Serialise with _type discriminator for round-trip deserialisation."""
        d = self.model_dump(mode="json")
        for node_id, node in self.nodes.items():
            d["nodes"][node_id]["_type"] = type(node).__name__
        return d
