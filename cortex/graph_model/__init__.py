"""
=============================================================================
 GRAPH MODEL INITIALIZATION
=============================================================================
This module initializes the graph model subpackage.
It exposes the fundamental data structures representing nodes and edges.

Key Features:
1. Groups related graph schema components into a single namespace.
2. Simplifies imports for the rest of the application.

Think of this module as the table of contents for the graph data structures.
=============================================================================
"""

from .enums import *
from .base import *
from .physical import *
from .vision import *
from .llm import *
from .flow import *
from .system import *
from .edges import *
from .graph import *
