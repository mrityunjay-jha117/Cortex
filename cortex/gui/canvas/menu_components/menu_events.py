"""
=============================================================================
 MENU_EVENTS.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect

class AnimatedMenuEvents:
    def _on_item_hovered(self, item):
        if self.active_submenu and self.active_submenu != item.submenu: # type: ignore
            self.active_submenu.close() # type: ignore
            self.active_submenu = None # type: ignore
            
        if item.is_submenu and item.submenu and not item.submenu.isVisible():
            self.active_submenu = item.submenu # type: ignore
            pos = item.mapToGlobal(item.rect().topRight())
            pos.setX(pos.x() - 10)
            pos.setY(pos.y() - 15)
            item.submenu.show_menu(pos)

    def show_menu(self, pos):
        self.container.adjustSize() # type: ignore
        ideal_width = self.container.width() + 40 # type: ignore
        ideal_height = self.container.height() + 40 # type: ignore
        
        screen = QApplication.primaryScreen().geometry() # type: ignore
        max_height = min(ideal_height, screen.height() - 150, 700)
        
        if ideal_height > max_height:
            ideal_width += 15
            
        ideal_width = max(220, ideal_width)
        
        target_rect = QRect(pos.x(), pos.y(), ideal_width, max_height)
        
        self.setGeometry(target_rect) # type: ignore
        self.setWindowOpacity(1.0) # type: ignore
        
        if not self.is_sub: # type: ignore
            start_rect = QRect(pos.x(), pos.y() - 10, ideal_width, max_height)
            self.setGeometry(start_rect) # type: ignore
            self.setWindowOpacity(0.0) # type: ignore
            self.anim_opacity.setStartValue(0.0) # type: ignore
            self.anim_opacity.setEndValue(1.0) # type: ignore
            self.anim_geom.setStartValue(start_rect) # type: ignore
            self.anim_geom.setEndValue(target_rect) # type: ignore
            self.anim_opacity.start() # type: ignore
            self.anim_geom.start() # type: ignore

        self.show() # type: ignore

    def close_all(self):
        if self.parent_menu: # type: ignore
            self.parent_menu.close_all() # type: ignore
        else:
            self.close() # type: ignore

    def hideEvent(self, event):
        if self.active_submenu: # type: ignore
            self.active_submenu.close() # type: ignore
            self.active_submenu = None # type: ignore
        super().hideEvent(event) # type: ignore

    def focusOutEvent(self, event):
        pass
