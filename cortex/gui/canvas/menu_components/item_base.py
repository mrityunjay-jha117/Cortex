"""
=============================================================================
 ITEM_BASE.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import PyQt6.QtGui as QtGui
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import pyqtSignal, QPropertyAnimation
from PyQt6.QtGui import QColor

class AnimatedMenuItemBase(QWidget):
    clicked = pyqtSignal()
    hovered = pyqtSignal(object)
    
    def __init__(self, text: str, parent=None, is_submenu=False):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.text = text
        self.is_submenu = is_submenu
        self.submenu = None
        self.setMouseTracking(True)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)
        
        self.anim_offset = QPropertyAnimation(self.shadow, b"offset")
        self.anim_offset.setDuration(100)
        
        self.anim_blur = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim_blur.setDuration(100)

        self._is_pressed = False
