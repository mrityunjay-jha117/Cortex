"""
gui/widgets/logic_inject_dialog.py — Dialog to inject an LLM logic node mid-recording.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget,
)

from cognitive_automator.graph_model import (
    LLMJudgmentNode, LLMExtractionNode, LLMGenerativeNode,
)
from cognitive_automator.gui.constants import MAIN_STYLESHEET


class LogicInjectDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Inject Logic Node")
        self.setMinimumWidth(440)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._node = None

        layout = QVBoxLayout(self)

        title = QLabel("Add LLM Logic Node")
        title.setStyleSheet("font-size:14px; font-weight:bold; padding-bottom:8px;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["LLM Judgment (True/False)", "LLM Extraction (JSON)", "LLM Generative (Text)"])
        form.addRow("Node Type", self._type_combo)

        self._label_edit = QLineEdit("My Logic Node")
        form.addRow("Label", self._label_edit)

        self._model_edit = QLineEdit("gpt-4o")
        form.addRow("Model", self._model_edit)

        self._prompt_edit = QPlainTextEdit()
        self._prompt_edit.setPlaceholderText(
            "e.g. Analyze {{clipboard}}. Is this related to stock prices? Reply YES or NO."
        )
        self._prompt_edit.setMinimumHeight(100)
        form.addRow("Prompt Template", self._prompt_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_node(self):  # type: ignore[return]
        node_type = self._type_combo.currentText()
        label = self._label_edit.text() or "Logic Node"
        model = self._model_edit.text() or "gpt-4o"
        prompt = self._prompt_edit.toPlainText()

        if "Judgment" in node_type:
            return LLMJudgmentNode(label=label, model=model, prompt_template=prompt)
        if "Extraction" in node_type:
            return LLMExtractionNode(label=label, model=model, prompt_template=prompt)
        if "Generative" in node_type:
            return LLMGenerativeNode(label=label, model=model, prompt_template=prompt)
        return None
