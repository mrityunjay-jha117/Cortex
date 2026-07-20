"""
=============================================================================
 LAYOUT.PY (helpers_components)
=============================================================================
This module is a microservice component for helpers_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QLabel
from cortex.gui.constants import APP_ACCENT

class LayoutHelpers:
    def _add_section(self, title: str) -> None:
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"color:{APP_ACCENT}; font-size:10px; font-weight:bold; "
                          f"letter-spacing:1px; padding-top:12px;")
        self._form_layout.addRow(lbl)
