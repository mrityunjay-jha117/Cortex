"""
=============================================================================
 CONTEXT_MENU.PY (view_components)
=============================================================================
This module is a microservice component for view_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu
from cognitive_automator.gui.canvas.node import NodeItem
from cognitive_automator.gui.canvas.scene import GraphScene
from cognitive_automator.graph_model import (
    CompareNode, KeyboardNode, LocateElementNode, LocateAndClickNode, MouseNode, WaitNode, NavigatorNode,
    GenerativeOCRNode, VisionExtractionNode, LLMJudgmentNode, LLMExtractionNode,
    LLMGenerativeNode, BranchNode, IterateNode, DynamicIterateNode, SubGraphNode,
    ClipboardNode, WriteFileNode, CSVWriterNode, ScreenshotterNode,
    ForLoopNode, FileDropNode, CSVDataLoaderNode, GlobalStartNode, GlobalEndNode
)

def build_and_exec_menu(view, event: Any) -> None:
    scene_cast: GraphScene = view.scene()  # type: ignore[assignment]
    if not scene_cast or not scene_cast._graph:
        return
    scene_pos = view.mapToScene(event.pos())

    def _add(node: Any) -> None:
        node.x = scene_pos.x()
        node.y = scene_pos.y()
        scene_cast._graph.add_node(node)
        scene_cast.load_graph(scene_cast._graph)
        scene_cast.graph_modified.emit()
    
    menu = QMenu(view)
    menu.setObjectName("canvasMenu")
    
    def _add_menu(parent_menu: QMenu, title: str) -> QMenu:
        sub = parent_menu.addMenu(title)
        sub.setObjectName("canvasMenu")
        return sub
    
    selected_nodes = [i for i in scene_cast.selectedItems() if isinstance(i, NodeItem)]
    if selected_nodes:
        menu.addAction("Duplicate Node(s) [Ctrl+D]", lambda: view._duplicate_selected())
        menu.addSeparator()

    # --- Vision Nodes ---
    vision_menu = _add_menu(menu, "Vision")
    vision_menu.addAction("Locate Image on Screen", lambda: _add(LocateElementNode(label="Find Element")))
    vision_menu.addAction("Locate and Click", lambda: _add(LocateAndClickNode(label="Find & Click")))
    vision_menu.addAction("Generative OCR (Text)", lambda: _add(GenerativeOCRNode(label="Extract Text")))
    vision_menu.addAction("Vision Extraction (Table/JSON)", lambda: _add(VisionExtractionNode(label="Extract Data")))

    # --- LLM Nodes ---
    llm_menu = _add_menu(menu, "LLM Logic")
    llm_menu.addAction("LLM Judgment (Yes/No)", lambda: _add(LLMJudgmentNode(label="Decision")))
    llm_menu.addAction("LLM Extraction (Structured)", lambda: _add(LLMExtractionNode(label="Extract JSON")))
    llm_menu.addAction("LLM Generative (Text)", lambda: _add(LLMGenerativeNode(label="Generate Text")))

    # --- Flow & Loops ---
    flow_menu = _add_menu(menu, "Flow & Loops")
    flow_menu.addAction("For Loop (Counter)", lambda: _add(ForLoopNode(label="Counter Loop")))
    flow_menu.addAction("Iterate (List/CSV)", lambda: _add(IterateNode(label="List Loop")))
    flow_menu.addAction("Dynamic Iterate (Context)", lambda: _add(DynamicIterateNode(label="Dynamic Loop")))
    flow_menu.addAction("Branch (Boolean)", lambda: _add(BranchNode(label="If/Else")))
    flow_menu.addAction("Compare (Condition)", lambda: _add(CompareNode(label="Check Condition")))
    flow_menu.addAction("Sub-Graph", lambda: _add(SubGraphNode(label="Call Subroutine")))
    flow_menu.addAction("Wait / Delay", lambda: _add(WaitNode(label="Wait")))

    # --- Physical Input ---
    input_menu = _add_menu(menu, "Input & IO")
    input_menu.addAction("Mouse", lambda: _add(MouseNode(label="Mouse Action")))
    input_menu.addAction("Keyboard", lambda: _add(KeyboardNode(label="Keyboard Action")))
    input_menu.addAction("Clipboard", lambda: _add(ClipboardNode(label="Clipboard")))
    input_menu.addAction("Navigator (Scroll/Focus)", lambda: _add(NavigatorNode(label="Navigator")))
    input_menu.addAction("File Drop / Upload", lambda: _add(FileDropNode(label="File Upload")))
    input_menu.addAction("Screenshotter (Multi-Page)", lambda: _add(ScreenshotterNode(label="Capturing Pages")))
    input_menu.addAction("Load CSV Data", lambda: _add(CSVDataLoaderNode(label="Load Data")))

    # --- System ---
    sys_menu = _add_menu(menu, "System")
    sys_menu.addAction("Global Start", lambda: _add(GlobalStartNode(label="START")))
    sys_menu.addAction("Global End", lambda: _add(GlobalEndNode(label="END")))
    sys_menu.addAction("Write to File", lambda: _add(WriteFileNode(label="Save Output")))
    sys_menu.addAction("Export to CSV", lambda: _add(CSVWriterNode(label="CSV Writer")))
    sys_menu.addAction("Load CSV Data", lambda: _add(CSVDataLoaderNode(label="Load Data")))

    menu.addSeparator()
    menu.addAction("Fit View  [F]", lambda: view.fitInView(
        view.scene().itemsBoundingRect(),
        Qt.AspectRatioMode.KeepAspectRatio,
    ))
    
    menu.exec(event.globalPos())
