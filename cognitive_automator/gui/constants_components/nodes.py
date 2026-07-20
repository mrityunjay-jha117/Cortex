"""
=============================================================================
 NODES.PY (constants_components)
=============================================================================
This module is a microservice component for constants_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Dict

# Node category colors
NODE_COLORS: Dict[str, Dict[str, str]] = {
    "physical": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "vision": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "llm": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "flow": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "logic": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "system": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
}

NODE_CATEGORY_LABELS: Dict[str, str] = {
    "physical": "Physical IO",
    "vision": "Vision",
    "llm": "LLM Logic",
    "flow": "Flow Control",
    "logic": "Programmatic Logic",
    "system": "System Markers",
}
