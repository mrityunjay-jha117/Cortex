"""
=============================================================================
 PROPERTY BUILDERS INITIALIZATION
=============================================================================
This module initializes the dynamic UI builders for node properties.
It groups the specific form generators tailored to different node types.

Key Features:
1. Registers builders for LLM, Flow, Data, and Vision nodes.
2. Routes node property editing to the correct specialized form.

Think of this module as the factory manager delegating form creation.
=============================================================================
"""

from .flow import FlowBuilders
from .data import DataBuilders
from .physical import PhysicalBuilders
from .vision import VisionBuilders
from .llm import LlmBuilders
from .base import BaseBuilders

class PropertyPanelBuilders(FlowBuilders, DataBuilders, PhysicalBuilders, VisionBuilders, LlmBuilders, BaseBuilders):
    pass
