"""
=============================================================================
 EXECUTION.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import logging
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QThread
from cortex.runtime.executor import ExecutionConfig, ExecutionEvent, ExecutionStatus
from .worker import ExecutionWorker

log = logging.getLogger(__name__)

class ExecutionMixin:
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
