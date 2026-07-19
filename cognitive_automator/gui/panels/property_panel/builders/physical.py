"""
gui/panels/property_panel/builders/physical.py — Physical Node Builders

This file implements UI forms for configuring physical automation nodes.
It includes fields for X/Y coordinates, keypress designations, PyAutoGUI actions, and interaction durations.
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



class PhysicalBuilders:

    def _build_mouse(self, node: MouseNode) -> None:
        action_combo = self._combo(
            [a.value for a in MouseAction], node.action.value,
            lambda v: [self._set(node, "action", MouseAction(v)), self._rebuild_form(node)]
        )
        self._form_layout.addRow("Action", action_combo)

        if node.action == MouseAction.SCROLL:
            self._form_layout.addRow("Scroll Amount", self._spin(node.scroll_amount, -10000, 10000, lambda v: self._set(node, "scroll_amount", v)))
            self._add_hint(
                "Negative = Scroll Down (typical)\n"
                "Positive = Scroll Up\n"
                "Windows: -120 is one notch. Try -1200 for a significant scroll."
            )

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
        self._form_layout.addRow("Duration (s)", self._dspin(node.duration, 0.0, 5.0, lambda v: self._set(node, "duration", v)))

    def _build_keyboard(self, node: KeyboardNode) -> None:
        action_combo = self._combo(
            [a.value for a in KeyboardAction], node.action.value,
            lambda v: [self._set(node, "action", KeyboardAction(v)), self._rebuild_form(node)]
        )
        self._form_layout.addRow("Action", action_combo)

        if node.action == KeyboardAction.TYPEWRITE:
            text_edit = self._plain_text(node.text, lambda v: self._set(node, "text", v))
            text_edit.setMaximumHeight(60)
            self._form_layout.addRow("Text", text_edit)
            self._form_layout.addRow("Interval (s)", self._dspin(node.interval, 0.0, 1.0, lambda v: self._set(node, "interval", v)))
        elif node.action == KeyboardAction.PRESS:
            self._form_layout.addRow("Key", self._line_edit(node.key, lambda v: self._set(node, "key", v)))
        elif node.action == KeyboardAction.HOTKEY:
            self._form_layout.addRow("Keys (hotkey)", self._line_edit(
                ",".join(node.keys),
                lambda v: self._set(node, "keys", [k.strip() for k in v.split(",") if k.strip()])
            ))
        elif node.action == KeyboardAction.PASTE:
            text_edit = self._plain_text(node.text, lambda v: self._set(node, "text", v))
            text_edit.setMaximumHeight(60)
            self._form_layout.addRow("Text to Paste", text_edit)
        elif node.action == KeyboardAction.SELECT_ALL:
            self._add_hint("Automatically performs Ctrl+A (or Cmd+A).")

    def _build_clipboard(self, node: ClipboardNode) -> None:
        action_combo = self._combo(
            [a.value for a in ClipboardAction], node.action.value,
            lambda v: self._set(node, "action", ClipboardAction(v))
        )
        self._form_layout.addRow("Action", action_combo)
        text_edit = self._plain_text(node.write_text, lambda v: self._set(node, "write_text", v))
        text_edit.setMaximumHeight(60)
        self._form_layout.addRow("Write Text", text_edit)

    def _build_locate(self, node: LocateElementNode) -> None:
        # Reference image preview
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
                    self._refresh_locate_preview(node)
            except Exception:
                self._locate_img_label.setText("(image decode error)")
        else:
            self._locate_img_label.setText("No image captured")
            self._locate_img_label.setStyleSheet(f"color:{APP_TEXT_DIM}; font-size:11px;")
        
        self._locate_img_label.setStyleSheet(
            f"border:1px solid {APP_BORDER}; border-radius:4px; "
            "padding:4px; background:#1a1a2e;"
        )
        self._locate_img_label.setFixedHeight(130)
        img_vbox.addWidget(self._locate_img_label)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0,0,0,0)
        
        change_btn = QPushButton("Change...")
        change_btn.clicked.connect(lambda: self._change_image(node, "reference_image_b64"))
        btn_layout.addWidget(change_btn)

        if self._locate_full_pixmap:
            view_btn = QPushButton("View Full")
            view_btn.clicked.connect(lambda: ImageViewer(self._locate_full_pixmap, self).exec()) # type: ignore[arg-type]
            btn_layout.addWidget(view_btn)
        
        img_vbox.addWidget(btn_row)

        self._form_layout.addRow("Reference\nImage", img_container)

        # Sliders for offset
        if self._locate_full_pixmap:
            w = self._locate_full_pixmap.width()
            h = self._locate_full_pixmap.height()
            
            def on_x_offset(v: int) -> None:
                self._set(node, "x_offset", v)
                self._refresh_locate_preview(node)
                x_val_label.setText(str(v))

            x_row = QWidget()
            x_layout = QHBoxLayout(x_row)
            x_layout.setContentsMargins(0,0,0,0)
            x_slider = self._slider(node.x_offset, -w//2, w//2, on_x_offset)
            x_val_label = QLabel(str(node.x_offset))
            x_val_label.setFixedWidth(30)
            x_layout.addWidget(x_slider)
            x_layout.addWidget(x_val_label)
            self._form_layout.addRow("X Offset", x_row)

            def on_y_offset(v: int) -> None:
                self._set(node, "y_offset", v)
                self._refresh_locate_preview(node)
                y_val_label.setText(str(v))

            y_row = QWidget()
            y_layout = QHBoxLayout(y_row)
            y_layout.setContentsMargins(0,0,0,0)
            y_slider = self._slider(node.y_offset, -h//2, h//2, on_y_offset)
            y_val_label = QLabel(str(node.y_offset))
            y_val_label.setFixedWidth(30)
            y_layout.addWidget(y_slider)
            y_layout.addWidget(y_val_label)
            self._form_layout.addRow("Y Offset", y_row)

        self._form_layout.addRow("Confidence", self._dspin(
            node.confidence, 0.5, 1.0, lambda v: self._set(node, "confidence", v), step=0.05
        ))
        grayscale_cb = QCheckBox()
        grayscale_cb.setChecked(node.grayscale)
        grayscale_cb.toggled.connect(lambda v: self._set(node, "grayscale", v))
        self._form_layout.addRow("Grayscale", grayscale_cb)

        find_all_cb = QCheckBox()
        find_all_cb.setChecked(node.find_all)
        find_all_cb.setToolTip(
            "Find ALL matches on screen and click each one.\n"
            "Useful for lists where multiple identical buttons exist."
        )
        find_all_cb.toggled.connect(lambda v: self._set(node, "find_all", v))
        self._form_layout.addRow("Find All", find_all_cb)

        self._form_layout.addRow("Timeout (s)", self._dspin(node.timeout_seconds, 1.0, 120.0, lambda v: self._set(node, "timeout_seconds", v)))
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
        
        # --- AI Fallback Mechanism ---
        self._add_section("AI Fallback")
        fallback_cb = QCheckBox()
        fallback_cb.setChecked(node.use_fallback)
        fallback_cb.toggled.connect(lambda v: [self._set(node, "use_fallback", v), self._rebuild_form(node)])
        self._form_layout.addRow("Enable AI Fallback", fallback_cb)

        if node.use_fallback:
            fb_edit = self._plain_text(node.fallback_prompt, lambda v: self._set(node, "fallback_prompt", v))
            fb_edit.setMaximumHeight(60)
            self._form_layout.addRow("AI Search Prompt", fb_edit)

            self._form_layout.addRow("Model Override", self._line_edit(node.fallback_model_override or "", lambda v: self._set(node, "fallback_model_override", v if v else None)))
            self._add_hint("Describe the element (e.g. 'blue login button'). Only runs if primary image match fails.")
            
            self._form_layout.addRow("Auto-Heal", self._toggle(node.auto_heal, lambda v: self._set(node, "auto_heal", v)))
            self._add_hint("Automatically update coordinates and image if AI succeeds.")

    def _build_locate_and_click(self, node: LocateAndClickNode) -> None:
        # Re-use the visual locating UI
        self._build_locate(node)
        
        self._add_section("Mouse Action")
        action_combo = self._combo(
            [a.value for a in MouseAction if a not in (MouseAction.DRAG_TO, MouseAction.SCROLL)], 
            node.action.value,
            lambda v: self._set(node, "action", MouseAction(v))
        )
        self._form_layout.addRow("Click Action", action_combo)
        
        self._form_layout.addRow("Button", self._combo(
            ["left", "right", "middle"], node.button,
            lambda v: self._set(node, "button", v)
        ))
        
        self._form_layout.addRow("Duration (s)", self._dspin(node.duration, 0.0, 5.0, lambda v: self._set(node, "duration", v)))
        self._form_layout.addRow("Wait After (s)", self._dspin(node.wait_after_click, 0.0, 10.0, lambda v: self._set(node, "wait_after_click", v)))
