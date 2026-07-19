"""
gui/panels/property_panel/helpers.py — Property Panel UI Helpers

This file contains modular PyQt6 widget generators.
It provides standardized functions for creating labeled text inputs, combo boxes, checkboxes, and numerical spinboxes, ensuring a unified aesthetic across all property forms.
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


class PropertyPanelHelpers:


    def _add_section(self, title: str) -> None:
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"color:{APP_ACCENT}; font-size:10px; font-weight:bold; "
                          f"letter-spacing:1px; padding-top:12px;")
        self._form_layout.addRow(lbl)

    def _line_edit(self, value: str, setter: Any, drop_handler: Any | None = None) -> QLineEdit:
        class DropLineEdit(QLineEdit):
            def __init__(self, contents: str, parent: QWidget | None = None) -> None:
                super().__init__(contents, parent)
                self.setAcceptDrops(True)
            
            def dragEnterEvent(self, event: Any) -> None:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
            
            def dropEvent(self, event: Any) -> None:
                urls = event.mimeData().urls()
                if urls:
                    file_path = urls[0].toLocalFile()
                    self.setText(file_path)
                    if drop_handler:
                        drop_handler(file_path)

        w = DropLineEdit(value)
        w.textChanged.connect(lambda v: self._safe_set(setter, v))
        return w

    def _plain_text(self, value: str, setter: Any) -> QPlainTextEdit:
        w = QPlainTextEdit(value)
        w.setTabChangesFocus(True)
        w.textChanged.connect(lambda: self._safe_set(setter, w.toPlainText()))
        return w

    def _spin(self, value: int, min_v: int, max_v: int, setter: Any) -> QSpinBox:
        w = QSpinBox()
        w.setRange(min_v, max_v)
        w.setValue(value)
        w.valueChanged.connect(lambda v: self._safe_set(setter, v))
        return w

    def _dspin(self, value: float, min_v: float, max_v: float,
               setter: Any, step: float = 0.1) -> QDoubleSpinBox:
        w = QDoubleSpinBox()
        w.setRange(min_v, max_v)
        w.setSingleStep(step)
        w.setDecimals(2)
        w.setValue(value)
        w.valueChanged.connect(lambda v: self._safe_set(setter, v))
        return w

    def _combo(self, options: list[str], current: str, setter: Any) -> QComboBox:
        w = QComboBox()
        w.addItems(options)
        if current in options:
            w.setCurrentText(current)
        w.currentTextChanged.connect(lambda v: self._safe_set(setter, v))
        return w

    def _safe_set(self, setter: Any, value: Any) -> None:
        if self._updating:
            return
        try:
            setter(value)
            if self._current_node:
                self.node_changed.emit(self._current_node.id)
        except Exception:
            pass

    def _set(self, node: Any, attr: str, value: Any) -> None:
        setattr(node, attr, value)
        if not self._updating:
            self.node_changed.emit(node.id)

    def _refresh_locate_preview(self, node: Any) -> None:
        if not self._locate_full_pixmap or not self._locate_img_label:
            return
        
        # Draw crosshair on a copy
        pm = self._locate_full_pixmap.copy()
        painter = QPainter(pm)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        
        # Robust attribute check
        x_off = getattr(node, "x_offset", 0)
        y_off = getattr(node, "y_offset", 0)
        
        cx = pm.width() // 2 + x_off
        cy = pm.height() // 2 + y_off
        
        # Draw crosshair
        painter.drawLine(cx - 10, cy, cx + 10, cy)
        painter.drawLine(cx, cy - 10, cx, cy + 10)
        painter.end()
        
        # Scale for display
        scaled = pm.scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        self._locate_img_label.setPixmap(scaled)

    def _slider(self, value: int, min_v: int, max_v: int, setter: Any) -> QSlider:
        w = QSlider(Qt.Orientation.Horizontal)
        w.setRange(min_v, max_v)
        w.setValue(value)
        w.valueChanged.connect(lambda v: self._safe_set(setter, v))
        return w

    def _toggle(self, value: bool, setter: Any) -> QPushButton:
        btn = QPushButton("ON" if value else "OFF")
        btn.setCheckable(True)
        btn.setChecked(value)
        
        def on_toggle(checked: bool) -> None:
            btn.setText("ON" if checked else "OFF")
            self._safe_set(setter, checked)
            
        btn.toggled.connect(on_toggle)
        return btn

    def _build_navigator(self, node: NavigatorNode) -> None:
        self._add_section("Navigation Focus (Optional)")
        
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
            self._locate_img_label.setText("No focus image")
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
        
        change_btn = QPushButton("Set Image...")
        change_btn.clicked.connect(lambda: self._change_image(node, "reference_image_b64"))
        btn_layout.addWidget(change_btn)

        if node.reference_image_b64:
            clear_btn = QPushButton("Clear")
            clear_btn.clicked.connect(lambda: [self._set(node, "reference_image_b64", ""), self._rebuild_form(node)])
            btn_layout.addWidget(clear_btn)
        
        img_vbox.addWidget(btn_row)
        self._form_layout.addRow("Focus Image", img_container)

        if self._locate_full_pixmap:
            w = self._locate_full_pixmap.width()
            h = self._locate_full_pixmap.height()
            
            def on_x_offset(v: int) -> None:
                self._set(node, "x_offset", v)
                self._refresh_locate_preview(node) # type: ignore[arg-type]
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
                self._refresh_locate_preview(node) # type: ignore[arg-type]
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

        self._add_section("Navigation Action")
        self._form_layout.addRow("Action", self._combo(
            [a.value for a in NavigationAction], node.action.value,
            lambda v: self._set(node, "action", NavigationAction(v))
        ))
        self._form_layout.addRow("Repeat", self._spin(node.repeat, 1, 100, lambda v: self._set(node, "repeat", v)))
