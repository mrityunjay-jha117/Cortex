"""
=============================================================================
 LOCATE.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cognitive_automator.graph_model import LocateElementNode, LocateAndClickNode, MouseAction
from .locate_image import LocateImageMixin
from .locate_options import LocateOptionsMixin

class LocateBuilder(LocateImageMixin, LocateOptionsMixin):
    def _build_locate(self, node: LocateElementNode) -> None:
        self._build_locate_image(node)
        self._build_locate_options(node)

    def _build_locate_and_click(self, node: LocateAndClickNode) -> None:
        self._build_locate(node)
        
        self._add_section("Mouse Action") # type: ignore
        action_combo = self._combo( # type: ignore
            [a.value for a in MouseAction if a not in (MouseAction.DRAG_TO, MouseAction.SCROLL)], 
            node.action.value,
            lambda v: self._set(node, "action", MouseAction(v)) # type: ignore
        )
        self._form_layout.addRow("Click Action", action_combo) # type: ignore
        
        self._form_layout.addRow("Button", self._combo( # type: ignore
            ["left", "right", "middle"], node.button,
            lambda v: self._set(node, "button", v) # type: ignore
        ))
        
        self._form_layout.addRow("Duration (s)", self._dspin(node.duration, 0.0, 5.0, lambda v: self._set(node, "duration", v))) # type: ignore
        self._form_layout.addRow("Wait After (s)", self._dspin(node.wait_after_click, 0.0, 10.0, lambda v: self._set(node, "wait_after_click", v))) # type: ignore

__all__ = ["LocateBuilder"]
