"""
=============================================================================
 FILE_DROP.PY (data_components)
=============================================================================
This module is a microservice component for data_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QFileDialog, QWidget, QLabel
from cortex.graph_model import FileDropNode

class FileDropMixin:
    def _build_file_drop(self, node: FileDropNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v))) # type: ignore
        
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0,0,0,0)
        
        browse_btn = QPushButton("Browse...")
        def on_browse() -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select File") # type: ignore
            if path:
                self._set(node, "file_path", path) # type: ignore
                self._rebuild_form(node) # type: ignore
        browse_btn.clicked.connect(on_browse)
        btn_layout.addWidget(browse_btn)
        self._form_layout.addRow("", btn_row) # type: ignore

        self._form_layout.addRow("X", self._spin(node.x_coord, 0, 9999, lambda v: self._set(node, "x_coord", v))) # type: ignore
        self._form_layout.addRow("Y", self._spin(node.y_coord, 0, 9999, lambda v: self._set(node, "y_coord", v))) # type: ignore
        
        self._add_section("Vision / Offsets") # type: ignore
        self._form_layout.addRow("Vision ID", self._line_edit(node.vision_node_id or "", lambda v: self._set(node, "vision_node_id", v if v else None))) # type: ignore
        
        def on_x_offset(v: int) -> None:
            self._set(node, "x_offset", v) # type: ignore
            x_val_label.setText(str(v))
        x_row = QWidget()
        x_layout = QHBoxLayout(x_row)
        x_layout.setContentsMargins(0,0,0,0)
        x_slider = self._slider(node.x_offset, -2000, 2000, on_x_offset) # type: ignore
        x_val_label = QLabel(str(node.x_offset))
        x_val_label.setFixedWidth(40)
        x_layout.addWidget(x_slider)
        x_layout.addWidget(x_val_label)
        self._form_layout.addRow("X Offset", x_row) # type: ignore

        def on_y_offset(v: int) -> None:
            self._set(node, "y_offset", v) # type: ignore
            y_val_label.setText(str(v))
        y_row = QWidget()
        y_layout = QHBoxLayout(y_row)
        y_layout.setContentsMargins(0,0,0,0)
        y_slider = self._slider(node.y_offset, -2000, 2000, on_y_offset) # type: ignore
        y_val_label = QLabel(str(node.y_offset))
        y_val_label.setFixedWidth(40)
        y_layout.addWidget(y_slider)
        y_layout.addWidget(y_val_label)
        self._form_layout.addRow("Y Offset", y_row) # type: ignore

        self._add_section("Settings") # type: ignore
        self._form_layout.addRow("Wait (s)", self._dspin(node.wait_after_click, 0.1, 10.0, lambda v: self._set(node, "wait_after_click", v))) # type: ignore
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
