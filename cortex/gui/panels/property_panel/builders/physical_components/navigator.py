"""
=============================================================================
 NAVIGATOR.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import base64
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from cortex.gui.constants import APP_BORDER, APP_TEXT_DIM, APP_SURFACE2
from cortex.graph_model import NavigatorNode, NavigationAction

class NavigatorBuilder:
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
        change_btn.setStyleSheet(f"background: {APP_SURFACE2}; color: #FFFFFF; border: 1px solid {APP_BORDER};")
        change_btn.clicked.connect(lambda: self._change_image(node, "reference_image_b64"))
        btn_layout.addWidget(change_btn)

        if node.reference_image_b64:
            clear_btn = QPushButton("Clear")
            clear_btn.setStyleSheet(f"background: {APP_SURFACE2}; color: #FFFFFF; border: 1px solid {APP_BORDER};")
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
