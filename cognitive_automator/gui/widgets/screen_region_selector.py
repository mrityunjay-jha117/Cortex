"""
=============================================================================
 SCREEN REGION SELECTOR
=============================================================================
This module implements a full-screen overlay for selecting coordinates.
It allows users to draw a box on their actual screen to define visual targets.

Key Features:
1. Captures the current screen state and draws it on a borderless window.
2. Calculates exact X/Y coordinates and dimensions based on user drag actions.

Think of this module as the digital snipping tool for automation targeting.
=============================================================================
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPaintEvent, QMouseEvent, QKeyEvent,
)
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

_HANDLE_SIZE = 10
_HALF = _HANDLE_SIZE // 2

# Cursor for each of the 8 handles (TL, T, TR, R, BR, B, BL, L)
_HANDLE_CURSORS = [
    Qt.CursorShape.SizeFDiagCursor,
    Qt.CursorShape.SizeVerCursor,
    Qt.CursorShape.SizeBDiagCursor,
    Qt.CursorShape.SizeHorCursor,
    Qt.CursorShape.SizeFDiagCursor,
    Qt.CursorShape.SizeVerCursor,
    Qt.CursorShape.SizeBDiagCursor,
    Qt.CursorShape.SizeHorCursor,
]

class ScreenRegionSelector(QWidget):
    """Full-screen overlay with a draggable, resizable dotted selection box."""

    region_selected = pyqtSignal(object, object)   # QRect, QPoint (normalized, logical px)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Default selection: centred 300×200 box
        w, h = self.width() or 1280, self.height() or 800
        cx, cy = w // 2, h // 2
        self._rect = QRect(cx - 150, cy - 100, 300, 200)
        self._click_point: QPoint | None = None

        self._drag_start: QPoint | None = None
        self._rect_at_drag: QRect | None = None
        self._active_handle: int | None = None
        self._dragging_body = False

        # Dimension label
        self._dim_lbl = QLabel(self)
        self._dim_lbl.setStyleSheet(
            "color:white; background:rgba(0,0,0,160);"
            "padding:3px 8px; border-radius:4px; font-size:12px; font-family:Consolas;"
        )

        # Buttons
        self._btn_capture = QPushButton("  Capture  [Enter]", self)
        self._btn_capture.setStyleSheet(
            "background:#00C9A7; color:#0D0E18; border:none;"
            "border-radius:6px; padding:8px 18px; font-weight:bold; font-size:13px;"
        )
        self._btn_capture.clicked.connect(self._confirm)

        self._btn_cancel = QPushButton("  Cancel  [Esc]", self)
        self._btn_cancel.setStyleSheet(
            "background:#FF6B6B; color:white; border:none;"
            "border-radius:6px; padding:8px 18px; font-size:13px;"
        )
        self._btn_cancel.clicked.connect(self._cancel)

        self._refresh_controls()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _refresh_controls(self) -> None:
        r = self._rect.normalized()
        self._dim_lbl.setText(f"{r.width()} × {r.height()}")
        self._dim_lbl.adjustSize()

        lbl_x = r.left()
        lbl_y = r.bottom() + 8
        # Flip above rect if too close to bottom
        if lbl_y + 80 > self.height():
            lbl_y = max(r.top() - 80, 4)
        self._dim_lbl.move(lbl_x, lbl_y)

        self._btn_capture.adjustSize()
        self._btn_cancel.adjustSize()
        btn_y = lbl_y + self._dim_lbl.height() + 6
        self._btn_capture.move(lbl_x, btn_y)
        self._btn_cancel.move(lbl_x + self._btn_capture.width() + 8, btn_y)

    # ------------------------------------------------------------------
    # Handle geometry
    # ------------------------------------------------------------------

    def _handle_rects(self) -> list[QRect]:
        r = self._rect.normalized()
        cx = r.left() + r.width() // 2
        cy = r.top() + r.height() // 2
        s, h = _HANDLE_SIZE, _HALF
        return [
            QRect(r.left() - h,  r.top() - h,    s, s),  # 0 TL
            QRect(cx - h,        r.top() - h,    s, s),  # 1 T
            QRect(r.right() - h, r.top() - h,    s, s),  # 2 TR
            QRect(r.right() - h, cy - h,          s, s),  # 3 R
            QRect(r.right() - h, r.bottom() - h,  s, s),  # 4 BR
            QRect(cx - h,        r.bottom() - h,  s, s),  # 5 B
            QRect(r.left() - h,  r.bottom() - h,  s, s),  # 6 BL
            QRect(r.left() - h,  cy - h,          s, s),  # 7 L
        ]

    def _hit_handle(self, pos: QPoint) -> int | None:
        for i, hr in enumerate(self._handle_rects()):
            if hr.contains(pos):
                return i
        return None

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, _event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark vignette outside selection
        p.fillRect(self.rect(), QColor(0, 0, 0, 130))

        # Punch out the selection area to show real screen behind
        r = self._rect.normalized()
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.fillRect(r, QColor(0, 0, 0, 0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Dotted border
        pen = QPen(QColor(255, 255, 255, 220), 2, Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([6.0, 4.0])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r)

        # Resize handles
        p.setPen(QPen(QColor(255, 255, 255, 200), 1))
        p.setBrush(QBrush(QColor("#7B61FF")))
        for hr in self._handle_rects():
            p.drawRect(hr)

        # Click point crosshair (Red)
        if self._click_point and r.contains(self._click_point):
            p.setPen(QPen(QColor("#FF4C4C"), 2))
            cp = self._click_point
            p.drawLine(cp.x() - 8, cp.y(), cp.x() + 8, cp.y())
            p.drawLine(cp.x(), cp.y() - 8, cp.x(), cp.y() + 8)
            p.drawEllipse(cp, 4, 4)

        p.end()

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        
        # Right-click to set click target point
        if event.button() == Qt.MouseButton.RightButton:
            if self._rect.normalized().contains(pos):
                self._click_point = pos
                self.update()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        h = self._hit_handle(pos)
        if h is not None:
            self._active_handle = h
            self._drag_start = pos
            self._rect_at_drag = QRect(self._rect)
        elif self._rect.normalized().contains(pos):
            self._dragging_body = True
            self._drag_start = pos
            self._rect_at_drag = QRect(self._rect)
        else:
            # Draw a new rectangle from scratch
            self._rect = QRect(pos, pos)
            self._drag_start = pos
            self._rect_at_drag = QRect(self._rect)
            self._active_handle = 4   # treat as BR drag so user draws outward
            self._click_point = None  # reset click point on new rect

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        buttons = event.buttons()

        if buttons & Qt.MouseButton.LeftButton:
            if self._active_handle is not None and self._drag_start is not None:
                self._apply_handle(self._active_handle, pos)
            elif self._dragging_body and self._drag_start is not None:
                delta = pos - self._drag_start
                self._rect = self._rect_at_drag.translated(delta)  # type: ignore[operator]
        else:
            # Hover cursor
            h = self._hit_handle(pos)
            if h is not None:
                self.setCursor(_HANDLE_CURSORS[h])
            elif self._rect.normalized().contains(pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
            return

        self._refresh_controls()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._active_handle = None
        self._dragging_body = False
        self._drag_start = None
        self._rect_at_drag = None

    def _apply_handle(self, handle: int, pos: QPoint) -> None:
        r = QRect(self._rect_at_drag)  # type: ignore[arg-type]
        if handle == 0:
            r.setTopLeft(pos)
        elif handle == 1:
            r.setTop(pos.y())
        elif handle == 2:
            r.setTopRight(pos)
        elif handle == 3:
            r.setRight(pos.x())
        elif handle == 4:
            r.setBottomRight(pos)
        elif handle == 5:
            r.setBottom(pos.y())
        elif handle == 6:
            r.setBottomLeft(pos)
        elif handle == 7:
            r.setLeft(pos.x())
        self._rect = r

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm()
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _confirm(self) -> None:
        r = self._rect.normalized()
        cp = self._click_point
        self.hide()
        self.region_selected.emit(r, cp)
        self.close()

    def _cancel(self) -> None:
        self.hide()
        self.cancelled.emit()
        self.close()
