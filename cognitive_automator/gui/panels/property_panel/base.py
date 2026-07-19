"""
gui/panels/property_panel/base.py — Property Panel Base

This file defines the core container for the Node Property Panel on the right side of the main window.
It dynamically clears and rebuilds its UI layout whenever a user selects a different node on the canvas.
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QLabel("Select a node to configure")
        self._header.setStyleSheet(
            f"background:{APP_SURFACE}; color:{APP_TEXT}; "
            f"padding:12px 16px; border-bottom:1px solid {APP_BORDER}; "
            "font-weight:bold; font-size:13px;"
        )
        layout.addWidget(self._header)

        # Scroll area wrapping stacked widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border:none; background:{APP_BG};")

        self._stacked = QStackedWidget()
        self._stacked.setStyleSheet(f"background:{APP_BG};")

        # Blank page
        blank = QWidget()
        blank_layout = QVBoxLayout(blank)
        hint = QLabel("Click a node on the canvas\nto view its properties.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color:{APP_TEXT_DIM}; font-size:12px;")
        blank_layout.addWidget(hint)
        self._stacked.addWidget(blank)   # index 0

        # Generic page (for all node types)
        self._form_widget = QWidget()
        self._form_layout = QFormLayout(self._form_widget)
        self._form_layout.setContentsMargins(16, 16, 16, 16)
        self._form_layout.setSpacing(10)
        self._form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._stacked.addWidget(self._form_widget)  # index 1

        scroll.setWidget(self._stacked)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll, stretch=1)

        self.setFixedWidth(350)
        self.setStyleSheet(f"background:{APP_BG};")

    def _add_hint(self, text: str) -> None:
        hint = QLabel(text)
        hint.setStyleSheet(f"color:{APP_TEXT_DIM}; font-size:11px;")
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

