"""
=============================================================================
 RUNTIME REGISTRY
=============================================================================
This module maintains a dictionary mapping Node types to Executor types.
It allows the engine to look up how to run a node based on its class name.

Key Features:
1. Provides a central `register_executor` pattern.
2. Decouples graph definition schemas from their execution logic.

Think of this module as the yellow pages linking jobs to contractors.
=============================================================================
"""

from __future__ import annotations
from typing import Callable
from cortex.graph_model import *
from cortex.nodes.executors import *

EXECUTOR_REGISTRY: dict[type, Callable] = {
    MouseNode: execute_mouse,
    NavigatorNode: execute_navigator,
    KeyboardNode: execute_keyboard,
    ClipboardNode: execute_clipboard,
    LocateAndClickNode: execute_locate_and_click,
    LocateElementNode: execute_locate_element,
    GenerativeOCRNode: execute_generative_ocr,
    LLMJudgmentNode: execute_judgment,
    LLMExtractionNode: execute_extraction,
    LLMGenerativeNode: execute_generative,
    WaitNode: execute_wait,
    BranchNode: execute_branch,
    IterateNode: execute_iterate,
    DynamicIterateNode: execute_dynamic_iterate,
    ForLoopNode: execute_for_loop,
    CompareNode: execute_compare,
    VisionExtractionNode: execute_vision_extraction,
    VisionImageNode: execute_vision_image,
    WriteFileNode: execute_write_file,
    CSVDataLoaderNode: execute_csv_data_loader,
    CSVWriterNode: execute_csv_writer,
    ScreenshotterNode: execute_screenshotter,
    FileDropNode: execute_file_drop,
    GlobalStartNode: execute_global_start,
    GlobalEndNode: execute_global_end,
}
