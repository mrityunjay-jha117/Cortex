"""
gui/canvas.py — Visual node graph editor using PyQt6 QGraphicsScene/View.

Nodes are rendered as draggable QGraphicsItems.
Edges are drawn as bezier curves between port sockets.
"""

from __future__ import annotations

import collections
from typing import Any

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QBrush,
    QLinearGradient, QCursor,
)
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView,
    QGraphicsPathItem, QMenu, QStyleOptionGraphicsItem, QWidget,
)

from cognitive_automator.graph_model import (
    ActionGraph, AnyNode, EdgeLabel, FileDropNode,
    GlobalStartNode, GlobalEndNode, ForLoopNode, CSVDataLoaderNode,
)
from cognitive_automator.gui.constants import NODE_COLORS, APP_BG, APP_ACCENT

NODE_W = 200
NODE_H = 70
PORT_RADIUS = 6
GRID_SIZE = 40

def _elide(text: str, max_width: int, font_size: int = 10) -> str:
    if len(text) * (font_size * 0.6) <= max_width:
        return text
    chars = int(max_width / (font_size * 0.6)) - 1
    return text[:max(chars, 4)] + "…"

