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

# Import Any for type hinting (useful for fields where we accept any object before parsing)
from typing import Any
# Import uuid to generate unique identifiers for objects (like nodes)
import uuid
# Import networkx to handle graph validation and structure operations (cycle detection)
import networkx as nx
# Import Pydantic utilities to enforce type safety, data validation, and serialization
from pydantic import BaseModel, Field, field_validator, model_validator

# Import all our custom Enums (like EdgeLabel, LLMProvider) used across the graph
from .enums import EdgeLabel, LLMProvider
# Import our Edge representation (what connects nodes together)
from .edges import GraphEdge
# Import the foundational BaseNode which all other nodes inherit from
from .base import BaseNode

# Import all Physical action nodes (mouse, keyboard, clipboard, etc.)
from .physical import MouseNode, KeyboardNode, ClipboardNode, NavigatorNode, FileDropNode, ScreenshotterNode
# Import all Vision nodes (finding UI elements, taking screenshots, OCR)
from .vision import LocateElementNode, LocateAndClickNode, VisionImageNode, GenerativeOCRNode, VisionExtractionNode
# Import LLM node types (for making decisions, generating text, extracting JSON)
from .llm import LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode
# Import Control Flow nodes (waits, conditional branches, loops, sub-graphs)
from .flow import WaitNode, BranchNode, IterateNode, DynamicIterateNode, ForLoopNode, SubGraphNode, CompareNode
# Import System/Data nodes (loading/saving files, designating start and end points)
from .system import CSVDataLoaderNode, GlobalStartNode, GlobalEndNode, WriteFileNode, CSVWriterNode

# `AnyNode` is a massive Type Alias using the Union operator `|`.
# It allows us to tell the type checker that a variable (like a value in a dictionary)
# can be exactly ONE of these predefined node classes. 
# This is crucial for Pydantic to know how to validate nodes dynamically.
AnyNode = (
    MouseNode | KeyboardNode | ClipboardNode | NavigatorNode | FileDropNode |
    LocateElementNode | LocateAndClickNode | VisionImageNode | GenerativeOCRNode | VisionExtractionNode | ScreenshotterNode |
    LLMJudgmentNode | LLMExtractionNode | LLMGenerativeNode |
    WaitNode | BranchNode | IterateNode | DynamicIterateNode | ForLoopNode | SubGraphNode |
    CompareNode | WriteFileNode | CSVDataLoaderNode | CSVWriterNode | GlobalStartNode | GlobalEndNode
)

# A Pydantic model for storing metadata about the automation graph (like a project file header).
class GraphMetadata(BaseModel):
    name: str = "Untitled"          # The user-facing name of the automation
    description: str = ""                      # A short description of what it does
    version: str = "1.0.0"                     # The version of the automation itself
    schema_version: int = 1                    # For tracking future structural breaking changes
    author: str = ""                           # Who created the automation
    created_at: str = ""                       # Timestamp of creation
    modified_at: str = ""                      # Timestamp of last edit
    tags: list[str] = Field(default_factory=list) # Tags for organization (using default_factory to prevent shared mutable state)

# A Pydantic model for global LLM configurations used across all LLM nodes in the graph
class LLMConfig(BaseModel):
    default_provider: LLMProvider = LLMProvider.OPENROUTER     # Primary AI provider
    fallback_provider: LLMProvider = LLMProvider.OPENROUTER    # Fallback provider if primary fails
    fallback_model: str = "qwen/qwen3-vl-32b-instruct"         # Specific model to use on fallback
    openrouter_api_key_env: str = "OPENROUTER_API_KEY"         # The environment variable key to pull the API key from
    request_timeout: float = 30.0                              # Max seconds to wait for AI response before failing
    max_retries: int = 3                                       # How many times to retry an AI call on network failure

