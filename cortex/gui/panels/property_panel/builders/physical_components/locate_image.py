"""
=============================================================================
 LOCATE_IMAGE.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import base64
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from cortex.gui.constants import APP_BORDER, APP_TEXT_DIM
from cortex.gui.panels.property_panel.base_components.image_viewer import ImageViewer

class LocateImageMixin:
    def _build_locate_image(self, node) -> None:
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
            self._locate_img_label.setText("No image captured") # type: ignore
            self._locate_img_label.setStyleSheet(f"color:{APP_TEXT_DIM}; font-size:11px;") # type: ignore
        
        self._locate_img_label.setStyleSheet( # type: ignore
            f"border:1px solid {APP_BORDER}; border-radius:4px; "
            "padding:4px; background:#1a1a2e;"
        )
        self._locate_img_label.setFixedHeight(130) # type: ignore
        img_vbox.addWidget(self._locate_img_label) # type: ignore

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0,0,0,0)
        
        change_btn = QPushButton("Change...")
        change_btn.clicked.connect(lambda: self._change_image(node, "reference_image_b64")) # type: ignore
        btn_layout.addWidget(change_btn)

        if self._locate_full_pixmap: # type: ignore
            view_btn = QPushButton("View Full")
            view_btn.clicked.connect(lambda: ImageViewer(self._locate_full_pixmap, self).exec()) # type: ignore
            btn_layout.addWidget(view_btn)
        
        img_vbox.addWidget(btn_row)
        self._form_layout.addRow("Reference\nImage", img_container) # type: ignore
