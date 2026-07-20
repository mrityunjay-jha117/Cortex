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
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from .screen_region_selector_components import GeometryMixin, PaintMixin, MouseMixin, KeyboardMixin

class ScreenRegionSelector(GeometryMixin, PaintMixin, MouseMixin, KeyboardMixin, QWidget):
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
            "padding:3px 8px; border-radius:4px; font-size:12px; font-family:\"Courier New\";"
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
