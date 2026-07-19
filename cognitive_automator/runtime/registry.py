"""
runtime/registry.py — Executor Dispatch Registry

This file maintains an O(1) lookup table mapping node types to their corresponding execution functions.
"""
from __future__ import annotations
from typing import Callable
from cognitive_automator.graph_model import *
from cognitive_automator.nodes.executors import *

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
