"""
=============================================================================
 IMAGE_VIEWER.PY (base_components)
=============================================================================
This module is a microservice component for base_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from typing import Optional
from PyQt6.QtWidgets import QWidget

class ImageViewer(QDialog):
    def __init__(self, pixmap: QPixmap, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Reference Image")
        layout = QVBoxLayout(self)
        lbl = QLabel()
        lbl.setPixmap(pixmap)
        layout.addWidget(lbl)
        self.setModal(True)
