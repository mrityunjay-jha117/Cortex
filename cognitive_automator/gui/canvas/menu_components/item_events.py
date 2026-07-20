"""
=============================================================================
 ITEM_EVENTS.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import Qt, QPointF

class AnimatedMenuItemEvents:
    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor) # type: ignore
        self.anim_offset.setEndValue(QPointF(0, 4)) # type: ignore
        self.anim_blur.setEndValue(12) # type: ignore
        self.anim_offset.start() # type: ignore
        self.anim_blur.start() # type: ignore
        self.update() # type: ignore
        self.hovered.emit(self) # type: ignore
        super().enterEvent(event) # type: ignore
        
    def leaveEvent(self, event):
        self.anim_offset.setEndValue(QPointF(0, 2)) # type: ignore
        self.anim_blur.setEndValue(8) # type: ignore
        self.anim_offset.start() # type: ignore
        self.anim_blur.start() # type: ignore
        self.update() # type: ignore
        super().leaveEvent(event) # type: ignore
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_submenu: # type: ignore
            self._is_pressed = True # type: ignore
            self.anim_offset.setEndValue(QPointF(0, 1)) # type: ignore
            self.anim_blur.setEndValue(2) # type: ignore
            self.anim_offset.start() # type: ignore
            self.anim_blur.start() # type: ignore
            self.update() # type: ignore
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_pressed and not self.is_submenu: # type: ignore
            self._is_pressed = False # type: ignore
            self.anim_offset.setEndValue(QPointF(0, 4) if self.underMouse() else QPointF(0, 2)) # type: ignore
            self.anim_blur.setEndValue(12 if self.underMouse() else 8) # type: ignore
            self.anim_offset.start() # type: ignore
            self.anim_blur.start() # type: ignore
            self.update() # type: ignore
            if self.rect().contains(event.pos()): # type: ignore
                self.clicked.emit() # type: ignore
