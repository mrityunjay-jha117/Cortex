"""
=============================================================================
 MOUSE.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .mouse_press import SceneMousePress
from .mouse_move import SceneMouseMove
from .mouse_release import SceneMouseRelease

class SceneMouseHandler(SceneMousePress, SceneMouseMove, SceneMouseRelease):
    pass

__all__ = ["SceneMouseHandler"]
