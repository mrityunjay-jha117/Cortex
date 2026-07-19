"""
gui/panels/property_panel/builders/llm.py — LLM Node Builders

This file implements UI forms for configuring AI-powered nodes.
It provides inputs for system prompts, AI provider selection (OpenRouter), model names, and fallback mechanisms.
"""
from __future__ import annotations

from typing import Any

import base64
import json

from PyQt6.QtCore import Qt, QByteArray, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QScrollArea,
    QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
    QColorDialog, QFileDialog, QPushButton, QDialog,
)

from cognitive_automator.graph_model import (
    AnyNode, BaseNode, BranchNode, ClipboardNode, ClipboardAction, CompareNode, CompareOp,
    DynamicIterateNode, FileDropNode, ForLoopNode, GenerativeOCRNode, GlobalStartNode, GlobalEndNode,
    IterateNode, KeyboardNode, KeyboardAction,
    LLMExtractionNode, LLMGenerativeNode, LLMJudgmentNode, LocateElementNode, LocateAndClickNode, MouseNode, MouseAction, WaitNode, SubGraphNode, OnErrorAction,
    NavigationAction, NavigatorNode, VisionExtractionNode, WriteFileNode, CSVDataLoaderNode, CSVWriterNode,
    ScreenshotterNode, ScreenshotMode, DetectionMode,
)
from cognitive_automator.gui.constants import (
    APP_SURFACE, APP_BORDER, APP_ACCENT, APP_TEXT_DIM, APP_TEXT, APP_BG,
)



class LlmBuilders:

    def _build_llm(self, node: Any) -> None:
        self._form_layout.addRow("Model", self._line_edit(node.model, lambda v: self._set(node, "model", v)))

        temp_label = QLabel(f"{node.temperature:.2f}")
        temp_label.setStyleSheet(f"color:{APP_ACCENT}; min-width:35px;")
        temp_slider = QSlider(Qt.Orientation.Horizontal)
        temp_slider.setRange(0, 200)
        temp_slider.setValue(int(node.temperature * 100))
        def on_temp(v: int) -> None:
            val = v / 100.0
            self._set(node, "temperature", val)
            temp_label.setText(f"{val:.2f}")
        temp_slider.valueChanged.connect(on_temp)
        temp_row = QWidget()
        temp_row_layout = QHBoxLayout(temp_row)
        temp_row_layout.setContentsMargins(0, 0, 0, 0)
        temp_row_layout.addWidget(temp_slider)
        temp_row_layout.addWidget(temp_label)
        self._form_layout.addRow("Temperature", temp_row)

        self._form_layout.addRow("Max Tokens", self._spin(node.max_tokens, 64, 8192, lambda v: self._set(node, "max_tokens", v)))

        prompt_edit = self._plain_text(node.prompt_template, lambda v: self._set(node, "prompt_template", v))
        prompt_edit.setMinimumHeight(120)
        self._form_layout.addRow("Prompt Template", prompt_edit)
        self._add_hint("Use {{variable}} for context injection")

        sys_prompt_edit = self._plain_text(node.system_prompt, lambda v: self._set(node, "system_prompt", v))
        sys_prompt_edit.setMaximumHeight(80)
        self._form_layout.addRow("System Prompt", sys_prompt_edit)

        # Multi-modal support: image context keys
        if hasattr(node, "image_context_keys"):
            self._form_layout.addRow("Image Context Keys", self._line_edit(
                ", ".join(node.image_context_keys),
                lambda v: self._set(node, "image_context_keys", [k.strip() for k in v.split(",") if k.strip()])
            ))

        if hasattr(node, "output_key"):
            self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v)))
