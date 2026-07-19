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

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog, QInputDialog, QMainWindow,
    QMessageBox, QSplitter, QStatusBar, QToolBar, QVBoxLayout, QWidget,
    QPushButton, QGridLayout,
)

from cognitive_automator.graph_model import (
    ActionGraph, BranchNode, ClipboardNode, CompareNode, DynamicIterateNode,
    IterateNode, KeyboardNode, LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode,
    LocateElementNode, GenerativeOCRNode, MouseNode, WaitNode, SubGraphNode, NavigatorNode,
)
from cognitive_automator.gui.canvas import GraphScene, GraphView
from cognitive_automator.gui.constants import MAIN_STYLESHEET
from cognitive_automator.gui.panels.property_panel import PropertyPanel
from cognitive_automator.gui.panels.log_panel import LogPanel
from cognitive_automator.runtime.executor import (
    ExecutionConfig, ExecutionEvent, ExecutionStatus, GraphExecutor,
)
from cognitive_automator.serializer import load_graph, new_graph, save_graph
from cognitive_automator import __version__

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Background execution worker
# ---------------------------------------------------------------------------

class ExecutionWorker(QObject):
    event_received = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, graph: ActionGraph, config: ExecutionConfig) -> None:
        super().__init__()
        self._graph = graph
        self._config = config
        self._executor: GraphExecutor | None = None

    def run(self) -> None:
        self._executor = GraphExecutor(
            self._graph, self._config, on_event=self._on_event
        )
        self._executor.run()
        self.finished.emit()

    def _on_event(self, event: ExecutionEvent) -> None:
        self.event_received.emit(event)

    def abort(self) -> None:
        if self._executor:
            self._executor.abort()

    def pause(self) -> None:
        if self._executor:
            self._executor.pause()

    def resume(self) -> None:
        if self._executor:
            self._executor.resume()

# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._graph: ActionGraph = new_graph("Untitled Automation")
        self._current_file: Path | None = None
        self._modified = False
        self._worker: ExecutionWorker | None = None
        self._exec_thread: QThread | None = None

        self.setWindowTitle(f"Cognitive Automator {__version__}")
        self.resize(1400, 900)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()
        self._refresh_canvas()
        self._update_title()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Horizontal splitter: canvas | properties
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Canvas container for overlays
        canvas_container = QWidget()
        canvas_grid = QGridLayout(canvas_container)
        canvas_grid.setContentsMargins(0, 0, 0, 0)

        self._scene = GraphScene()
        self._view = GraphView(self._scene)
        canvas_grid.addWidget(self._view, 0, 0)

        # Overlay button
        self._ai_toggle_btn = QPushButton(" AI Fallback: OFF", canvas_container)
        self._ai_toggle_btn.setCheckable(True)
        self._ai_toggle_btn.setFixedWidth(200)
        self._ai_toggle_btn.setStyleSheet("""
            QPushButton {
                background: #F7C76B;
                color: #000000;
                border: 2px solid #000000;
                border-right: 4px solid #000000;
                border-bottom: 4px solid #000000;
                border-radius: 0px;
                padding: 8px;
                font-family: "Courier New";
                font-weight: bold;
                margin-top: 15px;
                margin-right: 15px;
            }
            QPushButton:hover {
                background: #FDE49E;
                color: #000000;
            }
            QPushButton:pressed {
                background: #E0AD4C;
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-right: 2px solid #000000;
                border-bottom: 2px solid #000000;
                padding-top: 10px;
                padding-left: 10px;
                padding-bottom: 6px;
                padding-right: 6px;
            }
            QPushButton:checked {
                background: #E0AD4C;
                color: #000000;
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-right: 2px solid #000000;
                border-bottom: 2px solid #000000;
                padding-top: 10px;
                padding-left: 10px;
                padding-bottom: 6px;
                padding-right: 6px;
            }
        """)
        self._ai_toggle_btn.clicked.connect(self._toggle_global_ai_fallback)
        canvas_grid.addWidget(self._ai_toggle_btn, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        h_splitter.addWidget(canvas_container)

        # Property panel
        self._prop_panel = PropertyPanel()
        self._prop_panel.setObjectName("propPanel")
        h_splitter.addWidget(self._prop_panel)
        h_splitter.setSizes([1050, 300])

        # Vertical splitter: canvas area | log
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(h_splitter)

        self._log_panel = LogPanel()
        v_splitter.addWidget(self._log_panel)
        v_splitter.setSizes([680, 180])

        root_layout.addWidget(v_splitter)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _build_menu(self) -> None:
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._act_new = QAction("&New Automation", self)
        self._act_new.setShortcut(QKeySequence.StandardKey.New)
        file_menu.addAction(self._act_new)

        self._act_open = QAction("&Open…", self)
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(self._act_open)

        self._act_save = QAction("&Save", self)
        self._act_save.setShortcut(QKeySequence.StandardKey.Save)
        file_menu.addAction(self._act_save)

        self._act_save_as = QAction("Save &As…", self)
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        file_menu.addAction(self._act_save_as)

        file_menu.addSeparator()
        self._act_quit = QAction("&Quit", self)
        self._act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        file_menu.addAction(self._act_quit)

        # Edit — add node types
        edit_menu = mb.addMenu("&Edit")
        add_node_menu = edit_menu.addMenu("Add Node")

        physical_menu = add_node_menu.addMenu("Physical IO")
        physical_menu.addAction("Mouse Node").triggered.connect(lambda: self._add_node(MouseNode(label="Mouse Click")))
        physical_menu.addAction("Keyboard Node").triggered.connect(lambda: self._add_node(KeyboardNode(label="Type Text")))
        physical_menu.addAction("Navigator Node").triggered.connect(lambda: self._add_node(NavigatorNode(label="Focus & Scroll")))
        physical_menu.addAction("Clipboard Node").triggered.connect(lambda: self._add_node(ClipboardNode(label="Read Clipboard")))
        vision_menu = add_node_menu.addMenu("Vision")
        vision_menu.addAction("Locate Element").triggered.connect(lambda: self._add_node(LocateElementNode(label="Find Element")))
        vision_menu.addAction("Generative OCR").triggered.connect(lambda: self._add_node(GenerativeOCRNode(label="OCR Screen")))

        llm_menu = add_node_menu.addMenu("LLM Logic")
        llm_menu.addAction("LLM Judgment").triggered.connect(lambda: self._add_node(LLMJudgmentNode(label="Classify")))
        llm_menu.addAction("LLM Extraction").triggered.connect(lambda: self._add_node(LLMExtractionNode(label="Extract JSON")))
        llm_menu.addAction("LLM Generative").triggered.connect(lambda: self._add_node(LLMGenerativeNode(label="Generate Text")))

        flow_menu = add_node_menu.addMenu("Flow Control")
        flow_menu.addAction("Wait / Delay").triggered.connect(lambda: self._add_node(WaitNode(label="Wait")))
        flow_menu.addAction("Branch").triggered.connect(lambda: self._add_node(BranchNode(label="Branch")))
        flow_menu.addAction("Compare / Logic").triggered.connect(lambda: self._add_node(CompareNode(label="Compare")))
        flow_menu.addAction("Iterate (Loop)").triggered.connect(lambda: self._add_node(IterateNode(label="For Each")))
        flow_menu.addAction("Dynamic Iterate").triggered.connect(lambda: self._add_node(DynamicIterateNode(label="For Each (Dynamic)")))
        flow_menu.addAction("Sub-Graph").triggered.connect(lambda: self._add_node(SubGraphNode(label="Sub-Graph")))

        # Run
        run_menu = mb.addMenu("&Run")
        self._act_run = QAction("  Play", self)
        self._act_run.setShortcut(QKeySequence("F5"))
        run_menu.addAction(self._act_run)

        self._act_step = QAction("Step Mode", self, checkable=True)
        run_menu.addAction(self._act_step)

        self._act_pause = QAction("  Pause", self)
        self._act_pause.setEnabled(False)
        run_menu.addAction(self._act_pause)

        self._act_stop = QAction("  Stop", self)
        self._act_stop.setShortcut(QKeySequence("F6"))
        self._act_stop.setEnabled(False)
        run_menu.addAction(self._act_stop)

        # Help
        help_menu = mb.addMenu("&Help")
        help_menu.addAction("About").triggered.connect(self._show_about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addAction(self._act_new)
        tb.addAction(self._act_open)
        tb.addAction(self._act_save)
        tb.addSeparator()
        tb.addAction(self._act_run)
        tb.addAction(self._act_pause)
        tb.addAction(self._act_stop)
        tb.addSeparator()

    def _connect_signals(self) -> None:
        self._act_new.triggered.connect(self._new_graph)
        self._act_open.triggered.connect(self._open_graph)
        self._act_save.triggered.connect(self._save_graph)
        self._act_save_as.triggered.connect(self._save_graph_as)
        self._act_quit.triggered.connect(self.close)
        self._act_run.triggered.connect(self._run_graph)
        self._act_pause.triggered.connect(self._pause_graph)
        self._act_stop.triggered.connect(self._stop_graph)

        self._scene.node_selected.connect(self._on_node_selected)
        self._scene.node_double_clicked.connect(self._on_node_double_clicked)
        self._scene.graph_modified.connect(self._mark_modified)
        self._prop_panel.node_changed.connect(self._on_node_changed)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _new_graph(self) -> None:
        if self._modified:
            if not self._confirm_discard():
                return
        name, ok = QInputDialog.getText(self, "New Automation", "Automation name:")
        if ok and name:
            self._graph = new_graph(name)
            self._current_file = None
            self._modified = False
            self._refresh_canvas()
            self._update_title()

    def _open_graph(self) -> None:
        if self._modified and not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Automation", "",
            "Cognitive Automator (*.cogauto);;YAML (*.yaml *.yml);;JSON (*.json);;All Files (*)"
        )
        if path:
            try:
                self._graph = load_graph(path)
                self._current_file = Path(path)
                self._modified = False
                self._refresh_canvas()
                self._update_title()
                self._status.showMessage(f"Opened: {path}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Could not open file:\n{exc}")

    def _save_graph(self) -> None:
        if self._current_file is None:
            self._save_graph_as()
        else:
            self._do_save(self._current_file)

    def _save_graph_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Automation", self._graph.metadata.name,
            "Cognitive Automator (*.cogauto);;YAML (*.yaml);;JSON (*.json)"
        )
        if path:
            if not any(path.endswith(ext) for ext in (".cogauto", ".yaml", ".yml", ".json")):
                path += ".cogauto"
            self._do_save(Path(path))

    def _do_save(self, path: Path) -> None:
        try:
            save_graph(self._graph, path)
            self._current_file = path
            self._modified = False
            self._update_title()
            self._status.showMessage(f"Saved: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    def _confirm_discard(self) -> bool:
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Continue and discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def _add_node(self, node: Any) -> None:
        # Place at centre of view
        centre = self._view.mapToScene(
            self._view.viewport().rect().center()
        )
        node.x = centre.x()
        node.y = centre.y()
        self._graph.add_node(node)
        self._refresh_canvas()
        self._mark_modified()

    def _on_node_selected(self, node_id: str) -> None:
        node = self._graph.nodes.get(node_id)
        if node:
            self._prop_panel.show_node(node)

    def _on_node_double_clicked(self, node_id: str) -> None:
        node = self._graph.nodes.get(node_id)
        if node:
            self._prop_panel.show_node(node)

    def _on_node_changed(self, node_id: str) -> None:
        self._mark_modified()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _run_graph(self) -> None:
        if not self._graph.nodes:
            QMessageBox.information(self, "Empty Graph", "Add some nodes first.")
            return
        if self._exec_thread and self._exec_thread.isRunning():
            return

        self._scene.reset_all_states()
        self._log_panel.clear_log()
        self._act_run.setEnabled(False)
        self._act_stop.setEnabled(True)
        self._act_pause.setEnabled(True)

        config = ExecutionConfig(step_mode=self._act_step.isChecked())
        self._worker = ExecutionWorker(self._graph, config)
        self._exec_thread = QThread()
        self._worker.moveToThread(self._exec_thread)

        self._exec_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._exec_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._exec_thread.finished.connect(self._exec_thread.deleteLater)
        self._exec_thread.finished.connect(self._on_thread_finished)
        self._worker.finished.connect(self._on_execution_finished)
        self._worker.event_received.connect(self._on_execution_event)

        self._exec_thread.start()

    def _pause_graph(self) -> None:
        if self._worker:
            if self._act_pause.text().startswith(""):
                self._worker.pause()
                self._act_pause.setText("  Resume")
            else:
                self._worker.resume()
                self._act_pause.setText("  Pause")

    def _stop_graph(self) -> None:
        if self._worker:
            self._worker.abort()

    def _on_execution_event(self, event: ExecutionEvent) -> None:
        self._log_panel.append_event(event)
        if event.status == ExecutionStatus.NODE_ENTER:
            self._scene.set_node_executing(event.node_id)
            self._status.showMessage(f"Executing: {event.node_label or event.node_id}")
            # Auto-scroll canvas to the active node
            item = self._scene.get_node_item(event.node_id)
            if item:
                self._view.centerOn(item)
        elif event.status == ExecutionStatus.NODE_SUCCESS:
            self._scene.set_node_result(event.node_id, True)
        elif event.status == ExecutionStatus.NODE_FAILED:
            self._scene.set_node_result(event.node_id, False)
        elif event.status == ExecutionStatus.NODE_HEALED:
            # If the healed node is currently shown in the property panel, refresh it
            if self._prop_panel._current_node and self._prop_panel._current_node.id == event.node_id:
                # Re-show to update the image preview
                self._prop_panel.show_node(self._prop_panel._current_node)
            self._mark_modified() # Ensure the graph is marked as modified to prompt saving

    def _toggle_global_ai_fallback(self, checked: bool) -> None:
        state_text = "ON" if checked else "OFF"
        self._ai_toggle_btn.setText(f" AI Fallback: {state_text}")
        
        count = 0
        from cognitive_automator.graph_model import LLMProvider
        for node in self._graph.nodes.values():
            if isinstance(node, LocateElementNode):
                node.use_fallback = checked
                node.fallback_provider_override = LLMProvider.OPENROUTER
                count += 1
        
        self._status.showMessage(f"AI Fallback {'enabled' if checked else 'disabled'} for {count} nodes")
        self._mark_modified()
        
        # Refresh property panel if a LocateElementNode is selected
        if self._prop_panel._current_node and isinstance(self._prop_panel._current_node, LocateElementNode):
            self._prop_panel.show_node(self._prop_panel._current_node)

    def _on_execution_finished(self) -> None:
        self._act_run.setEnabled(True)
        self._act_stop.setEnabled(False)
        self._act_pause.setEnabled(False)
        self._act_pause.setText("  Pause")
        self._status.showMessage("Execution complete.")
        
        if self._modified and self._current_file:
            log.info("Auto-saving healed graph to %s", self._current_file)
            self._do_save(self._current_file)

    def _on_thread_finished(self) -> None:
        self._exec_thread = None
        self._worker = None

    # ------------------------------------------------------------------
    # Canvas refresh
    # ------------------------------------------------------------------

    def _refresh_canvas(self) -> None:
        self._scene.load_graph(self._graph)
        self._prop_panel.clear()

    def _mark_modified(self) -> None:
        self._modified = True
        self._update_title()

    def _update_title(self) -> None:
        name = self._graph.metadata.name
        file_part = f" — {self._current_file.name}" if self._current_file else ""
        mod_part = " *" if self._modified else ""
        self.setWindowTitle(f"Cognitive Automator  ·  {name}{file_part}{mod_part}")

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Cognitive Automator",
            f"<b>Cognitive Automator</b> v{__version__}<br><br>"
            "LLM-Powered Windows Automation Framework<br><br>"
            "Combines PyAutoGUI physical automation with<br>"
            "Large Language Model cognitive routing.<br><br>"
            "<i>PyAutoGUI FAILSAFE is always active.<br>"
            "Move mouse to top-left corner to abort.</i>"
        )

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