# The core schema representing the entire Automation execution flow
class ActionGraph(BaseModel):
    # Uses default_factory so every new graph gets a fresh instance of metadata
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)
    # Global LLM settings for this graph
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    # A dictionary mapping Node UUIDs to the actual Node objects. 
    nodes: dict[str, AnyNode] = Field(default_factory=dict)
    # A list of GraphEdge objects representing the connections/lines drawn between nodes
    edges: list[GraphEdge] = Field(default_factory=list)
    # Keeps track of which node the executor should start running from. Can be None if the graph is empty.
    entry_node_id: str | None = None

    # This is a special Pydantic validator that runs BEFORE the built-in validators parse the `nodes` dictionary.
    # Its job is to take raw JSON dictionaries loaded from disk and convert them back into proper Python Node objects.
    @field_validator("nodes", mode="before")
    @classmethod
    def parse_nodes(cls, v: Any) -> dict[str, AnyNode]:
        # If the incoming data isn't a dictionary (e.g. invalid data), just pass it along so Pydantic can throw a standard error
        if not isinstance(v, dict):
            return v
            
        parsed: dict[str, AnyNode] = {}
        
        # A lookup table mapping string class names (saved in JSON) to their actual Python Class types
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
        
        # Iterate over every node ID and its raw data dictionary
        for node_id, node_data in v.items():
            # If the data is already a fully instantiated Python object, just keep it (useful for programmatic creation)
            if isinstance(node_data, BaseNode):
                parsed[node_id] = node_data
                continue
                
            # Extract the stored class name from the JSON data. We check both `_type` and `type` for backwards compatibility.
            node_type_name = node_data.get("_type", node_data.get("type", ""))
            
            # Fetch the actual Python class from our type_map
            node_cls = type_map.get(node_type_name)
            if node_cls is None:
                # If we don't recognize the type (e.g., someone tampered with the save file), we crash loudly
                raise ValueError(f"Unknown node type '{node_type_name}' for node id '{node_id}'")
                
            # Instantiate the proper Node class, passing in all saved properties (kwargs) EXCEPT the special `_type` marker
            parsed[node_id] = node_cls(**{k: v2 for k, v2 in node_data.items() if k not in ("_type", "type")})
            
        return parsed

    # This validator runs AFTER Pydantic has fully parsed and created all nodes and edges.
    # Its job is to ensure the overall graph is logical and structurally sound.
    @model_validator(mode="after")
    def validate_graph_integrity(self) -> "ActionGraph":
        # Extract all valid node UUIDs into a fast-lookup set
        node_ids = set(self.nodes.keys())
        
        # 1. Edge Validation: Make sure no edge connects to a node that doesn't exist (Dangling Edges)
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(f"Edge source '{edge.source_id}' not in nodes")
            if edge.target_id not in node_ids:
                raise ValueError(f"Edge target '{edge.target_id}' not in nodes")
                
        # 2. Cycle Detection: Build a temporary mathematical graph to analyze the structure
        G = self._build_nx_graph(exclude_loop_edges=True)
        # If the graph has a cycle (e.g. Node A -> Node B -> Node A) but it's NOT a valid control-flow loop, it will break the engine
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Action Graph contains an unsupported cycle. Use IterateNode for loops.")
            
        # 3. Entry Node Validation: Ensure the defined starting point actually exists in the graph
        if self.entry_node_id and self.entry_node_id not in node_ids:
            raise ValueError(f"entry_node_id '{self.entry_node_id}' not in nodes")
            
        return self

    # Helper method to convert our Pydantic graph into a NetworkX DiGraph (Directed Graph) for advanced traversal
    def _build_nx_graph(self, exclude_loop_edges: bool = False) -> nx.DiGraph:
        G: nx.DiGraph = nx.DiGraph()
        # Add all node UUIDs to NetworkX
        G.add_nodes_from(self.nodes.keys())
        
        # Add all edges to NetworkX
        for edge in self.edges:
            # For cycle validation, we ignore intentional loop edges (like LOOP_BODY or TRUE/FALSE logic)
            # because we expect those to flow backwards naturally without breaking the engine
            if exclude_loop_edges and edge.label in (
                EdgeLabel.LOOP_BODY, EdgeLabel.LOOP_END,
                EdgeLabel.TRUE, EdgeLabel.FALSE,
            ):
                continue
            G.add_edge(edge.source_id, edge.target_id, label=edge.label.value)
        return G

    # Public API method to expose the fully connected NetworkX graph (useful for UI rendering or debugging)
    def to_nx(self) -> nx.DiGraph:
        return self._build_nx_graph(exclude_loop_edges=False)

    # API method to add a new Node object to the graph
    def add_node(self, node: AnyNode) -> None:
        self.nodes[node.id] = node
        # If this is the very first node added, or if it's explicitly a GlobalStartNode, make it the entry point automatically
        if self.entry_node_id is None or isinstance(node, GlobalStartNode):
            self.entry_node_id = node.id

    # API method to duplicate a node (like copy/pasting in the UI)
    def duplicate_node(self, node_id: str) -> str | None:
        node = self.nodes.get(node_id)
        if not node:
            return None # Node doesn't exist
            
        # Deep copy the node so memory isn't shared, and forcefully assign it a brand new UUID
        new_node = node.model_copy(deep=True, update={"id": str(uuid.uuid4())})
        
        # Shift the visual position slightly so it doesn't spawn exactly on top of the original node in the UI
        new_node.x += 30
        new_node.y += 30
        
        self.nodes[new_node.id] = new_node
        return new_node.id

    # API method to create a connection (edge) between two nodes
    def add_edge(self, source_id: str, target_id: str, label: EdgeLabel = EdgeLabel.DEFAULT) -> None:
        self.edges.append(GraphEdge(source_id=source_id, target_id=target_id, label=label))

    # API method to safely delete a node
    def remove_node(self, node_id: str) -> None:
        # Remove the node from the dictionary
        self.nodes.pop(node_id, None)
        
        # Also remove ANY edges connected to this node (both incoming and outgoing) to prevent dangling edges
        self.edges = [e for e in self.edges if e.source_id != node_id and e.target_id != node_id]
        
        # If we deleted the entry point, we need to pick a new one (randomly picks the first available node, or None if empty)
        if self.entry_node_id == node_id:
            self.entry_node_id = next(iter(self.nodes), None)

    # Custom serialization method for saving the graph to a JSON file
    def model_dump_with_types(self) -> dict[str, Any]:
        # Dump all standard Pydantic fields to a dictionary
        d = self.model_dump(mode="json")
        
        # Iterate over all nodes and inject a special `_type` string property
        # This is CRITICAL! Because Pydantic loses class information during JSON conversion,
        # we must manually record the class name (e.g., "MouseNode") so `parse_nodes` can resurrect the exact right class on load.
        for node_id, node in self.nodes.items():
            d["nodes"][node_id]["_type"] = type(node).__name__
        return d
