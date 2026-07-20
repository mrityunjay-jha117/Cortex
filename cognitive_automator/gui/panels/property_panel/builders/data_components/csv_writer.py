"""
=============================================================================
 CSV_WRITER.PY (data_components)
=============================================================================
This module is a microservice component for data_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QCheckBox
from cognitive_automator.graph_model import CSVWriterNode

class CSVWriterMixin:
    def _build_csv_writer(self, node: CSVWriterNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v))) # type: ignore
        self._form_layout.addRow("Data Source Key", self._line_edit(node.data_source_key, lambda v: self._set(node, "data_source_key", v))) # type: ignore
        
        append_cb = QCheckBox()
        append_cb.setChecked(node.append)
        append_cb.toggled.connect(lambda v: self._set(node, "append", v)) # type: ignore
        self._form_layout.addRow("Append Mode", append_cb) # type: ignore
        
        self._form_layout.addRow("Status Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        self._add_hint("Writes context data (dict or list[dict]) to CSV.") # type: ignore
