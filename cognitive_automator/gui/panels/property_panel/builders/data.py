"""
gui/panels/property_panel/builders/data.py — Data Node Builders

This file implements UI forms for configuring data manipulation nodes (like CSV loading or File Writing).
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



class DataBuilders:

    def _build_csv_data_loader(self, node: CSVDataLoaderNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v)))
        
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0,0,0,0)
        
        browse_btn = QPushButton("Browse...")
        def on_browse() -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
            if path:
                self._set(node, "file_path", path)
                self._rebuild_form(node)
        browse_btn.clicked.connect(on_browse)
        btn_layout.addWidget(browse_btn)
        self._form_layout.addRow("", btn_row)
        
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        self._add_hint("Loads CSV as a list of dicts. Connect this to a For Loop.")

    def _build_csv_writer(self, node: CSVWriterNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v)))
        self._form_layout.addRow("Data Source Key", self._line_edit(node.data_source_key, lambda v: self._set(node, "data_source_key", v)))
        
        append_cb = QCheckBox()
        append_cb.setChecked(node.append)
        append_cb.toggled.connect(lambda v: self._set(node, "append", v))
        self._form_layout.addRow("Append Mode", append_cb)
        
        self._form_layout.addRow("Status Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        self._add_hint("Writes context data (dict or list[dict]) to CSV.")

    def _build_file_drop(self, node: FileDropNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v)))
        
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0,0,0,0)
        
        browse_btn = QPushButton("Browse...")
        def on_browse() -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
            if path:
                self._set(node, "file_path", path)
                self._rebuild_form(node)
        browse_btn.clicked.connect(on_browse)
        btn_layout.addWidget(browse_btn)
        self._form_layout.addRow("", btn_row)

        self._form_layout.addRow("X", self._spin(node.x_coord, 0, 9999, lambda v: self._set(node, "x_coord", v)))
        self._form_layout.addRow("Y", self._spin(node.y_coord, 0, 9999, lambda v: self._set(node, "y_coord", v)))
        
        self._add_section("Vision / Offsets")
        self._form_layout.addRow("Vision ID", self._line_edit(node.vision_node_id or "", lambda v: self._set(node, "vision_node_id", v if v else None)))
        
        # X Offset
        def on_x_offset(v: int) -> None:
            self._set(node, "x_offset", v)
            x_val_label.setText(str(v))
        x_row = QWidget()
        x_layout = QHBoxLayout(x_row)
        x_layout.setContentsMargins(0,0,0,0)
        x_slider = self._slider(node.x_offset, -2000, 2000, on_x_offset)
        x_val_label = QLabel(str(node.x_offset))
        x_val_label.setFixedWidth(40)
        x_layout.addWidget(x_slider)
        x_layout.addWidget(x_val_label)
        self._form_layout.addRow("X Offset", x_row)

        # Y Offset
        def on_y_offset(v: int) -> None:
            self._set(node, "y_offset", v)
            y_val_label.setText(str(v))
        y_row = QWidget()
        y_layout = QHBoxLayout(y_row)
        y_layout.setContentsMargins(0,0,0,0)
        y_slider = self._slider(node.y_offset, -2000, 2000, on_y_offset)
        y_val_label = QLabel(str(node.y_offset))
        y_val_label.setFixedWidth(40)
        y_layout.addWidget(y_slider)
        y_layout.addWidget(y_val_label)
        self._form_layout.addRow("Y Offset", y_row)

        self._add_section("Settings")
        self._form_layout.addRow("Wait (s)", self._dspin(node.wait_after_click, 0.1, 10.0, lambda v: self._set(node, "wait_after_click", v)))
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
