"""
=============================================================================
 GUI CANVAS INITIALIZATION
=============================================================================
This module initializes the visual node editor canvas.
It groups the scene, view, nodes, and edges into a single importable package.

Key Features:
1. Orchestrates the visual drawing board for the node graph.
2. Bridges abstract graph concepts with UI renderables.

Think of this module as the art supply box for drawing automation flows.
=============================================================================
"""

from .base import *
from .port import *
from .node import *
from .edge import *
from .scene import *
from .view import *
