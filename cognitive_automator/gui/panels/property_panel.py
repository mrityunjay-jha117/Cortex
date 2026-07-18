"""
gui/panels/property_panel.py — Right-side panel for editing node properties.

Uses a QStackedWidget to show the correct form for each node type.
All changes immediately update the underlying Pydantic model.
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

class PropertyPanel(QWidget):
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

    def _build_marker(self, node: AnyNode, desc: str) -> None:
        lbl = QLabel(desc)
        lbl.setStyleSheet(f"color:{APP_TEXT_DIM};")
        lbl.setWordWrap(True)
        self._form_layout.addRow("", lbl)

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

    def _build_write_file(self, node: WriteFileNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v)))
        self._form_layout.addRow("Content", self._plain_text(node.content_template, lambda v: self._set(node, "content_template", v)))
        
        append_cb = QCheckBox()
        append_cb.setChecked(node.append)
        append_cb.toggled.connect(lambda v: self._set(node, "append", v))
        self._form_layout.addRow("Append Mode", append_cb)
        self._form_layout.addRow("Status Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))

    def _set_schema(self, node: Any, v: str) -> None:
        import json
        try:
            schema = json.loads(v)
            self._set(node, "output_schema", schema)
        except Exception:
            pass

    def _build_llm(self, node: Any) -> None:
        self._form_layout.addRow("Model", self._line_edit(node.model, lambda v: self._set(node, "model", v)))

        temp_label = QLabel(f"{node.temperature:.2f}")
        temp_label.setStyleSheet(f"color:{APP_ACCENT}; min-width:35px;")
        temp_slider = QSlider(Qt.Orientation.Horizontal)
        temp_slider.setRange(0, 200)
        temp_slider.setValue(int(node.temperature * 100))
        def on_temp(v: int) -> None:
            val = v / 100.0
            self._set(node, "temperature", val)
            temp_label.setText(f"{val:.2f}")
        temp_slider.valueChanged.connect(on_temp)
        temp_row = QWidget()
        temp_row_layout = QHBoxLayout(temp_row)
        temp_row_layout.setContentsMargins(0, 0, 0, 0)
        temp_row_layout.addWidget(temp_slider)
        temp_row_layout.addWidget(temp_label)
        self._form_layout.addRow("Temperature", temp_row)

        self._form_layout.addRow("Max Tokens", self._spin(node.max_tokens, 64, 8192, lambda v: self._set(node, "max_tokens", v)))

        prompt_edit = self._plain_text(node.prompt_template, lambda v: self._set(node, "prompt_template", v))
        prompt_edit.setMinimumHeight(120)
        self._form_layout.addRow("Prompt Template", prompt_edit)
        self._add_hint("Use {{variable}} for context injection")

        sys_prompt_edit = self._plain_text(node.system_prompt, lambda v: self._set(node, "system_prompt", v))
        sys_prompt_edit.setMaximumHeight(80)
        self._form_layout.addRow("System Prompt", sys_prompt_edit)

        # Multi-modal support: image context keys
        if hasattr(node, "image_context_keys"):
            self._form_layout.addRow("Image Context Keys", self._line_edit(
                ", ".join(node.image_context_keys),
                lambda v: self._set(node, "image_context_keys", [k.strip() for k in v.split(",") if k.strip()])
            ))

        if hasattr(node, "output_key"):
            self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))

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

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

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
