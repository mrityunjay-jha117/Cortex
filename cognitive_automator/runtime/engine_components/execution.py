"""
=============================================================================
 EXECUTION.PY (engine_components)
=============================================================================
This module is a microservice component for engine_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import logging
import traceback
from typing import Any
import pyautogui  # type: ignore
from collections import deque

from ..models import ExecutionStatus, AbortException
from .execution_graph import build_adj, find_back_edges, calculate_forward_in_degree
from .execution_result import process_node_result

log = logging.getLogger(__name__)

class ExecutionMixin:
    def run(self) -> dict[str, Any]:
        pyautogui.FAILSAFE = False
        self._emit(ExecutionStatus.STARTED) # type: ignore
        
        adj = build_adj(self.graph) # type: ignore
        back_edges = find_back_edges(self.graph, adj) # type: ignore
        forward_in_degree = calculate_forward_in_degree(self.graph, back_edges) # type: ignore
        initial_nodes = [nid for nid, deg in forward_in_degree.items() if deg == 0]

        node_tokens = {nid: 0 for nid in self.graph.nodes} # type: ignore
        node_exec_requests = {nid: 0 for nid in self.graph.nodes} # type: ignore
        
        queue: deque[tuple[str, bool, bool]] = deque()
        for sn in initial_nodes:
            forward_in_degree[sn] += 1
            queue.append((sn, True, False))

        try:
            while queue and not self._abort: # type: ignore
                nid, is_exec, is_back_edge = queue.popleft()
                
                if is_back_edge:
                    node_tokens[nid] = forward_in_degree[nid]
                    node_exec_requests[nid] = 1 if is_exec else 0
                else:
                    node_tokens[nid] += 1
                    if is_exec:
                        node_exec_requests[nid] += 1
                        
                if node_tokens[nid] < forward_in_degree[nid]:
                    continue
                    
                should_execute = (node_exec_requests[nid] > 0)
                node_tokens[nid] = 0
                node_exec_requests[nid] = 0
                
                node = self.graph.nodes.get(nid) # type: ignore
                if not node:
                    continue
                    
                out_edges = adj.get(nid, [])
                
                def push_tokens(label_to_exec: str | list[str], skip_others: bool = True) -> None:
                    if isinstance(label_to_exec, str): label_to_exec = [label_to_exec]
                    for e in out_edges:
                        is_be = (e.source_id, e.target_id, e.label) in back_edges
                        if e.label in label_to_exec:
                            queue.append((e.target_id, True, is_be))
                        elif skip_others:
                            if not is_be:
                                queue.append((e.target_id, False, is_be))

                if not should_execute or not node.enabled:
                    if not node.enabled:
                        log.debug(f"Node '{nid}' disabled. Skipping.")
                    push_tokens([], skip_others=True)
                    continue
                    
                while self._paused and not self._abort: # type: ignore
                    import time; time.sleep(0.1)
                if self._abort: raise AbortException() # type: ignore
                
                self._emit(ExecutionStatus.NODE_ENTER, node_id=nid, node_label=node.label or nid) # type: ignore
                result = self._execute_with_retry(node) # type: ignore
                if self._abort: raise AbortException() # type: ignore
                
                process_node_result(self, node, nid, result, out_edges, push_tokens)

            self._emit(ExecutionStatus.GRAPH_COMPLETE, message="All nodes completed.") # type: ignore
        except pyautogui.FailSafeException:
            self._emit(ExecutionStatus.GRAPH_ABORTED, message="FAILSAFE triggered — mouse corner.") # type: ignore
            raise
        except AbortException:
            self._emit(ExecutionStatus.GRAPH_ABORTED, message="Aborted by user.") # type: ignore
        except Exception as exc:
            self._emit(ExecutionStatus.GRAPH_ABORTED, message=f"Unhandled error: {exc}") # type: ignore
            log.error(f"Graph execution aborted: {exc}\n{traceback.format_exc()}")
        return self._context # type: ignore
