"""
=============================================================================
 TYPES.PY (graph_components)
=============================================================================
This module is a microservice component for graph_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from pydantic import BaseModel, Field

# Import all Physical action nodes (mouse, keyboard, clipboard, etc.)
from ..physical import MouseNode, KeyboardNode, ClipboardNode, NavigatorNode, FileDropNode, ScreenshotterNode
# Import all Vision nodes (finding UI elements, taking screenshots, OCR)
from ..vision import LocateElementNode, LocateAndClickNode, VisionImageNode, GenerativeOCRNode, VisionExtractionNode
# Import LLM node types (for making decisions, generating text, extracting JSON)
from ..llm import LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode
# Import Control Flow nodes (waits, conditional branches, loops, sub-graphs)
from ..flow import WaitNode, BranchNode, IterateNode, DynamicIterateNode, ForLoopNode, SubGraphNode, CompareNode
# Import System/Data nodes (loading/saving files, designating start and end points)
from ..system import CSVDataLoaderNode, GlobalStartNode, GlobalEndNode, WriteFileNode, CSVWriterNode
from ..enums import LLMProvider

AnyNode = (
    MouseNode | KeyboardNode | ClipboardNode | NavigatorNode | FileDropNode |
    LocateElementNode | LocateAndClickNode | VisionImageNode | GenerativeOCRNode | VisionExtractionNode | ScreenshotterNode |
    LLMJudgmentNode | LLMExtractionNode | LLMGenerativeNode |
    WaitNode | BranchNode | IterateNode | DynamicIterateNode | ForLoopNode | SubGraphNode |
    CompareNode | WriteFileNode | CSVDataLoaderNode | CSVWriterNode | GlobalStartNode | GlobalEndNode
)

class GraphMetadata(BaseModel):
    name: str = "Untitled"
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
