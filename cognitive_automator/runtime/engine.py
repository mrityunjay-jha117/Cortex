"""
=============================================================================
 RUNTIME ENGINE
=============================================================================
This module defines the core execution loop that traverses the Action Graph.
It manages state, calls node executors, and determines the next node to run.

Key Features:
1. Maintains the `RuntimeContext` holding all variable state.
2. Resolves edges based on executor results (e.g., branching).

Think of this module as the heartbeat and brain stem of the running automation.
=============================================================================
"""

from __future__ import annotations
import logging
import traceback
import inspect
from typing import Any
import pyautogui  # type: ignore

from cognitive_automator.graph_model import ActionGraph, AnyNode, SubGraphNode, EdgeLabel, ForLoopNode, IterateNode, DynamicIterateNode, GlobalEndNode, GlobalStartNode, OnErrorAction
from cognitive_automator.nodes.executors import NodeResult
from .models import ExecutionConfig, ExecutionEvent, ExecutionStatus, StatusCallback, AbortException
from .registry import EXECUTOR_REGISTRY

log = logging.getLogger(__name__)

class GraphExecutor:
    def __init__(self, graph: ActionGraph, config: ExecutionConfig | None = None, on_event: StatusCallback | None = None) -> None:
        self.graph = graph
        self.config = config or ExecutionConfig()
        self.on_event = on_event or (lambda e: None)
        self._context: dict[str, Any] = dict(self.config.initial_context)
        self._paused = False
        self._abort = False

    def pause(self) -> None: self._paused = True
    def resume(self) -> None: self._paused = False
    def abort(self) -> None: self._abort = True

    def run(self) -> dict[str, Any]:
        pyautogui.FAILSAFE = False
        self._emit(ExecutionStatus.STARTED)
        
        back_edges = set()
        visited = set()
        rec_stack = set()
        
        adj = {nid: [] for nid in self.graph.nodes}
        for e in self.graph.edges:
            adj.setdefault(e.source_id, []).append(e)

        def dfs(u: str) -> None:
            visited.add(u)
            rec_stack.add(u)
            for e in adj.get(u, []):
                v = e.target_id
                if v not in visited:
                    dfs(v)
                elif v in rec_stack:
                    back_edges.add((u, v, e.label))
            rec_stack.remove(u)
            
        start_nodes = [nid for nid, node in self.graph.nodes.items() if isinstance(node, GlobalStartNode)]
        if self.graph.entry_node_id and self.graph.entry_node_id in self.graph.nodes:
            if self.graph.entry_node_id not in start_nodes:
                start_nodes.append(self.graph.entry_node_id)
                
        for nid in start_nodes:
            if nid not in visited:
                dfs(nid)
                
        for nid in self.graph.nodes:
            if nid not in visited:
                dfs(nid)

        forward_in_degree = {nid: 0 for nid in self.graph.nodes}
        for e in self.graph.edges:
            if (e.source_id, e.target_id, e.label) not in back_edges:
                forward_in_degree[e.target_id] += 1

        initial_nodes = [nid for nid, deg in forward_in_degree.items() if deg == 0]

        node_tokens = {nid: 0 for nid in self.graph.nodes}
        node_exec_requests = {nid: 0 for nid in self.graph.nodes}
        
        from collections import deque
        queue: deque[tuple[str, bool, bool]] = deque()
        
        for sn in initial_nodes:
            forward_in_degree[sn] += 1
            queue.append((sn, True, False))

        try:
            while queue and not self._abort:
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
                
                node = self.graph.nodes.get(nid)
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
                    
                while self._paused and not self._abort:
                    import time; time.sleep(0.1)
                if self._abort: raise AbortException()
                
                self._emit(ExecutionStatus.NODE_ENTER, node_id=nid, node_label=node.label or nid)
                result = self._execute_with_retry(node)
                if self._abort: raise AbortException()
                
                if result.output_key:
                    self._context[result.output_key] = result.output_value
                    
                if result.success:
                    if result.healed:
                        self._emit(ExecutionStatus.NODE_HEALED, node_id=nid, node_label=node.label)
                    self._emit(ExecutionStatus.NODE_SUCCESS, node_id=nid, node_label=node.label)
                    
                    if isinstance(node, GlobalEndNode):
                        push_tokens([], skip_others=True)
                        continue
                        
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
                        continue
                        
                    if node.on_error == OnErrorAction.CONTINUE:
                        log.warning(f"Node '{nid}' failed but on_error is CONTINUE.")
                        push_tokens([EdgeLabel.DEFAULT.value], skip_others=True)
                    else:
                        raise RuntimeError(f"Node '{nid}' failed: {result.error}")

            self._emit(ExecutionStatus.GRAPH_COMPLETE, message="All nodes completed.")
        except pyautogui.FailSafeException:
            self._emit(ExecutionStatus.GRAPH_ABORTED, message="FAILSAFE triggered — mouse corner.")
            raise
        except AbortException:
            self._emit(ExecutionStatus.GRAPH_ABORTED, message="Aborted by user.")
        except Exception as exc:  # noqa: BLE001
            self._emit(ExecutionStatus.GRAPH_ABORTED, message=f"Unhandled error: {exc}")
            log.error(f"Graph execution aborted: {exc}\n{traceback.format_exc()}")
        return self._context

    def _execute_with_retry(self, node: AnyNode) -> NodeResult:
        import time
        last_result = NodeResult(success=False, error="Not executed")
        max_retries = node.retry_count
        retry_delay = node.retry_delay

        for attempt in range(max_retries + 1):
            if self._abort: raise AbortException()
            if attempt > 0:
                self._emit(ExecutionStatus.NODE_RETRYING, node_id=node.id, message=f"Retry {attempt}/{max_retries}")
                remaining = retry_delay
                while remaining > 0:
                    if self._abort: raise AbortException()
                    step = min(remaining, 0.1)
                    time.sleep(step)
                    remaining -= step
            
            last_result = self._dispatch(node)
            if last_result.success:
                return last_result
        return last_result

    def _dispatch(self, node: AnyNode) -> NodeResult:
        if isinstance(node, SubGraphNode):
            return self._execute_subgraph(node)
            
        func = EXECUTOR_REGISTRY.get(type(node))
        if not func:
            return NodeResult(success=False, error=f"Unknown node type: {type(node).__name__}")

        if not hasattr(self.__class__, '_executor_sig_cache'):
            self.__class__._executor_sig_cache = {}
            
        if func not in self.__class__._executor_sig_cache:
            self.__class__._executor_sig_cache[func] = inspect.signature(func)
            
        sig = self.__class__._executor_sig_cache[func]
        kwargs = {}
        
        if "abort_signal" in sig.parameters: kwargs["abort_signal"] = lambda: self._abort
        if "emit_info" in sig.parameters: kwargs["emit_info"] = lambda msg: self._emit(ExecutionStatus.NODE_INFO, node_id=node.id, node_label=node.label, message=msg)
        if "dev_mode" in sig.parameters: kwargs["dev_mode"] = self.config.dev_mode
        if "llm_config" in sig.parameters: kwargs["llm_config"] = self.graph.llm_config
        if "graph" in sig.parameters: kwargs["graph"] = self.graph
        
        return func(node, self._context, **kwargs)

    def _execute_subgraph(self, node: SubGraphNode) -> NodeResult:
        from cognitive_automator.serializer.file_io.load import load_graph
        try:
            sub_graph = load_graph(node.sub_graph_path)
            sub_config = ExecutionConfig(
                initial_context={k: self._context.get(v, "") for k, v in node.input_mapping.items()}
            )
            sub_executor = GraphExecutor(sub_graph, sub_config, self.on_event)
            sub_context = sub_executor.run()
            for out_key, ctx_key in node.output_mapping.items():
                if out_key in sub_context:
                    self._context[ctx_key] = sub_context[out_key]
            return NodeResult(success=True)
        except Exception as exc:
            return NodeResult(success=False, error=str(exc))

    def _emit(self, status: ExecutionStatus, node_id: str = "", node_label: str = "", message: str = "") -> None:
        event = ExecutionEvent(status=status, node_id=node_id, node_label=node_label, message=message, context_snapshot=dict(self._context))
        try:
            self.on_event(event)
        except Exception:
            pass
