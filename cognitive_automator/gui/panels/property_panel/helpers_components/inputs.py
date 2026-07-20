"""
=============================================================================
 INPUTS.PY (helpers_components)
=============================================================================
This module is a microservice component for helpers_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit, QSlider, QSpinBox, QWidget, QPushButton
)

class InputHelpers:
    def _line_edit(self, value: str, setter: Any, drop_handler: Any | None = None) -> QLineEdit:
        class DropLineEdit(QLineEdit):
            def __init__(self, contents: str, parent: QWidget | None = None) -> None:
                super().__init__(contents, parent)
                self.setAcceptDrops(True)
            
            def dragEnterEvent(self, event: Any) -> None:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
            
            def dropEvent(self, event: Any) -> None:
                urls = event.mimeData().urls()
                if urls:
                    file_path = urls[0].toLocalFile()
                    self.setText(file_path)
                    if drop_handler:
                        drop_handler(file_path)

        w = DropLineEdit(value)
        w.textChanged.connect(lambda v: getattr(self, "_safe_set")(setter, v))
        return w

    def _plain_text(self, value: str, setter: Any) -> QPlainTextEdit:
        w = QPlainTextEdit(value)
        w.setTabChangesFocus(True)
        w.textChanged.connect(lambda: getattr(self, "_safe_set")(setter, w.toPlainText()))
        return w

    def _spin(self, value: int, min_v: int, max_v: int, setter: Any) -> QSpinBox:
        w = QSpinBox()
        w.setRange(min_v, max_v)
        w.setValue(value)
        w.valueChanged.connect(lambda v: getattr(self, "_safe_set")(setter, v))
        return w

    def _dspin(self, value: float, min_v: float, max_v: float,
               setter: Any, step: float = 0.1) -> QDoubleSpinBox:
        w = QDoubleSpinBox()
        w.setRange(min_v, max_v)
        w.setSingleStep(step)
        w.setDecimals(2)
        w.setValue(value)
        w.valueChanged.connect(lambda v: getattr(self, "_safe_set")(setter, v))
        return w

    def _combo(self, options: list[str], current: str, setter: Any) -> QComboBox:
        w = QComboBox()
        w.addItems(options)
        if current in options:
            w.setCurrentText(current)
        w.currentTextChanged.connect(lambda v: getattr(self, "_safe_set")(setter, v))
        return w

    def _slider(self, value: int, min_v: int, max_v: int, setter: Any) -> QSlider:
        w = QSlider(Qt.Orientation.Horizontal)
        w.setRange(min_v, max_v)
        w.setValue(value)
        w.valueChanged.connect(lambda v: getattr(self, "_safe_set")(setter, v))
        return w

    def _toggle(self, value: bool, setter: Any) -> QPushButton:
        btn = QPushButton("ON" if value else "OFF")
        btn.setCheckable(True)
        btn.setChecked(value)
        
        def on_toggle(checked: bool) -> None:
            btn.setText("ON" if checked else "OFF")
            getattr(self, "_safe_set")(setter, checked)
            
        btn.toggled.connect(on_toggle)
        return btn
