"""
nodes/executors.py — Execution logic for every node type.

Each executor receives the node model + the mutable execution context dict.
Returns NodeResult(success, output_key, output_value, next_edge_label).

PyAutoGUI calls are wrapped with FAILSAFE guard.
"""

import base64
import csv
import logging
import sys
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Callable

import pyautogui  # type: ignore
import pyperclip  # type: ignore
from PIL import Image

from cognitive_automator.graph_model import (
    ActionGraph,
    BranchNode,
    CSVDataLoaderNode,
    ClipboardNode,
    CompareNode,
    CompareOp,
    DynamicIterateNode,
    EdgeLabel,
    FileDropNode,
    ForLoopNode,
    GenerativeOCRNode,
    GlobalEndNode,
    GlobalStartNode,
    IterateNode,
    KeyboardAction,
    KeyboardNode,
    LLMConfig,
    LLMExtractionNode,
    LLMGenerativeNode,
    LLMJudgmentNode,
    LLMProvider,
    LocateElementNode,
    LocateAndClickNode,
    MouseNode,
    MouseAction,
    ClipboardAction,
    NavigatorNode,
    WaitNode,
    VisionExtractionNode,
    VisionImageNode,
    WriteFileNode,
    CSVWriterNode,
    ScreenshotterNode,

    ScreenshotMode,
    DetectionMode,
)
from cognitive_automator.llm.structured import (
    run_extraction,
    run_generative,
    run_judgment,
    run_ocr,
    run_vision_extraction,
)
from cognitive_automator.llm.templates import render_prompt

log = logging.getLogger(__name__)

# Enforce PyAutoGUI FAILSAFE at import time — non-negotiable
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15   # Increased for better stability between focus/type transitions


@dataclass
class NodeResult:
    success: bool
    next_edge: EdgeLabel = EdgeLabel.DEFAULT
    error: str = ""
    # Key/value written into the execution context
    output_key: str = ""
    output_value: Any = None
    healed: bool = False

