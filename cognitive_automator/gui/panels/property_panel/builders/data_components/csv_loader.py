"""
=============================================================================
 CSV_LOADER.PY (data_components)
=============================================================================
This module is a microservice component for data_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QFileDialog, QWidget
from cognitive_automator.graph_model import CSVDataLoaderNode

class CSVLoaderMixin:
    def _build_csv_data_loader(self, node: CSVDataLoaderNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v))) # type: ignore
        
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0,0,0,0)
        
        browse_btn = QPushButton("Browse...")
        def on_browse() -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)") # type: ignore
            if path:
                self._set(node, "file_path", path) # type: ignore
                self._rebuild_form(node) # type: ignore
        browse_btn.clicked.connect(on_browse)
        btn_layout.addWidget(browse_btn)
        self._form_layout.addRow("", btn_row) # type: ignore
        
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        self._add_hint("Loads CSV as a list of dicts. Connect this to a For Loop.") # type: ignore
