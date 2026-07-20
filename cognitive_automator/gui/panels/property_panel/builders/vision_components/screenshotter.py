"""
=============================================================================
 SCREENSHOTTER.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
import base64
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from cognitive_automator.graph_model import ScreenshotterNode, ScreenshotMode, DetectionMode
from cognitive_automator.gui.constants import APP_BORDER

class ScreenshotterMixin:
    def _build_screenshotter(self, node: ScreenshotterNode) -> None:
        self._add_section("Scroll & Capture") # type: ignore
        self._form_layout.addRow("Mode", self._combo( # type: ignore
            [m.value for m in ScreenshotMode], node.mode.value,
            lambda v: [self._set(node, "mode", ScreenshotMode(v)), self._rebuild_form(node)] # type: ignore
        ))
        if node.mode == ScreenshotMode.N_TIMES:
            self._form_layout.addRow("Number of Captures", self._spin(node.n_times, 1, 100, lambda v: self._set(node, "n_times", v))) # type: ignore
        
        self._form_layout.addRow("Scroll Amount", self._spin(node.scroll_amount, -5000, 5000, lambda v: self._set(node, "scroll_amount", v))) # type: ignore
        self._form_layout.addRow("Wait (s)", self._dspin(node.wait_per_scroll, 0.1, 10.0, lambda v: self._set(node, "wait_per_scroll", v))) # type: ignore
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        
        self._add_section("Image Action (Optional)") # type: ignore
        self._form_layout.addRow("Detection Mode", self._combo( # type: ignore
            [m.value for m in DetectionMode], node.detection_mode.value,
            lambda v: [self._set(node, "detection_mode", DetectionMode(v)), self._rebuild_form(node)] # type: ignore
        ))

        if node.detection_mode != DetectionMode.NONE:
            img_container = QWidget()
            img_vbox = QVBoxLayout(img_container)
            img_vbox.setContentsMargins(0, 0, 0, 0)

            self._locate_img_label = QLabel() # type: ignore
            self._locate_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # type: ignore
            self._locate_full_pixmap = None # type: ignore

            if node.reference_image_b64:
                try:
                    data = base64.b64decode(node.reference_image_b64)
                    pm = QPixmap()
                    pm.loadFromData(QByteArray(data))
                    if not pm.isNull():
                        self._locate_full_pixmap = pm # type: ignore
                        self._refresh_locate_preview(node) # type: ignore
                except Exception:
                    self._locate_img_label.setText("(image decode error)") # type: ignore
            else:
                self._locate_img_label.setText("No target image") # type: ignore
            
            self._locate_img_label.setStyleSheet(f"border:1px solid {APP_BORDER}; background:#1a1a2e;") # type: ignore
            self._locate_img_label.setFixedHeight(130) # type: ignore
            img_vbox.addWidget(self._locate_img_label) # type: ignore

            change_btn = QPushButton("Capture/Set Target...")
            change_btn.clicked.connect(lambda: self._change_image(node, "reference_image_b64")) # type: ignore
            img_vbox.addWidget(change_btn)
            self._form_layout.addRow("Target Image", img_container) # type: ignore

            if self._locate_full_pixmap: # type: ignore
                w, h = self._locate_full_pixmap.width(), self._locate_full_pixmap.height() # type: ignore
                def on_x(v: int) -> None:
                    self._set(node, "x_offset", v) # type: ignore
                    self._refresh_locate_preview(node) # type: ignore
                self._form_layout.addRow("X Offset", self._slider(node.x_offset, -w//2, w//2, on_x)) # type: ignore
                
                def on_y(v: int) -> None:
                    self._set(node, "y_offset", v) # type: ignore
                    self._refresh_locate_preview(node) # type: ignore
                self._form_layout.addRow("Y Offset", self._slider(node.y_offset, -h//2, h//2, on_y)) # type: ignore

            self._form_layout.addRow("Confidence", self._dspin(node.confidence, 0.5, 1.0, lambda v: self._set(node, "confidence", v), step=0.05)) # type: ignore
            self._form_layout.addRow("Wait After Click (s)", self._dspin(node.wait_after_click, 0.1, 10.0, lambda v: self._set(node, "wait_after_click", v))) # type: ignore
