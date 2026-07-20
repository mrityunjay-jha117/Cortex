"""
=============================================================================
 FORM_REBUILDER.PY (base_components)
=============================================================================
This module is a microservice component for base_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QCheckBox
from cognitive_automator.gui.constants import APP_TEXT_DIM
from cognitive_automator.graph_model import (
    AnyNode, MouseNode, KeyboardNode, NavigatorNode, ClipboardNode,
    LocateElementNode, LocateAndClickNode, GenerativeOCRNode,
    VisionExtractionNode, WriteFileNode, CSVDataLoaderNode, CSVWriterNode,
    ScreenshotterNode, LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode,
    WaitNode, BranchNode, IterateNode, DynamicIterateNode, SubGraphNode, CompareNode,
    FileDropNode, ForLoopNode, GlobalStartNode, GlobalEndNode
)
from .descriptions import get_node_desc

class FormRebuilderMixin:
    def _rebuild_form(self, node: AnyNode) -> None:  # type: ignore[type-arg]
        QTimer.singleShot(0, lambda: self._do_rebuild(node))

    def _do_rebuild(self, node: AnyNode) -> None:  # type: ignore[type-arg]
        if getattr(self, "_current_node", None) != node:
            return

        while self._form_layout.rowCount():
            self._form_layout.removeRow(0)

        self._locate_full_pixmap = None
        self._locate_img_label = None
        self._updating = True

        desc_label = QLabel(self._get_node_desc(node))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {APP_TEXT_DIM}; font-size: 11px; font-style: italic; margin-bottom: 10px;")
        self._form_layout.addRow(desc_label)
        
        self._add_section("General")
        label_edit = self._line_edit(node.label, lambda v: setattr(node, "label", v))
        self._form_layout.addRow("Label", label_edit)

        enabled_cb = QCheckBox()
        enabled_cb.setChecked(node.enabled)
        enabled_cb.toggled.connect(lambda v: self._set(node, "enabled", v))
        self._form_layout.addRow("Enabled", enabled_cb)

        note_edit = self._plain_text(node.note, lambda v: self._set(node, "note", v))
        note_edit.setMaximumHeight(60)
        self._form_layout.addRow("Note", note_edit)

        self._add_section(type(node).__name__)

        if isinstance(node, MouseNode):
            self._build_mouse(node)
        elif isinstance(node, KeyboardNode):
            self._build_keyboard(node)
        elif isinstance(node, NavigatorNode):
            self._build_navigator(node)
        elif isinstance(node, ClipboardNode):
            self._build_clipboard(node)
        elif isinstance(node, LocateElementNode):
            if isinstance(node, LocateAndClickNode):
                self._build_locate_and_click(node)
            else:
                self._build_locate(node)
        elif isinstance(node, GenerativeOCRNode):
            self._build_ocr(node)
        elif isinstance(node, VisionExtractionNode):
            self._build_vision_extraction(node)
        elif isinstance(node, WriteFileNode):
            self._build_write_file(node)
        elif isinstance(node, CSVDataLoaderNode):
            self._build_csv_data_loader(node)
        elif isinstance(node, CSVWriterNode):
            self._build_csv_writer(node)
        elif isinstance(node, ScreenshotterNode):
            self._build_screenshotter(node)
        elif isinstance(node, (LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode)):
            self._build_llm(node)
        elif isinstance(node, WaitNode):
            self._build_wait(node)
        elif isinstance(node, BranchNode):
            self._build_branch(node)
        elif isinstance(node, IterateNode):
            self._build_iterate(node)
        elif isinstance(node, DynamicIterateNode):
            self._build_dynamic_iterate(node)
        elif isinstance(node, SubGraphNode):
            self._build_subgraph(node)
        elif isinstance(node, CompareNode):
            self._build_compare(node)
        elif isinstance(node, FileDropNode):
            self._build_file_drop(node)
        elif isinstance(node, ForLoopNode):
            self._build_for_loop(node)
        elif isinstance(node, GlobalStartNode):
            self._build_marker(node, "Start marker for the automation.")
        elif isinstance(node, GlobalEndNode):
            self._build_marker(node, "End marker for the automation.")

        self._add_section("Visual Style")
        self._build_visual_style(node)

        self._add_section("Error Handling")
        self._build_error_handling(node)

        self._updating = False

    def _get_node_desc(self, node: AnyNode) -> str:
        return get_node_desc(node)
