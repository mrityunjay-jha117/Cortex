"""
=============================================================================
 KEYBOARD.PY (screen_region_selector_components)
=============================================================================
This module is a microservice component for screen_region_selector_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class KeyboardMixin:
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm()
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel()
