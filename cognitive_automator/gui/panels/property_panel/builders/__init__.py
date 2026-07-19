"""
gui/panels/property_panel/builders/__init__.py — Node Form Builders

This package contains individual builder classes that generate specific UI layouts for different node categories.
"""
from .flow import FlowBuilders
from .data import DataBuilders
from .physical import PhysicalBuilders
from .vision import VisionBuilders
from .llm import LlmBuilders
from .base import BaseBuilders

class PropertyPanelBuilders(FlowBuilders, DataBuilders, PhysicalBuilders, VisionBuilders, LlmBuilders, BaseBuilders):
    pass
