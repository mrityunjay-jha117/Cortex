"""
=============================================================================
 PORTS.PY (node_components)
=============================================================================
This module is a microservice component for node_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.gui.canvas.base import NODE_W, NODE_H, EdgeLabel
from cortex.gui.canvas.port import PortItem
from cortex.graph_model import (
    GlobalStartNode, GlobalEndNode, ForLoopNode,
    LLMJudgmentNode, BranchNode, IterateNode, DynamicIterateNode,
    CompareNode,
)

def setup_node_ports(node_item) -> None:
    node = node_item.node
    h = node_item.node_h
    
    # Default input (Left)
    if isinstance(node, GlobalStartNode):
        node_item._input_ports = []
        node_item._input_port = None
    elif not isinstance(node, ForLoopNode):
        in_port = PortItem(node_item, is_output=False, parent=node_item)
        in_port.setPos(0, h / 2)
        node_item._input_ports = [in_port]
        node_item._input_port = in_port # legacy
    else:
        # ForLoopNode specialized inputs
        # Left: In (from previous node)
        left_in = PortItem(node_item, is_output=False, label="In", parent=node_item)
        left_in.setPos(0, h / 2)
        
        # Bottom Right: Back-link from loop end
        back_in = PortItem(node_item, is_output=False, label="Back", parent=node_item)
        back_in.setPos(NODE_W * 0.75, h)
        
        # Top: Data Bind (from CSV Loader)
        data_in = PortItem(node_item, is_output=False, label="Data", edge_label=EdgeLabel.DEFAULT, parent=node_item)
        data_in.setPos(NODE_W / 2, 0)
        
        node_item._input_ports = [left_in, back_in, data_in]
        node_item._input_port = left_in

    # Output ports
    if isinstance(node, GlobalEndNode):
        node_item._output_ports = []
    elif isinstance(node, (LLMJudgmentNode, BranchNode, CompareNode)):
        t_port = PortItem(node_item, is_output=True, label="T", edge_label=EdgeLabel.TRUE, parent=node_item)
        t_port.setPos(NODE_W, h * 0.35)
        f_port = PortItem(node_item, is_output=True, label="F", edge_label=EdgeLabel.FALSE, parent=node_item)
        f_port.setPos(NODE_W, h * 0.65)
        node_item._output_ports = [t_port, f_port]
    elif isinstance(node, ForLoopNode):
        # Bottom Left: Body (start loop)
        body_port = PortItem(node_item, is_output=True, label="↻ Body", edge_label=EdgeLabel.LOOP_BODY, parent=node_item)
        body_port.setPos(NODE_W * 0.25, h)
        
        # Right: End (finished)
        end_port = PortItem(node_item, is_output=True, label=" End", edge_label=EdgeLabel.LOOP_END, parent=node_item)
        end_port.setPos(NODE_W, h / 2)
        
        node_item._output_ports = [body_port, end_port]
    elif isinstance(node, (IterateNode, DynamicIterateNode)):
        body_port = PortItem(node_item, is_output=True, label="↻", edge_label=EdgeLabel.LOOP_BODY, parent=node_item)
        body_port.setPos(NODE_W, h * 0.35)
        end_port = PortItem(node_item, is_output=True, label="", edge_label=EdgeLabel.LOOP_END, parent=node_item)
        end_port.setPos(NODE_W, h * 0.65)
        node_item._output_ports = [body_port, end_port]
    else:
        default_port = PortItem(node_item, is_output=True, label="", edge_label=EdgeLabel.DEFAULT, parent=node_item)
        default_port.setPos(NODE_W, h / 2)
        node_item._output_ports = [default_port]
