"""
=============================================================================
 DATA PROPERTY BUILDERS
=============================================================================
This module generates UI forms specifically for Data handling nodes.
It handles properties like file paths, schemas, and variables.

Key Features:
1. Provides specialized file picker widgets.
2. Simplifies configuring inputs for CSV loaders and data extractors.

Think of this module as the settings menu for filing cabinets.
=============================================================================
"""

from .data_components import DataBuilders

__all__ = ["DataBuilders"]
