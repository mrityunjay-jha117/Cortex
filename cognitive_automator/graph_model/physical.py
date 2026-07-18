from typing import Literal
from pydantic import BaseModel, Field
from .enums import NodeCategory, MouseAction, KeyboardAction, ClipboardAction, NavigationAction, ScreenshotMode, DetectionMode
from .base import BaseNode

class MouseNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: MouseAction = MouseAction.CLICK
    x_coord: int = 0
    y_coord: int = 0
    dest_x: int = 0
    dest_y: int = 0
    duration: float = 0.0
    button: str = "left"
    vision_node_id: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    scroll_amount: int = 0

class KeyboardNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: KeyboardAction = KeyboardAction.TYPEWRITE
    text: str = ""
    key: str = ""
    keys: list[str] = Field(default_factory=list)
    interval: float = 0.0

class ClipboardNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    action: ClipboardAction = ClipboardAction.READ
    write_text: str = ""
    source_output_key: str | None = None

class NavigatorNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    reference_image_b64: str = ""
    x_offset: int = 0
    y_offset: int = 0
    confidence: float = 0.75
    action: NavigationAction = NavigationAction.PAGE_DOWN
    repeat: int = 1

class FileDropNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    file_path: str = ""
    x_coord: int = 0
    y_coord: int = 0
    vision_node_id: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    wait_after_click: float = 1.0
    output_key: str = "dropped_file_path"

class ScreenshotterNode(BaseNode):
    category: Literal[NodeCategory.PHYSICAL] = NodeCategory.PHYSICAL
    mode: ScreenshotMode = ScreenshotMode.N_TIMES
    n_times: int = 3
    scroll_amount: int = -1000
    wait_per_scroll: float = 1.0
    output_key: str = "captured_images"
    detection_mode: DetectionMode = DetectionMode.NONE
    reference_image_b64: str | None = None
    x_offset: int = 0
    y_offset: int = 0
    confidence: float = 0.8
    grayscale: bool = False
    wait_after_click: float = 0.5
