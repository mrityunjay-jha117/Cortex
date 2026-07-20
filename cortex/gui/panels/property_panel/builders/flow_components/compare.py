"""
=============================================================================
 COMPARE.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QCheckBox
from cortex.graph_model import CompareNode, CompareOp

class CompareMixin:
    def _build_compare(self, node: CompareNode) -> None:
        self._form_layout.addRow( # type: ignore
            "Left Operand",
            self._line_edit(node.left_operand, lambda v: self._set(node, "left_operand", v)) # type: ignore
        )
        self._form_layout.addRow("Operator", self._combo( # type: ignore
            [op.value for op in CompareOp], node.operator.value,
            lambda v: self._set(node, "operator", CompareOp(v)) # type: ignore
        ))
        self._form_layout.addRow( # type: ignore
            "Right Operand",
            self._line_edit(node.right_operand, lambda v: self._set(node, "right_operand", v)) # type: ignore
        )
        cs_cb = QCheckBox()
        cs_cb.setChecked(node.case_sensitive)
        cs_cb.toggled.connect(lambda v: self._set(node, "case_sensitive", v)) # type: ignore
        self._form_layout.addRow("Case Sensitive", cs_cb) # type: ignore
        self._add_hint( # type: ignore
            "Use {{key}} to pull values from context.\n"
            "Numeric ops (num_*) parse both sides as float.\n"
            "Routes to TRUE or FALSE edge."
        )
