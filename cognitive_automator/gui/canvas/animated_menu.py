import PyQt6.QtGui as QtGui
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QGraphicsDropShadowEffect,
    QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QPointF, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath

class AnimatedMenuItem(QWidget):
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
        self.shadow.setColor(QColor(0, 0, 0, 100)) # Black shadow
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)
        
        self.anim_offset = QPropertyAnimation(self.shadow, b"offset")
        self.anim_offset.setDuration(100)
        
        self.anim_blur = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim_blur.setDuration(100)

        self._is_pressed = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._is_pressed:
            bg_color = QColor("#f2f2f2")
            y_offset = 2
            bottom_depth = 0
        elif self.underMouse():
            bg_color = QColor("#ffffff")
            y_offset = -1
            bottom_depth = 3
        else:
            bg_color = QColor("#ffffff")
            y_offset = 0
            bottom_depth = 2

        rect = self.rect()
        rect.adjust(2, 2 + y_offset, -2, -2 - (3 - bottom_depth))
        
        # 2.5D bottom edge - grey/black with sharp corners
        path = QPainterPath()
        path.addRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height() + bottom_depth))
        painter.fillPath(path, QColor("#a0a0a0"))
        
        # Top face - White with sharp corners
        path_top = QPainterPath()
        path_top.addRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()))
        painter.fillPath(path_top, bg_color)
        
        # Border
        pen = QtGui.QPen(QColor("#d4d4d4"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path_top)
        
        # Text - Black
        painter.setPen(QColor("#000000"))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        text_rect = QRect(rect.x() + 12, rect.y(), rect.width() - 34, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text)

        if self.is_submenu:
            arrow_rect = QRect(rect.width() - 20, rect.y(), 15, rect.height())
            painter.setPen(QColor("#666666"))
            painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "▶")

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.anim_offset.setEndValue(QPointF(0, 4))
        self.anim_blur.setEndValue(12)
        self.anim_offset.start()
        self.anim_blur.start()
        self.update()
        self.hovered.emit(self)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.anim_offset.setEndValue(QPointF(0, 2))
        self.anim_blur.setEndValue(8)
        self.anim_offset.start()
        self.anim_blur.start()
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_submenu:
            self._is_pressed = True
            self.anim_offset.setEndValue(QPointF(0, 1))
            self.anim_blur.setEndValue(2)
            self.anim_offset.start()
            self.anim_blur.start()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_pressed and not self.is_submenu:
            self._is_pressed = False
            self.anim_offset.setEndValue(QPointF(0, 4) if self.underMouse() else QPointF(0, 2))
            self.anim_blur.setEndValue(12 if self.underMouse() else 8)
            self.anim_offset.start()
            self.anim_blur.start()
            self.update()
            if self.rect().contains(event.pos()):
                self.clicked.emit()


class AnimatedMenu(QWidget):
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
        
        self.layout = QVBoxLayout(self)
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
        self.container_layout.setSpacing(0)  # No vertical space
        
        self.scroll.setWidget(self.container)
        self.bg_layout.addWidget(self.scroll)
        self.layout.addWidget(self.bg_widget)
        
        # Intense black shadow
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

    def add_section(self, title: str):
        lbl = QLabel(title)
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #666666; padding-top: 8px; padding-bottom: 4px; padding-left: 6px;")
        self.container_layout.addWidget(lbl)
        
    def add_action(self, text: str, callback):
        item = AnimatedMenuItem(text, self)
        item.clicked.connect(callback)
        item.clicked.connect(self.close_all)
        item.hovered.connect(self._on_item_hovered)
        self.container_layout.addWidget(item)
        return item
        
    def add_menu(self, text: str):
        item = AnimatedMenuItem(text, self, is_submenu=True)
        item.hovered.connect(self._on_item_hovered)
        
        submenu = AnimatedMenu(self, is_sub=True)
        item.submenu = submenu
        
        self.container_layout.addWidget(item)
        return submenu

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #d0d0d0; margin-top: 6px; margin-bottom: 6px;")
        line.setFixedHeight(1)
        self.container_layout.addWidget(line)

    def _on_item_hovered(self, item):
        if self.active_submenu and self.active_submenu != item.submenu:
            self.active_submenu.close()
            self.active_submenu = None
            
        if item.is_submenu and item.submenu and not item.submenu.isVisible():
            self.active_submenu = item.submenu
            pos = item.mapToGlobal(item.rect().topRight())
            pos.setX(pos.x() - 10)
            pos.setY(pos.y() - 15)
            item.submenu.show_menu(pos)

    def show_menu(self, pos):
        self.container.adjustSize()
        ideal_width = self.container.width() + 40
        ideal_height = self.container.height() + 40
        
        screen = QApplication.primaryScreen().geometry()
        max_height = min(ideal_height, screen.height() - 150, 700)
        
        if ideal_height > max_height:
            ideal_width += 15
            
        ideal_width = max(220, ideal_width)
        
        target_rect = QRect(pos.x(), pos.y(), ideal_width, max_height)
        
        self.setGeometry(target_rect)
        self.setWindowOpacity(1.0)
        
        if not self.is_sub:
            # Only animate main menu to prevent submenus from glitching to blank
            start_rect = QRect(pos.x(), pos.y() - 10, ideal_width, max_height)
            self.setGeometry(start_rect)
            self.setWindowOpacity(0.0)
            self.anim_opacity.setStartValue(0.0)
            self.anim_opacity.setEndValue(1.0)
            self.anim_geom.setStartValue(start_rect)
            self.anim_geom.setEndValue(target_rect)
            self.anim_opacity.start()
            self.anim_geom.start()

        self.show()

    def close_all(self):
        if self.parent_menu:
            self.parent_menu.close_all()
        else:
            self.close()

    def hideEvent(self, event):
        if self.active_submenu:
            self.active_submenu.close()
            self.active_submenu = None
        super().hideEvent(event)

    def focusOutEvent(self, event):
        # We handle closing manually or let Qt handle it for popups
        pass
