from typing import Any
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
