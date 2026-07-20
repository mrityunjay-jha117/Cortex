"""
=============================================================================
 MAIN WINDOW
=============================================================================
This module defines the primary application window shell.
It manages menus, toolbars, docking panels, and the central canvas view.

Key Features:
1. Orchestrates the layout of the Property Panel, Log Panel, and Canvas.
2. Handles global actions like Save, Load, and Run Flow.

Think of this module as the dashboard housing all the controls and screens.
=============================================================================
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from cognitive_automator.graph_model import ActionGraph
from cognitive_automator.serializer import new_graph
from cognitive_automator import __version__
from cognitive_automator.gui.constants import MAIN_STYLESHEET

from .main_window_components import UIBuilderMixin, FileActionsMixin, ExecutionMixin, NodesMixin, ExecutionWorker

log = logging.getLogger(__name__)

class MainWindow(UIBuilderMixin, FileActionsMixin, ExecutionMixin, NodesMixin, QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._graph: ActionGraph = new_graph("Untitled Automation")
        self._current_file: Path | None = None
        self._modified = False
        self._worker: ExecutionWorker | None = None
        self._exec_thread: QThread | None = None

        self.setWindowTitle(f"Cognitive Automator {__version__}")
        self.resize(1400, 900)
        self.showMaximized()
        self.setStyleSheet(MAIN_STYLESHEET)

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()
        self._refresh_canvas()
        self._update_title()

    def closeEvent(self, event: Any) -> None:
        if self._modified:
            if not self._confirm_discard():
                event.ignore()
                return
        if self._exec_thread and self._exec_thread.isRunning():
            if self._worker:
                self._worker.abort()
            self._exec_thread.quit()
            self._exec_thread.wait(2000)
        event.accept()
