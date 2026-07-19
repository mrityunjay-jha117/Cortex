"""
=============================================================================
 PROPERTY PANEL BASE
=============================================================================
This module provides the core framework for the property editor.
It defines how the panel reacts to node selection and commits changes.

Key Features:
1. Connects UI form inputs back to the underlying Pydantic node models.
2. Manages the layout lifecycle when switching between different nodes.

Think of this module as the scaffolding holding the settings dials.
=============================================================================
"""

from __future__ import annotations

from typing import Any

import base64
import json

from PyQt6.QtCore import Qt, QByteArray, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QScrollArea,
    QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
    QColorDialog, QFileDialog, QPushButton, QDialog,
)

from cognitive_automator.graph_model import (
    AnyNode, BaseNode, BranchNode, ClipboardNode, ClipboardAction, CompareNode, CompareOp,
    DynamicIterateNode, FileDropNode, ForLoopNode, GenerativeOCRNode, GlobalStartNode, GlobalEndNode,
    IterateNode, KeyboardNode, KeyboardAction,
    LLMExtractionNode, LLMGenerativeNode, LLMJudgmentNode, LocateElementNode, LocateAndClickNode, MouseNode, MouseAction, WaitNode, SubGraphNode, OnErrorAction,
    NavigationAction, NavigatorNode, VisionExtractionNode, WriteFileNode, CSVDataLoaderNode, CSVWriterNode,
    ScreenshotterNode, ScreenshotMode, DetectionMode,
)
from cognitive_automator.gui.constants import (
    APP_SURFACE, APP_BORDER, APP_ACCENT, APP_TEXT_DIM, APP_TEXT, APP_BG,
)

