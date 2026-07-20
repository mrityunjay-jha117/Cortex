"""
=============================================================================
 UI_BUILDER_MAIN.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QGridLayout, QPushButton, QStatusBar
from cognitive_automator.gui.canvas import GraphScene, GraphView
from cognitive_automator.gui.panels.property_panel import PropertyPanel
from cognitive_automator.gui.panels.log_panel import LogPanel

class UIBuilderMainMixin:
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central) # type: ignore
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        canvas_container = QWidget()
        canvas_grid = QGridLayout(canvas_container)
        canvas_grid.setContentsMargins(0, 0, 0, 0)

        self._scene = GraphScene()
        self._view = GraphView(self._scene)
        canvas_grid.addWidget(self._view, 0, 0)

        self._ai_toggle_btn = QPushButton(" AI Fallback: OFF", canvas_container)
        self._ai_toggle_btn.setCheckable(True)
        self._ai_toggle_btn.setFixedWidth(200)
        self._ai_toggle_btn.setStyleSheet("""
            QPushButton {
                background: #F7C76B;
                color: #000000;
                border: 2px solid #000000;
                border-right: 4px solid #000000;
                border-bottom: 4px solid #000000;
                border-radius: 0px;
                padding: 8px;
                font-family: "Courier New";
                font-weight: bold;
                margin-top: 15px;
                margin-right: 15px;
            }
            QPushButton:hover {
                background: #FDE49E;
                color: #000000;
            }
            QPushButton:pressed {
                background: #E0AD4C;
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-right: 2px solid #000000;
                border-bottom: 2px solid #000000;
                padding-top: 10px;
                padding-left: 10px;
                padding-bottom: 6px;
                padding-right: 6px;
            }
            QPushButton:checked {
                background: #E0AD4C;
                color: #000000;
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-right: 2px solid #000000;
                border-bottom: 2px solid #000000;
                padding-top: 10px;
                padding-left: 10px;
                padding-bottom: 6px;
                padding-right: 6px;
            }
        """)
        self._ai_toggle_btn.clicked.connect(self._toggle_global_ai_fallback) # type: ignore
        canvas_grid.addWidget(self._ai_toggle_btn, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        h_splitter.addWidget(canvas_container)

        self._prop_panel = PropertyPanel()
        self._prop_panel.setObjectName("propPanel")
        h_splitter.addWidget(self._prop_panel)
        h_splitter.setSizes([990, 360])

        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(h_splitter)

        self._log_panel = LogPanel()
        v_splitter.addWidget(self._log_panel)
        v_splitter.setSizes([680, 180])

        root_layout.addWidget(v_splitter)

        self._status = QStatusBar()
        self.setStatusBar(self._status) # type: ignore
        self._status.showMessage("Ready")
