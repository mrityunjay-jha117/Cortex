from .flow import FlowBuilders
from .data import DataBuilders
from .physical import PhysicalBuilders
from .vision import VisionBuilders
from .llm import LlmBuilders
from .base import BaseBuilders

class PropertyPanelBuilders(FlowBuilders, DataBuilders, PhysicalBuilders, VisionBuilders, LlmBuilders, BaseBuilders):
    pass
