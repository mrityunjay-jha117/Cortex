from enum import Enum

class NodeCategory(str, Enum):
    PHYSICAL = "physical"
    VISION = "vision"
    LLM = "llm"
    FLOW = "flow"
    LOGIC = "logic"
    SYSTEM = "system"

class MouseAction(str, Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE_TO = "move_to"
    DRAG_TO = "drag_to"
    SCROLL = "scroll"

class KeyboardAction(str, Enum):
    TYPEWRITE = "typewrite"
    PRESS = "press"
    HOTKEY = "hotkey"
    PASTE = "paste"
    SELECT_ALL = "select_all"

class ClipboardAction(str, Enum):
    READ = "read"
    WRITE = "write"

class NavigationAction(str, Enum):
    PAGE_UP = "pageup"
    PAGE_DOWN = "pagedown"
    HOME = "home"
    END = "end"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class LLMProvider(str, Enum):
    OPENROUTER = "openrouter"

class CompareOp(str, Enum):
    EQUALS          = "equals"
    NOT_EQUALS      = "not_equals"
    CONTAINS        = "contains"
    NOT_CONTAINS    = "not_contains"
    STARTS_WITH     = "starts_with"
    ENDS_WITH       = "ends_with"
    IS_EMPTY        = "is_empty"
    IS_NOT_EMPTY    = "is_not_empty"
    NUM_GT          = "num_gt"
    NUM_LT          = "num_lt"
    NUM_GTE         = "num_gte"
    NUM_LTE         = "num_lte"
    NUM_EQUALS      = "num_equals"

class OnErrorAction(str, Enum):
    STOP = "stop"
    CONTINUE = "continue"
    RETRY = "retry"

class ScreenshotMode(str, Enum):
    N_TIMES = "n_times"
    UNTIL_END = "until_end"

class DetectionMode(str, Enum):
    NONE = "none"
    SINGLE = "single"
    MULTIPLE = "multiple"

class EdgeLabel(str, Enum):
    DEFAULT = "default"
    TRUE = "true"
    FALSE = "false"
    LOOP_BODY = "loop_body"
    LOOP_END = "loop_end"
    DATA_BIND = "data_bind"
    ERROR = "error"
