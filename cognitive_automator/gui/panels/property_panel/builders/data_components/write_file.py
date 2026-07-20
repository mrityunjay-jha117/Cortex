"""
=============================================================================
 WRITE_FILE.PY (data_components)
=============================================================================
This module is a microservice component for data_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QCheckBox
from cognitive_automator.graph_model import WriteFileNode

class WriteFileMixin:
    def _build_write_file(self, node: WriteFileNode) -> None:
        self._form_layout.addRow("File Path", self._line_edit(node.file_path, lambda v: self._set(node, "file_path", v))) # type: ignore
        
        content_edit = self._plain_text(node.content_template, lambda v: self._set(node, "content_template", v)) # type: ignore
        content_edit.setMinimumHeight(60)
        self._form_layout.addRow("Content", content_edit) # type: ignore
        
        append_cb = QCheckBox()
        append_cb.setChecked(node.append)
        append_cb.toggled.connect(lambda v: self._set(node, "append", v)) # type: ignore
        self._form_layout.addRow("Append", append_cb) # type: ignore
        
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        self._add_hint("Writes text to a file. Supports {template} variables in the content.") # type: ignore
