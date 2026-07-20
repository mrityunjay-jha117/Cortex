"""
=============================================================================
 MENU_BUILD.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QLabel, QFrame
from PyQt6.QtGui import QFont
from .item import AnimatedMenuItem

class AnimatedMenuBuild:
    def add_section(self, title: str):
        lbl = QLabel(title)
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #666666; padding-top: 8px; padding-bottom: 4px; padding-left: 6px;")
        self.container_layout.addWidget(lbl) # type: ignore
        
    def add_action(self, text: str, callback):
        item = AnimatedMenuItem(text, self) # type: ignore
        item.clicked.connect(callback)
        item.clicked.connect(self.close_all) # type: ignore
        item.hovered.connect(self._on_item_hovered) # type: ignore
        self.container_layout.addWidget(item) # type: ignore
        return item
        
    def add_menu(self, text: str):
        item = AnimatedMenuItem(text, self, is_submenu=True) # type: ignore
        item.hovered.connect(self._on_item_hovered) # type: ignore
        
        from .menu import AnimatedMenu # break circular import
        submenu = AnimatedMenu(self, is_sub=True) # type: ignore
        item.submenu = submenu
        
        self.container_layout.addWidget(item) # type: ignore
        return submenu

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #d0d0d0; margin-top: 6px; margin-bottom: 6px;")
        line.setFixedHeight(1)
        self.container_layout.addWidget(line) # type: ignore
