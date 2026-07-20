"""
=============================================================================
 __INIT__.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .mouse import MouseBuilder
from .keyboard import KeyboardBuilder
from .clipboard import ClipboardBuilder
from .locate import LocateBuilder
from .navigator import NavigatorBuilder

class PhysicalBuilders(MouseBuilder, KeyboardBuilder, ClipboardBuilder, LocateBuilder, NavigatorBuilder):
    pass
