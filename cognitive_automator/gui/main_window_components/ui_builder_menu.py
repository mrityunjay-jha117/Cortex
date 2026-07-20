"""
=============================================================================
 UI_BUILDER_MENU.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QToolBar

class UIBuilderMenuMixin:
    def _build_menu(self) -> None:
        mb = self.menuBar() # type: ignore

        file_menu = mb.addMenu("&File")
        self._act_new = QAction("&New Automation", self) # type: ignore
        self._act_new.setShortcut(QKeySequence.StandardKey.New)
        file_menu.addAction(self._act_new)

        self._act_open = QAction("&Open…", self) # type: ignore
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(self._act_open)

        self._act_save = QAction("&Save", self) # type: ignore
        self._act_save.setShortcut(QKeySequence.StandardKey.Save)
        file_menu.addAction(self._act_save)

        self._act_save_as = QAction("Save &As…", self) # type: ignore
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        file_menu.addAction(self._act_save_as)

        file_menu.addSeparator()
        self._act_quit = QAction("&Quit", self) # type: ignore
        self._act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        file_menu.addAction(self._act_quit)

        run_menu = mb.addMenu("&Run")
        self._act_run = QAction("  Play", self) # type: ignore
        self._act_run.setShortcut(QKeySequence("F5"))
        run_menu.addAction(self._act_run)

        self._act_step = QAction("Step Mode", self, checkable=True) # type: ignore
        run_menu.addAction(self._act_step)

        self._act_pause = QAction("  Pause", self) # type: ignore
        self._act_pause.setEnabled(False)
        run_menu.addAction(self._act_pause)

        self._act_stop = QAction("  Stop", self) # type: ignore
        self._act_stop.setShortcut(QKeySequence("F6"))
        self._act_stop.setEnabled(False)
        run_menu.addAction(self._act_stop)

        help_menu = mb.addMenu("&Help")
        help_menu.addAction("About").triggered.connect(self._show_about) # type: ignore

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb) # type: ignore

        tb.addAction(self._act_new)
        tb.addAction(self._act_open)
        tb.addAction(self._act_save)
        tb.addSeparator()
        tb.addAction(self._act_run)
        tb.addAction(self._act_pause)
        tb.addAction(self._act_stop)
        tb.addSeparator()

    def _connect_signals(self) -> None:
        self._act_new.triggered.connect(self._new_graph) # type: ignore
        self._act_open.triggered.connect(self._open_graph) # type: ignore
        self._act_save.triggered.connect(self._save_graph) # type: ignore
        self._act_save_as.triggered.connect(self._save_graph_as) # type: ignore
        self._act_quit.triggered.connect(self.close) # type: ignore
        self._act_run.triggered.connect(self._run_graph) # type: ignore
        self._act_pause.triggered.connect(self._pause_graph) # type: ignore
        self._act_stop.triggered.connect(self._stop_graph) # type: ignore

        self._scene.node_selected.connect(self._on_node_selected) # type: ignore
        self._scene.node_double_clicked.connect(self._on_node_double_clicked) # type: ignore
        self._scene.graph_modified.connect(self._mark_modified) # type: ignore
        self._prop_panel.node_changed.connect(self._on_node_changed) # type: ignore
