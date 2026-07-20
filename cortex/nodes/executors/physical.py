"""
=============================================================================
 PHYSICAL EXECUTOR
=============================================================================
This module executes commands that interact with the mouse and keyboard.
It uses libraries like PyAutoGUI to simulate human input on the host machine.

Key Features:
1. Moves the mouse, clicks, and drags based on node parameters.
2. Simulates keystrokes and shortcuts (e.g., Ctrl+C).

Think of this module as the ghost in the machine typing on your keyboard.
=============================================================================
"""

from .physical_components import execute_mouse, execute_navigator, execute_keyboard, execute_file_drop, execute_clipboard

__all__ = ["execute_mouse", "execute_navigator", "execute_keyboard", "execute_file_drop", "execute_clipboard"]
