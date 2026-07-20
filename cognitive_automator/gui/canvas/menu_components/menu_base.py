"""
=============================================================================
 MENU_BASE.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

class AnimatedMenuBase(QWidget):
    def __init__(self, parent=None, is_sub=False):
        if not is_sub:
            flags = Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        else:
            flags = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        
        super().__init__(parent, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if is_sub:
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.is_sub = is_sub
        self.parent_menu = parent if is_sub else None
        self.active_submenu = None
        
        self.layout = QVBoxLayout(self) # type: ignore
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.bg_widget = QWidget(self)
        self.bg_widget.setObjectName("BgWidget")
        self.bg_widget.setStyleSheet("""
            QWidget#BgWidget {
                background-color: #f7f7f7;
                border-radius: 0px;
                border: 1px solid #c0c0c0;
            }
        """)
        
        self.bg_layout = QVBoxLayout(self.bg_widget)
        self.bg_layout.setContentsMargins(6, 6, 6, 6)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        self.scroll.setWidget(self.container)
        self.bg_layout.addWidget(self.scroll)
        self.layout.addWidget(self.bg_widget) # type: ignore
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(0, 0, 0, 160))
        self.shadow.setOffset(0, 10)
        self.bg_widget.setGraphicsEffect(self.shadow)
        
        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacity.setDuration(150)
        
        self.anim_geom = QPropertyAnimation(self, b"geometry")
        self.anim_geom.setDuration(200)
        self.anim_geom.setEasingCurve(QEasingCurve.Type.OutBack)
