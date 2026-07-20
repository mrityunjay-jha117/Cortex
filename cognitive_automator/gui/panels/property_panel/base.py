"""
=============================================================================
 PROPERTY PANEL BASE
=============================================================================
This module provides the core framework for the property editor.
It defines how the panel reacts to node selection and commits changes.

Key Features:
1. Connects UI form inputs back to the underlying Pydantic node models.
2. Manages the layout lifecycle when switching between different nodes.

Think of this module as the scaffolding holding the settings dials.
=============================================================================
"""

from __future__ import annotations

from typing import Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFormLayout, QLabel, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from cognitive_automator.graph_model import AnyNode
from cognitive_automator.gui.constants import APP_BORDER

from .builders import PropertyPanelBuilders
from .helpers import PropertyPanelHelpers
from .base_components.image_viewer import ImageViewer
from .base_components.styles import PROPERTY_PANEL_STYLESHEET
from .base_components.form_rebuilder import FormRebuilderMixin

class PropertyPanel(PropertyPanelBuilders, PropertyPanelHelpers, FormRebuilderMixin, QWidget):
    """Emits node_changed when a property is edited."""
    node_changed = pyqtSignal(str)   # node_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_node: AnyNode | None = None  # type: ignore[type-arg]
        self._updating = False

        # Locate preview state
        self._locate_full_pixmap: QPixmap | None = None
        self._locate_img_label: QLabel | None = None

        self.setStyleSheet(PROPERTY_PANEL_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QLabel("Select a node to configure")
        self._header.setStyleSheet(
            f"background:#111827; color:#FFFFFF; "
            f"padding:12px 16px; border-bottom:2px solid {APP_BORDER}; "
            "font-weight:bold; font-size:14px;"
        )
        layout.addWidget(self._header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border:none; background:transparent;")

        self._stacked = QStackedWidget()
        self._stacked.setStyleSheet(f"background:transparent;")

        # Blank page
        blank = QWidget()
        blank.setObjectName("propPage")
        blank_layout = QVBoxLayout(blank)
        hint = QLabel("Click a node on the canvas\nto view its properties.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color:#FFFFFF; font-size:14px; font-weight:bold;")
        blank_layout.addWidget(hint)
        self._stacked.addWidget(blank)   # index 0

        # Generic page (for all node types)
        self._form_widget = QWidget()
        self._form_widget.setObjectName("propPage")
        self._form_layout = QFormLayout(self._form_widget)
        self._form_layout.setContentsMargins(16, 16, 16, 16)
        self._form_layout.setSpacing(10)
        self._form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._stacked.addWidget(self._form_widget)  # index 1

        scroll.setWidget(self._stacked)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll, stretch=1)

        self.setMinimumWidth(300)

    def _add_hint(self, text: str) -> None:
        hint = QLabel(text)
        hint.setStyleSheet(f"color:#CCCCCC; font-size:12px; font-weight:bold;")
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
