"""
gui/panels/property_panel/builders/vision.py — Vision Node Builders

This file implements UI forms for configuring computer vision nodes.
It manages the UI for capturing screen regions, adjusting confidence thresholds, and rendering the embedded Base64 reference images.
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



class VisionBuilders:

    def _build_screenshotter(self, node: ScreenshotterNode) -> None:
        self._add_section("Scroll & Capture")
        self._form_layout.addRow("Mode", self._combo(
            [m.value for m in ScreenshotMode], node.mode.value,
            lambda v: [self._set(node, "mode", ScreenshotMode(v)), self._rebuild_form(node)]
        ))
        if node.mode == ScreenshotMode.N_TIMES:
            self._form_layout.addRow("Number of Captures", self._spin(node.n_times, 1, 100, lambda v: self._set(node, "n_times", v)))
        
        self._form_layout.addRow("Scroll Amount", self._spin(node.scroll_amount, -5000, 5000, lambda v: self._set(node, "scroll_amount", v)))
        self._form_layout.addRow("Wait (s)", self._dspin(node.wait_per_scroll, 0.1, 10.0, lambda v: self._set(node, "wait_per_scroll", v)))
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        
        # --- Detection Action Section ---
        self._add_section("Image Action (Optional)")
        self._form_layout.addRow("Detection Mode", self._combo(
            [m.value for m in DetectionMode], node.detection_mode.value,
            lambda v: [self._set(node, "detection_mode", DetectionMode(v)), self._rebuild_form(node)]
        ))

        # Always show image capture if mode is not NONE
        if node.detection_mode != DetectionMode.NONE:
            img_container = QWidget()
            img_vbox = QVBoxLayout(img_container)
            img_vbox.setContentsMargins(0, 0, 0, 0)

            self._locate_img_label = QLabel()
            self._locate_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._locate_full_pixmap = None

            if node.reference_image_b64:
                try:
                    data = base64.b64decode(node.reference_image_b64)
                    pm = QPixmap()
                    pm.loadFromData(QByteArray(data))
                    if not pm.isNull():
                        self._locate_full_pixmap = pm
                        self._refresh_locate_preview(node) # type: ignore[arg-type]
                except Exception:
                    self._locate_img_label.setText("(image decode error)")
            else:
                self._locate_img_label.setText("No target image")
            
            self._locate_img_label.setStyleSheet(f"border:1px solid {APP_BORDER}; background:#1a1a2e;")
            self._locate_img_label.setFixedHeight(130)
            img_vbox.addWidget(self._locate_img_label)

            change_btn = QPushButton("Capture/Set Target...")
            change_btn.clicked.connect(lambda: self._change_image(node, "reference_image_b64"))
            img_vbox.addWidget(change_btn)
            self._form_layout.addRow("Target Image", img_container)

            # Offset Sliders
            if self._locate_full_pixmap:
                w, h = self._locate_full_pixmap.width(), self._locate_full_pixmap.height()
                def on_x(v: int) -> None:
                    self._set(node, "x_offset", v)
                    self._refresh_locate_preview(node) # type: ignore[arg-type]
                self._form_layout.addRow("X Offset", self._slider(node.x_offset, -w//2, w//2, on_x))
                
                def on_y(v: int) -> None:
                    self._set(node, "y_offset", v)
                    self._refresh_locate_preview(node) # type: ignore[arg-type]
                self._form_layout.addRow("Y Offset", self._slider(node.y_offset, -h//2, h//2, on_y))

            self._form_layout.addRow("Confidence", self._dspin(node.confidence, 0.5, 1.0, lambda v: self._set(node, "confidence", v), step=0.05))
            self._form_layout.addRow("Wait After Click (s)", self._dspin(node.wait_after_click, 0.1, 10.0, lambda v: self._set(node, "wait_after_click", v)))

    def _build_ocr(self, node: GenerativeOCRNode) -> None:
        bbox_str = f"{node.bbox[0]},{node.bbox[1]},{node.bbox[2]},{node.bbox[3]}"
        def set_bbox(v: str) -> None:
            parts = [int(x.strip()) for x in v.split(",") if x.strip()]
            if len(parts) == 4:
                self._set(node, "bbox", tuple(parts))
        self._form_layout.addRow("BBox (L,T,R,B)", self._line_edit(bbox_str, set_bbox))
        self._form_layout.addRow("Model", self._line_edit(node.model, lambda v: self._set(node, "model", v)))
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        self._form_layout.addRow("System Prompt", self._plain_text(node.system_prompt, lambda v: self._set(node, "system_prompt", v)))

    def _build_vision_extraction(self, node: VisionExtractionNode) -> None:
        bbox_str = f"{node.bbox[0]},{node.bbox[1]},{node.bbox[2]},{node.bbox[3]}"
        def set_bbox(v: str) -> None:
            parts = [int(x.strip()) for x in v.split(",") if x.strip()]
            if len(parts) == 4:
                self._set(node, "bbox", tuple(parts))
        self._form_layout.addRow("BBox (L,T,R,B)", self._line_edit(bbox_str, set_bbox))
        self._form_layout.addRow("Model", self._line_edit(node.model, lambda v: self._set(node, "model", v)))
        self._form_layout.addRow("Prompt", self._plain_text(node.prompt_template, lambda v: self._set(node, "prompt_template", v)))
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        
        schema_edit = self._plain_text(
            json.dumps(node.output_schema, indent=2) if node.output_schema else "{}",
            lambda v: self._set_schema(node, v)
        )
        self._form_layout.addRow("JSON Schema", schema_edit)
