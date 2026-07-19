"""
=============================================================================
 SYSTEM NODES
=============================================================================
This module defines nodes that interact with the host operating system.
It covers tasks like file operations, running commands, and process management.

Key Features:
1. Defines models for system-level actions (e.g., executing scripts).
2. Manages properties related to file paths and environment configurations.

Think of this module as the automator's bridge to the host computer's OS.
=============================================================================
"""

from typing import Literal
from pydantic import BaseModel, Field
from .enums import NodeCategory
from .base import BaseNode

class CSVDataLoaderNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = ""
    output_key: str = "csv_data"

class GlobalStartNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM

class GlobalEndNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM

class WriteFileNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = "output.txt"
    content_template: str = "{{vision_data}}"
    append: bool = False
    output_key: str = "write_status"

class CSVWriterNode(BaseNode):
    category: Literal[NodeCategory.SYSTEM] = NodeCategory.SYSTEM
    file_path: str = "output.csv"
    data_source_key: str = ""
    append: bool = True
    output_key: str = "csv_write_status"
