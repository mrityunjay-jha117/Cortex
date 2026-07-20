"""
=============================================================================
 EXECUTORS INITIALIZATION
=============================================================================
This module initializes the executors subpackage.
It exposes the base classes and specialized runners for different node categories.

Key Features:
1. Groups logic execution handlers into a central namespace.
2. Ensures all nodes have a registered runner class.

Think of this module as the staging area for the execution crew.
=============================================================================
"""

from .base import *
from .physical import *
from .vision import *
from .llm import *
from .flow import *
