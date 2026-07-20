"""
=============================================================================
 UI_BUILDER.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .ui_builder_main import UIBuilderMainMixin
from .ui_builder_menu import UIBuilderMenuMixin

class UIBuilderMixin(UIBuilderMainMixin, UIBuilderMenuMixin):
    pass