class ImageViewer(QDialog):
    def __init__(self, pixmap: QPixmap, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Reference Image")
        layout = QVBoxLayout(self)
        lbl = QLabel()
        lbl.setPixmap(pixmap)
        layout.addWidget(lbl)
        self.setModal(True)

from .builders import PropertyPanelBuilders
from .helpers import PropertyPanelHelpers
class PropertyPanel(PropertyPanelBuilders, PropertyPanelHelpers, QWidget):
    """Emits node_changed when a property is edited."""
    node_changed = pyqtSignal(str)   # node_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_node: AnyNode | None = None  # type: ignore[type-arg]
        self._updating = False

        # Locate preview state
        self._locate_full_pixmap: QPixmap | None = None
        self._locate_img_label: QLabel | None = None

        self.setStyleSheet(f"""
            #propPanel {{
                background-color: #111827;
                color: #FFFFFF;
            }}
            QScrollArea, QStackedWidget {{
                background-color: transparent;
                border: none;
            }}
            QLabel, QCheckBox {{
                color: #FFFFFF;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                background-color: #374151;
                border: 1px solid #4B5563;
                width: 14px;
                height: 14px;
                border-radius: 2px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {APP_ACCENT};
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
                background-color: #1F2937;
                color: #FFFFFF;
                border: 1px solid #374151;
                padding: 4px;
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {APP_ACCENT};
                color: #000000;
                border: 2px solid #000000;
                border-right: 4px solid #000000;
                border-bottom: 4px solid #000000;
                border-radius: 0px;
                padding: 4px 12px;
                font-family: "Courier New";
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #FFFFFF;
                color: #000000;
                border-color: #000000;
            }}
            QPushButton:pressed {{
                background-color: #FFFFFF;
                color: #000000;
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-right: 2px solid #000000;
                border-bottom: 2px solid #000000;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #374151;
                height: 8px;
                background: #1F2937;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {APP_ACCENT};
                border: 1px solid {APP_ACCENT};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QScrollBar:vertical {{
                background: #111827;
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {APP_ACCENT};
                min-height: 20px;
                border: none;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: #111827;
                height: 12px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {APP_ACCENT};
                min-width: 20px;
                border: none;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QLabel("Select a node to configure")
        self._header.setStyleSheet(
            f"background:#111827; color:#FFFFFF; "
            f"padding:12px 16px; border-bottom:2px solid {APP_BORDER}; "
            "font-weight:bold; font-size:14px;"
        )
        layout.addWidget(self._header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border:none; background:transparent;")

        self._stacked = QStackedWidget()
        self._stacked.setStyleSheet(f"background:transparent;")

        # Blank page
        blank = QWidget()
        blank.setObjectName("propPage")
        blank_layout = QVBoxLayout(blank)
        hint = QLabel("Click a node on the canvas\nto view its properties.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color:#FFFFFF; font-size:14px; font-weight:bold;")
        blank_layout.addWidget(hint)
        self._stacked.addWidget(blank)   # index 0

        # Generic page (for all node types)
        self._form_widget = QWidget()
        self._form_widget.setObjectName("propPage")
        self._form_layout = QFormLayout(self._form_widget)
        self._form_layout.setContentsMargins(16, 16, 16, 16)
        self._form_layout.setSpacing(10)
        self._form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._stacked.addWidget(self._form_widget)  # index 1

        scroll.setWidget(self._stacked)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll, stretch=1)

        self.setMinimumWidth(300)

    def _add_hint(self, text: str) -> None:
        hint = QLabel(text)
        hint.setStyleSheet(f"color:#CCCCCC; font-size:12px; font-weight:bold;")
        hint.setWordWrap(True)
        self._form_layout.addRow("", hint)

    def show_node(self, node: AnyNode) -> None:  # type: ignore[type-arg]
        self._current_node = node
        self._header.setText(f"{type(node).__name__}  ·  {node.id[:8]}")
        self._rebuild_form(node)
        self._stacked.setCurrentIndex(1)

    def clear(self) -> None:
        self._current_node = None
        self._stacked.setCurrentIndex(0)
        self._header.setText("Select a node to configure")

    # ------------------------------------------------------------------
    # Form builder
    # ------------------------------------------------------------------

    def _rebuild_form(self, node: AnyNode) -> None:  # type: ignore[type-arg]
        # Decouple rebuild from signal handlers to avoid deleting sender during signal
        QTimer.singleShot(0, lambda: self._do_rebuild(node))

    def _do_rebuild(self, node: AnyNode) -> None:  # type: ignore[type-arg]
        if self._current_node != node:
            return

        # Clear existing rows
        while self._form_layout.rowCount():
            self._form_layout.removeRow(0)

        self._locate_full_pixmap = None
        self._locate_img_label = None

        self._updating = True

        desc_label = QLabel(self._get_node_desc(node))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {APP_TEXT_DIM}; font-size: 11px; font-style: italic; margin-bottom: 10px;")
        self._form_layout.addRow(desc_label)
        # ── Common fields ──
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

        # ── Node-specific fields ──
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

        # ── Advanced settings ──
        self._add_section("Visual Style")
        self._build_visual_style(node)

        self._add_section("Error Handling")
        self._build_error_handling(node)

        self._updating = False

    def _get_node_desc(self, node: AnyNode) -> str:
        descs = {
            "MouseNode": "Simulates physical mouse movements, clicks, and scrolling on the screen. Used to interact with elements at specific coordinates.",
            "KeyboardNode": "Simulates physical keyboard key presses and text typing. Useful for entering data into forms or triggering shortcuts.",
            "ClipboardNode": "Reads from or writes to the system clipboard. Allows copying text to paste elsewhere or extracting copied data.",
            "NavigatorNode": "Performs scrolling or focus actions, optionally centering the screen on a provided reference image. Helpful for navigating large pages.",
            "FileDropNode": "Simulates dragging and dropping a specific file into a target application or window to automate file uploads.",
            "ScreenshotterNode": "Captures screenshots of the screen. Can scroll and capture multiple pages, stitching them together if needed.",
            "CSVDataLoaderNode": "Loads data from a CSV file line by line to feed into the workflow. Great for batch processing tasks.",
            "WriteFileNode": "Writes or appends generated text or data into a local text file for logging or output generation.",
            "CSVWriterNode": "Appends structured row data into a CSV file. Useful for saving extracted information into a spreadsheet format.",
            "LocateElementNode": "Uses computer vision (template matching or AI) to find the screen coordinates of a reference image or text.",
            "LocateAndClickNode": "Finds a specific image or text on the screen using computer vision and immediately clicks its center point.",
            "GenerativeOCRNode": "Uses a Vision Language Model (VLM) to read and extract text from the screen or a specific region.",
            "VisionExtractionNode": "Uses a Vision Language Model to analyze the screen and extract structured data, like tables or JSON.",
            "LLMJudgmentNode": "Asks an LLM a yes/no question based on provided context. Used to make intelligent logical branching decisions.",
            "LLMExtractionNode": "Uses an LLM to parse unstructured text and extract specific data points into a structured JSON format.",
            "LLMGenerativeNode": "Uses an LLM to generate creative text, summarize content, or answer questions based on the provided prompt.",
            "BranchNode": "Routes the workflow execution down one of two paths based on a true/false condition or previous judgment.",
            "CompareNode": "Compares two variables (e.g., equals, greater than, contains) and outputs a boolean true/false result for branching.",
            "ForLoopNode": "Executes a sequence of connected nodes a specific number of times. Perfect for repetitive, fixed-count actions.",
            "IterateNode": "Loops over a list of items (like a CSV row or JSON array), running the connected nodes for each item.",
            "DynamicIterateNode": "Uses an LLM to dynamically determine how to iterate over unstructured context, handling complex repeating patterns intelligently.",
            "SubGraphNode": "Calls another saved automation workflow as a subroutine. Useful for modularizing and reusing common automation tasks.",
            "WaitNode": "Pauses the execution of the workflow for a specified number of seconds before continuing to the next node.",
            "GlobalStartNode": "The mandatory starting point of the automation workflow. Execution always begins from this node.",
            "GlobalEndNode": "The final endpoint of the automation workflow. Reaching this node terminates the current execution path gracefully."
        }
        return descs.get(type(node).__name__, "No description available for this node.")
