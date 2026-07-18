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
