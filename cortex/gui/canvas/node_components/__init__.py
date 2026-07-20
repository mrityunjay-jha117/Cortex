"""
=============================================================================
 __INIT__.PY (node_components)
=============================================================================
This module is a microservice component for node_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .ports import setup_node_ports
from .painter import NodePainter

__all__ = ["setup_node_ports", "NodePainter"]
