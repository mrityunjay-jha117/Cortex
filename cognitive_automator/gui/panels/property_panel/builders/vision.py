"""
=============================================================================
 VISION PROPERTY BUILDERS
=============================================================================
This module generates UI forms for computer vision nodes.
It handles properties like confidence thresholds and bounding boxes.

Key Features:
1. Builds inputs for region-of-interest selection.
2. Provides tuning sliders for visual matching sensitivity.

Think of this module as the optometrist's toolkit for calibrating the digital eyes.
=============================================================================
"""

from .vision_components import VisionBuilders

__all__ = ["VisionBuilders"]
