"""
=============================================================================
 LOG PANEL
=============================================================================
This module defines the widget that displays runtime logs and output.
It provides a scrolling text area showing execution progress and errors.

Key Features:
1. Captures and renders structured log messages with color coding.
2. Allows users to debug flows by reading real-time feedback.

Think of this module as the application's internal diary and megaphone.
=============================================================================
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from cortex.gui.constants import (
    APP_BG, APP_BORDER, APP_SURFACE, APP_ACCENT,
    APP_SUCCESS, APP_ERROR, APP_WARNING, APP_TEXT_DIM,
)
from cortex.runtime.executor import ExecutionEvent, ExecutionStatus

class LogPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setObjectName("logHeader")
        header.setStyleSheet(f"#logHeader {{ background:#444444; border-top:2px solid {APP_BORDER}; border-bottom:2px solid {APP_BORDER}; }}")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)

        title = QLabel("EXECUTION LOG")
        title.setStyleSheet(f"color:#FFFFFF; font-size:12px; font-weight:bold; letter-spacing:2px; padding:10px")
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_btn)
        layout.addWidget(header)

        # Log text area
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            f"background:#333333; color:#FFFFFF; "
            "font-family:'Consolas','Courier New',monospace; "
            f"font-size:13px; border:none; padding:8px;"
        )
        layout.addWidget(self._log)
        self.setMaximumHeight(220)

    def append_event(self, event: ExecutionEvent) -> None:
        fmt = QTextCharFormat()

        if event.status == ExecutionStatus.NODE_ENTER:
            fmt.setForeground(QColor(APP_ACCENT))
            self._append(f"  {event.node_label or event.node_id}", fmt)
        elif event.status == ExecutionStatus.NODE_SUCCESS:
            fmt.setForeground(QColor(APP_SUCCESS))
            self._append(f"  {event.node_label or event.node_id}", fmt)
        elif event.status == ExecutionStatus.NODE_FAILED:
            fmt.setForeground(QColor(APP_ERROR))
            self._append(f"  {event.node_label or event.node_id} — {event.message}", fmt)
        elif event.status == ExecutionStatus.NODE_INFO:
            fmt.setForeground(QColor("#A0A0A0"))
            self._append(f"  [{event.node_label or event.node_id}] {event.message}", fmt)
        elif event.status == ExecutionStatus.GRAPH_ABORTED:
            fmt.setForeground(QColor(APP_WARNING))
            self._append(f"↻  {event.node_label}  {event.message}", fmt)
        elif event.status == ExecutionStatus.GRAPH_COMPLETE:
            fmt.setForeground(QColor(APP_SUCCESS))
            self._append("═══  GRAPH COMPLETE  ═══", fmt)
        elif event.status == ExecutionStatus.GRAPH_ABORTED:
            fmt.setForeground(QColor(APP_ERROR))
            self._append(f"  ABORTED: {event.message}", fmt)
        elif event.status == ExecutionStatus.STARTED:
            fmt.setForeground(QColor(APP_TEXT_DIM))
            self._append("─── Execution started ───", fmt)

    def append_text(self, text: str, color: str = "#C0C0D0") -> None:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        self._append(text, fmt)

    def clear_log(self) -> None:
        self._log.clear()

    def _append(self, text: str, fmt: QTextCharFormat) -> None:
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()
