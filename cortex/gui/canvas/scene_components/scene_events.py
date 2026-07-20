"""
=============================================================================
 SCENE_EVENTS.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from .mouse import SceneMouseHandler

class SceneEventsMixin:
    def mousePressEvent(self, event: Any) -> None:
        if not SceneMouseHandler.mousePressEvent(self, event): # type: ignore
            super().mousePressEvent(event) # type: ignore

    def mouseMoveEvent(self, event: Any) -> None:
        if not SceneMouseHandler.mouseMoveEvent(self, event): # type: ignore
            super().mouseMoveEvent(event) # type: ignore

    def mouseReleaseEvent(self, event: Any) -> None:
        if not SceneMouseHandler.mouseReleaseEvent(self, event): # type: ignore
            super().mouseReleaseEvent(event) # type: ignore
