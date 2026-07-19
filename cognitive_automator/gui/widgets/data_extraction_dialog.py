"""
gui/widgets/data_extraction_dialog.py — Data Extraction Dialog

This file defines a popup modal for creating structured JSON schemas.
It allows users to define expected data formats for LLM Extraction nodes using an interactive table instead of writing raw JSON schema.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QPlainTextEdit, QVBoxLayout,
)

from cognitive_automator.graph_model import (
    ClipboardAction, ClipboardNode, LLMExtractionNode, LLMProvider,
)


class DataExtractionDialog(QDialog):
    """Configure a ClipboardRead + LLMExtraction node pair."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configure Data Extraction")
        self.setMinimumWidth(440)
        self._result_nodes: tuple[ClipboardNode, LLMExtractionNode] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        info = QLabel(
            "Reads clipboard text then calls an LLM to extract structured data.\n"
            "The extracted value is stored as a context variable for later nodes.\n"
            "Tip: press Ctrl+C in the app before this node runs so the text is in the clipboard."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px; padding-bottom:4px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        self._prompt_edit = QPlainTextEdit()
        self._prompt_edit.setPlaceholderText(
            "Describe what to extract.\n"
            "Example: Extract the company name, invoice number, and total amount."
        )
        self._prompt_edit.setMinimumHeight(90)
        form.addRow("What to extract:", self._prompt_edit)

        self._output_key_edit = QLineEdit("extracted")
        form.addRow("Output variable:", self._output_key_edit)

        self._model_edit = QLineEdit("openai/gpt-4o")
        form.addRow("LLM Model:", self._model_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        desc = self._prompt_edit.toPlainText().strip()
        if not desc:
            return
        output_key = self._output_key_edit.text().strip() or "extracted"
        model = self._model_edit.text().strip() or "openai/gpt-4o"

        clipboard_node = ClipboardNode(
            label="Read Clipboard",
            action=ClipboardAction.READ,
        )

        short_desc = desc[:50] + ("..." if len(desc) > 50 else "")
        extraction_node = LLMExtractionNode(
            label=f"Extract: {short_desc}",
            prompt_template=(
                "Here is the text from the clipboard:\n\n"
                "{{clipboard}}\n\n"
                f"{desc}"
            ),
            system_prompt="Extract the requested information as valid JSON.",
            output_key=output_key,
            provider=LLMProvider.OPENROUTER,
            model=model,
        )

        self._result_nodes = (clipboard_node, extraction_node)
        self.accept()

    def get_nodes(self) -> tuple[ClipboardNode, LLMExtractionNode] | None:
        """Returns the configured node pair, or None if cancelled."""
        return self._result_nodes
