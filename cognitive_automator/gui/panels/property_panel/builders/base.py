"""
gui/panels/property_panel/builders/base.py — Property Builder Interfaces

This file defines the abstract base classes and registry for Property Builders.
A Builder is responsible for constructing the specific UI form required to edit a particular node type (e.g. LLM vs Mouse).
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



class BaseBuilders:

    def _build_marker(self, node: AnyNode, desc: str) -> None:
        lbl = QLabel(desc)
        lbl.setStyleSheet(f"color:{APP_TEXT_DIM};")
        lbl.setWordWrap(True)
        self._form_layout.addRow("", lbl)

    def _build_visual_style(self, node: BaseNode) -> None:
        color_btn = QPushButton(node.color or "Default")
        if node.color:
            color_btn.setStyleSheet(f"background: {node.color}; color: {'#000' if QColor(node.color).lightness() > 128 else '#fff'};")
        
        def on_color() -> None:
            initial = QColor(node.color) if node.color else QColor(APP_ACCENT)
            color = QColorDialog.getColor(initial, self, "Select Node Color")
            if color.isValid():
                hex_color = color.name()
                self._set(node, "color", hex_color)
                color_btn.setText(hex_color)
                color_btn.setStyleSheet(f"background: {hex_color}; color: {'#000' if color.lightness() > 128 else '#fff'};")
        
        color_btn.clicked.connect(on_color)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(60)
        def on_reset() -> None:
            self._set(node, "color", None)
            color_btn.setText("Default")
            color_btn.setStyleSheet("")
        reset_btn.clicked.connect(on_reset)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.addWidget(color_btn)
        row_layout.addWidget(reset_btn)
        self._form_layout.addRow("Color Override", row)

    def _build_error_handling(self, node: BaseNode) -> None:
        self._form_layout.addRow("On Error", self._combo(
            [a.value for a in OnErrorAction], node.on_error.value,
            lambda v: self._set(node, "on_error", OnErrorAction(v))
        ))
        retry_spin = self._spin(node.retry_count, 0, 10, lambda v: self._set(node, "retry_count", v))
        self._form_layout.addRow("Retry Count", retry_spin)
        self._form_layout.addRow("Retry Delay (s)", self._dspin(node.retry_delay, 0.1, 60.0, lambda v: self._set(node, "retry_delay", v)))
