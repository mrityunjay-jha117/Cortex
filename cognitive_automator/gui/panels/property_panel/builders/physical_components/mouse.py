"""
=============================================================================
 MOUSE.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from cognitive_automator.graph_model import MouseNode, MouseAction

class MouseBuilder:
    def _build_mouse(self, node: MouseNode) -> None:
        action_combo = self._combo(
            [a.value for a in MouseAction], node.action.value,
            lambda v: [self._set(node, "action", MouseAction(v)), self._rebuild_form(node)]
        )
        self._form_layout.addRow("Action", action_combo)

        if node.action == MouseAction.SCROLL:
            self._form_layout.addRow("Scroll Amount", self._spin(node.scroll_amount, -10000, 10000, lambda v: self._set(node, "scroll_amount", v)))
            self._add_hint(
                "Negative = Scroll Down (typical)\n"
                "Positive = Scroll Up\n"
                "Windows: -120 is one notch. Try -1200 for a significant scroll."
            )

        self._form_layout.addRow("X", self._spin(node.x_coord, 0, 9999, lambda v: self._set(node, "x_coord", v)))
        self._form_layout.addRow("Y", self._spin(node.y_coord, 0, 9999, lambda v: self._set(node, "y_coord", v)))
        
        self._add_section("Vision / Offsets")
        self._form_layout.addRow("Vision ID", self._line_edit(node.vision_node_id or "", lambda v: self._set(node, "vision_node_id", v if v else None)))
        
        # X Offset
        def on_x_offset(v: int) -> None:
            self._set(node, "x_offset", v)
            x_val_label.setText(str(v))
        x_row = QWidget()
        x_layout = QHBoxLayout(x_row)
        x_layout.setContentsMargins(0,0,0,0)
        x_slider = self._slider(node.x_offset, -2000, 2000, on_x_offset)
        x_val_label = QLabel(str(node.x_offset))
        x_val_label.setFixedWidth(40)
        x_layout.addWidget(x_slider)
        x_layout.addWidget(x_val_label)
        self._form_layout.addRow("X Offset", x_row)

        # Y Offset
        def on_y_offset(v: int) -> None:
            self._set(node, "y_offset", v)
            y_val_label.setText(str(v))
        y_row = QWidget()
        y_layout = QHBoxLayout(y_row)
        y_layout.setContentsMargins(0,0,0,0)
        y_slider = self._slider(node.y_offset, -2000, 2000, on_y_offset)
        y_val_label = QLabel(str(node.y_offset))
        y_val_label.setFixedWidth(40)
        y_layout.addWidget(y_slider)
        y_layout.addWidget(y_val_label)
        self._form_layout.addRow("Y Offset", y_row)

        self._add_section("Settings")
        self._form_layout.addRow("Duration (s)", self._dspin(node.duration, 0.0, 5.0, lambda v: self._set(node, "duration", v)))
