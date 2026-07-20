"""
=============================================================================
 PAINTER.PY (node_components)
=============================================================================
This module is a microservice component for node_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .painter_base import NodePainterBase
from .painter_header import NodePainterHeader
from .painter_content import NodePainterContent

class NodePainter:
    @staticmethod
    def bounding_rect(node_item):
        return NodePainterBase.bounding_rect(node_item)

    @staticmethod
    def paint(node_item, painter, option, widget=None) -> None:
        h = node_item.node_h
        header_color, _ = NodePainterBase._draw_background_and_border(node_item, painter, h)
        header_h = NodePainterHeader._draw_header(node_item, painter, header_color)
        NodePainterContent._draw_content(node_item, painter, header_h, h)

__all__ = ["NodePainter"]
