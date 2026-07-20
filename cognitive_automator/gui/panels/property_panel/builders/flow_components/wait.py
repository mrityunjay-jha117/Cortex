"""
=============================================================================
 WAIT.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
import base64
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from cognitive_automator.graph_model import WaitNode
from cognitive_automator.gui.constants import APP_TEXT_DIM, APP_BORDER

class WaitMixin:
    def _build_wait(self, node: WaitNode) -> None:
        self._form_layout.addRow("Static Delay (s)", self._dspin( # type: ignore
            node.static_seconds or 1.0, 0.0, 60.0, lambda v: self._set(node, "static_seconds", v) # type: ignore
        ))
        
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
        
        self._form_layout.addRow("Wait for\nImage", img_container) # type: ignore

        self._form_layout.addRow("Confidence", self._dspin(node.wait_confidence, 0.5, 1.0, lambda v: self._set(node, "wait_confidence", v))) # type: ignore
        self._form_layout.addRow("Timeout (s)", self._dspin(node.timeout_seconds, 1.0, 300.0, lambda v: self._set(node, "timeout_seconds", v))) # type: ignore
        self._form_layout.addRow("Poll Interval (s)", self._dspin(node.poll_interval, 0.1, 5.0, lambda v: self._set(node, "poll_interval", v))) # type: ignore

    def _change_image(self, node: Any, attr: str) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)" # type: ignore
        )
        if path:
            try:
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                self._set(node, attr, b64_data) # type: ignore
                self._rebuild_form(node) # type: ignore
            except Exception as e:
                print(f"Error loading image: {e}")
