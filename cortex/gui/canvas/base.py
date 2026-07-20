"""
=============================================================================
 CANVAS BASE CLASSES
=============================================================================
This module defines abstract graphics classes used on the canvas.
It provides common utilities for drawing, selection, and hovering effects.

Key Features:
1. Handles standard QGraphicsItem event logic.
2. Ensures all visual items share a consistent styling baseline.

Think of this module as the foundational canvas material every drawing relies on.
=============================================================================
"""

from __future__ import annotations

import collections
from typing import Any

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QBrush,
    QLinearGradient, QCursor, QTransform, QPixmap,
)
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView,
    QGraphicsPathItem, QMenu, QStyleOptionGraphicsItem, QWidget,
)

from cortex.graph_model import (
    ActionGraph, AnyNode, EdgeLabel, FileDropNode,
    GlobalStartNode, GlobalEndNode, ForLoopNode, CSVDataLoaderNode,
)
from cortex.gui.constants import NODE_COLORS, APP_BG, APP_ACCENT

NODE_W = 200
NODE_H = 70
PORT_RADIUS = 6
GRID_SIZE = 40

def _elide(text: str, max_width: int, font_size: int = 10) -> str:
    if len(text) * (font_size * 0.6) <= max_width:
        return text
    chars = int(max_width / (font_size * 0.6)) - 1
    return text[:max(chars, 4)] + "…"

