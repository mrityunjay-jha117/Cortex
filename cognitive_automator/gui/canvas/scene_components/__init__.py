"""
=============================================================================
 __INIT__.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .scene_base import SceneBaseMixin
from .scene_load import SceneLoadMixin
from .scene_state import SceneStateMixin
from .scene_events import SceneEventsMixin

class GraphScene(SceneEventsMixin, SceneStateMixin, SceneLoadMixin, SceneBaseMixin):
    pass

__all__ = ["GraphScene"]
