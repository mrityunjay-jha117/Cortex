"""
=============================================================================
 EXECUTION_RESULT.PY (engine_components)
=============================================================================
This module is a microservice component for engine_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import logging
from cognitive_automator.graph_model import EdgeLabel, ForLoopNode, IterateNode, DynamicIterateNode, GlobalEndNode, OnErrorAction
from ..models import ExecutionStatus

log = logging.getLogger(__name__)

def process_node_result(self, node, nid, result, out_edges, push_tokens):
    if result.output_key:
        self._context[result.output_key] = result.output_value
        
    if result.success:
        if result.healed:
            self._emit(ExecutionStatus.NODE_HEALED, node_id=nid, node_label=node.label)
        self._emit(ExecutionStatus.NODE_SUCCESS, node_id=nid, node_label=node.label)
        
        if isinstance(node, GlobalEndNode):
            push_tokens([], skip_others=True)
            return
            
        if isinstance(node, (ForLoopNode, IterateNode, DynamicIterateNode)):
            if result.next_edge == EdgeLabel.LOOP_BODY:
                push_tokens([EdgeLabel.LOOP_BODY.value], skip_others=False)
            else:
                push_tokens([EdgeLabel.LOOP_END.value], skip_others=True)
        else:
            push_tokens([result.next_edge.value], skip_others=True)
    else:
        self._emit(ExecutionStatus.NODE_FAILED, node_id=nid, message=result.error)
        
        error_edges = [e for e in out_edges if e.label == EdgeLabel.ERROR]
        if error_edges:
            log.info(f"Routing to error edge from '{nid}'")
            push_tokens([EdgeLabel.ERROR.value], skip_others=True)
            return
            
        if node.on_error == OnErrorAction.CONTINUE:
            log.warning(f"Node '{nid}' failed but on_error is CONTINUE.")
            push_tokens([EdgeLabel.DEFAULT.value], skip_others=True)
        else:
            raise RuntimeError(f"Node '{nid}' failed: {result.error}")
