"""
=============================================================================
 FLOW PROPERTY BUILDERS
=============================================================================
This module generates UI forms specifically for Control Flow nodes.
It handles properties like wait times, conditions, and loop iterations.

Key Features:
1. Builds editors for branching logic and comparison operators.
2. Validates numerical inputs for delays and counters.

Think of this module as the control board for the traffic lights.
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

class FlowBuilders:

    def _build_for_loop(self, node: ForLoopNode) -> None:
        self._form_layout.addRow("Variable Name", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        self._form_layout.addRow("Start (i =)", self._spin(node.start, -999999, 999999, lambda v: self._set(node, "start", v)))
        self._form_layout.addRow("End (while i <)", self._spin(node.end, -999999, 999999, lambda v: self._set(node, "end", v)))
        self._form_layout.addRow("Step (i +=)", self._spin(node.step, -9999, 9999, lambda v: self._set(node, "step", v)))
        self._add_hint(
            "Connect Data nodes (CSV Loader, File Drop) to the top port.\n"
            "This will show a visual BLUE connection.\n"
            "Access data via ${data[i].column}."
        )

    def _build_wait(self, node: WaitNode) -> None:
        self._form_layout.addRow("Static Delay (s)", self._dspin(
            node.static_seconds or 1.0, 0.0, 60.0, lambda v: self._set(node, "static_seconds", v)
        ))
        
        # Image wait
        img_container = QWidget()
        img_vbox = QVBoxLayout(img_container)
        img_vbox.setContentsMargins(0,0,0,0)
        
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if node.wait_for_image_b64:
             try:
                data = base64.b64decode(node.wait_for_image_b64)
                pm = QPixmap()
                pm.loadFromData(QByteArray(data))
                if not pm.isNull():
                    pm = pm.scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                    img_label.setPixmap(pm)
             except Exception:
                img_label.setText("(image decode error)")
        else:
            img_label.setText("No wait image set")
            img_label.setStyleSheet(f"color:{APP_TEXT_DIM}; font-size:11px;")
        
        img_label.setStyleSheet(
            f"border:1px solid {APP_BORDER}; border-radius:4px; "
            "padding:4px; background:#1a1a2e;"
        )
        img_label.setFixedHeight(130)
        img_vbox.addWidget(img_label)

        change_btn = QPushButton("Set Wait Image...")
        change_btn.clicked.connect(lambda: self._change_image(node, "wait_for_image_b64"))
        img_vbox.addWidget(change_btn)
        
        self._form_layout.addRow("Wait for\nImage", img_container)

        self._form_layout.addRow("Confidence", self._dspin(node.wait_confidence, 0.5, 1.0, lambda v: self._set(node, "wait_confidence", v)))
        self._form_layout.addRow("Timeout (s)", self._dspin(node.timeout_seconds, 1.0, 300.0, lambda v: self._set(node, "timeout_seconds", v)))
        self._form_layout.addRow("Poll Interval (s)", self._dspin(node.poll_interval, 0.1, 5.0, lambda v: self._set(node, "poll_interval", v)))

    def _change_image(self, node: Any, attr: str) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            try:
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                self._set(node, attr, b64_data)
                self._rebuild_form(node) # Refresh to show new image
            except Exception as e:
                print(f"Error loading image: {e}")

    def _build_branch(self, node: BranchNode) -> None:
        self._form_layout.addRow("Condition Key", self._line_edit(node.condition_key, lambda v: self._set(node, "condition_key", v)))
        self._add_hint("This key must exist in the\nexecution context as a bool.")

    def _build_iterate(self, node: IterateNode) -> None:
        self._form_layout.addRow("CSV Path", self._line_edit(node.csv_file_path, lambda v: self._set(node, "csv_file_path", v)))
        self._form_layout.addRow("CSV Column", self._line_edit(node.csv_column, lambda v: self._set(node, "csv_column", v)))
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))

    def _build_dynamic_iterate(self, node: DynamicIterateNode) -> None:
        self._form_layout.addRow("Source Key", self._line_edit(
            node.source_key, lambda v: self._set(node, "source_key", v)
        ))
        self._form_layout.addRow("Output Key", self._line_edit(
            node.output_key, lambda v: self._set(node, "output_key", v)
        ))
        self._add_hint(
            "source_key must match the output_key of a\n"
            "LocateElement (find_all) or LLM extraction node.\n"
            "Each iteration puts the current item into output_key."
        )

    def _build_compare(self, node: CompareNode) -> None:
        self._form_layout.addRow(
            "Left Operand",
            self._line_edit(node.left_operand, lambda v: self._set(node, "left_operand", v))
        )
        self._form_layout.addRow("Operator", self._combo(
            [op.value for op in CompareOp], node.operator.value,
            lambda v: self._set(node, "operator", CompareOp(v))
        ))
        self._form_layout.addRow(
            "Right Operand",
            self._line_edit(node.right_operand, lambda v: self._set(node, "right_operand", v))
        )
        cs_cb = QCheckBox()
        cs_cb.setChecked(node.case_sensitive)
        cs_cb.toggled.connect(lambda v: self._set(node, "case_sensitive", v))
        self._form_layout.addRow("Case Sensitive", cs_cb)
        self._add_hint(
            "Use {{key}} to pull values from context.\n"
            "Numeric ops (num_*) parse both sides as float.\n"
            "Routes to TRUE or FALSE edge."
        )

    def _build_subgraph(self, node: SubGraphNode) -> None:
        self._form_layout.addRow("Graph Path", self._line_edit(node.sub_graph_path, lambda v: self._set(node, "sub_graph_path", v)))
