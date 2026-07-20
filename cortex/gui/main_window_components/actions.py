"""
=============================================================================
 ACTIONS.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from pathlib import Path
from PyQt6.QtWidgets import QInputDialog, QFileDialog, QMessageBox
from cortex.serializer import load_graph, new_graph, save_graph
from cortex import __version__

class FileActionsMixin:
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
            "Cortex (*.cortex);;YAML (*.yaml *.yml);;JSON (*.json);;All Files (*)"
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
            "Cortex (*.cortex);;YAML (*.yaml);;JSON (*.json)"
        )
        if path:
            if not any(path.endswith(ext) for ext in (".cortex", ".yaml", ".yml", ".json")):
                path += ".cortex"
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

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Cortex",
            f"<b>Cortex</b> v{__version__}<br><br>"
            "LLM-Powered Windows Automation Framework<br><br>"
            "Combines PyAutoGUI physical automation with<br>"
            "Large Language Model cognitive routing.<br><br>"
        )
