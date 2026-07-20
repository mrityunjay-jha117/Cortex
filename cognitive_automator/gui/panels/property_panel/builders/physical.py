"""
=============================================================================
 PHYSICAL PROPERTY BUILDERS
=============================================================================
This module generates UI forms for physical interaction nodes.
It handles inputs for coordinates, key presses, and mouse actions.

Key Features:
1. Validates X/Y coordinate inputs.
2. Provides dropdowns for specific keyboard keys and mouse buttons.

Think of this module as the remote control for the digital hands.
=============================================================================
"""

from .physical_components import PhysicalBuilders

__all__ = ["PhysicalBuilders"]
