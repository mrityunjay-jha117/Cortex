"""
=============================================================================
 CORE ACTION GRAPH
=============================================================================
This module defines the overarching `ActionGraph` container.
It aggregates all nodes and edges into a cohesive executable graph.

Key Features:
1. Holds dictionaries of all nodes and lists of edges.
2. Provides validation to ensure graph structural integrity (no broken links).

Think of this module as the master blueprint containing the entire visual program.
=============================================================================
"""

from typing import Any
import networkx as nx
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import BaseNode
from .edges import GraphEdge
from .physical import MouseNode, KeyboardNode, ClipboardNode, NavigatorNode, FileDropNode, ScreenshotterNode
from .vision import LocateElementNode, LocateAndClickNode, VisionImageNode, GenerativeOCRNode, VisionExtractionNode
from .llm import LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode
from .flow import WaitNode, BranchNode, IterateNode, DynamicIterateNode, ForLoopNode, SubGraphNode, CompareNode
from .system import CSVDataLoaderNode, GlobalStartNode, GlobalEndNode, WriteFileNode, CSVWriterNode
from .graph_components import AnyNode, GraphMetadata, LLMConfig, GraphMethodsMixin

class ActionGraph(GraphMethodsMixin, BaseModel):
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    nodes: dict[str, AnyNode] = Field(default_factory=dict) # type: ignore
    edges: list[GraphEdge] = Field(default_factory=list)
    entry_node_id: str | None = None

    @field_validator("nodes", mode="before")
    @classmethod
    def parse_nodes(cls, v: Any) -> dict[str, AnyNode]: # type: ignore
        if not isinstance(v, dict):
            return v
            
        parsed: dict[str, AnyNode] = {} # type: ignore
        
        type_map: dict[str, type] = {
            "MouseNode": MouseNode, "KeyboardNode": KeyboardNode, "ClipboardNode": ClipboardNode,
            "NavigatorNode": NavigatorNode, "FileDropNode": FileDropNode, "LocateElementNode": LocateElementNode,
            "LocateAndClickNode": LocateAndClickNode, "VisionImageNode": VisionImageNode,
            "GenerativeOCRNode": GenerativeOCRNode, "VisionExtractionNode": VisionExtractionNode,
            "ScreenshotterNode": ScreenshotterNode, "LLMJudgmentNode": LLMJudgmentNode,
            "LLMExtractionNode": LLMExtractionNode, "LLMGenerativeNode": LLMGenerativeNode,
            "WaitNode": WaitNode, "BranchNode": BranchNode, "IterateNode": IterateNode,
            "DynamicIterateNode": DynamicIterateNode, "ForLoopNode": ForLoopNode, "SubGraphNode": SubGraphNode,
            "CompareNode": CompareNode, "WriteFileNode": WriteFileNode, "CSVDataLoaderNode": CSVDataLoaderNode,
            "CSVWriterNode": CSVWriterNode, "GlobalStartNode": GlobalStartNode, "GlobalEndNode": GlobalEndNode,
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
