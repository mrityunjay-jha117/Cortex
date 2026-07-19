"""
runtime/executor.py — Graph execution engine.

Walks the ActionGraph topologically, dispatching each node to its executor.
Manages execution context (shared dict), retry logic, and error edges.
Emits status events via a callback for GUI live updates.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


from cognitive_automator.graph_model import (
    ActionGraph,
    AnyNode,
    BranchNode,
    ClipboardNode,
    CompareNode,
    DynamicIterateNode,
    EdgeLabel,
    GenerativeOCRNode,
    IterateNode,
    ForLoopNode,
    GlobalStartNode,
    GlobalEndNode,
    KeyboardNode,
    LLMExtractionNode,
    LLMGenerativeNode,
    LLMJudgmentNode,
    LocateElementNode,
    LocateAndClickNode,
    VisionImageNode,
    MouseNode,
    NavigatorNode,
    FileDropNode,
    SubGraphNode,
    WaitNode,
    VisionExtractionNode,
    WriteFileNode,
    CSVDataLoaderNode,
    CSVWriterNode,
    ScreenshotterNode,
)
from cognitive_automator.nodes.executors import (
    NodeResult,
    execute_branch,
    execute_clipboard,
    execute_compare,
    execute_csv_data_loader,
    execute_csv_writer,
    execute_dynamic_iterate,
    execute_extraction,
    execute_file_drop,
    execute_for_loop,
    execute_generative,
    execute_generative_ocr,
    execute_iterate,
    execute_keyboard,
    execute_judgment,
    execute_locate_element,
    execute_locate_and_click,
    execute_mouse,
    execute_navigator,
    execute_screenshotter,
    execute_wait,
    execute_vision_extraction,
    execute_vision_image,
    execute_write_file,
    )


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Status events (consumed by GUI)
# ---------------------------------------------------------------------------

class ExecutionStatus(str, Enum):
    STARTED = "started"
    NODE_INFO = "node_info"
    NODE_ENTER = "node_enter"
    NODE_SUCCESS = "node_success"
    NODE_FAILED = "node_failed"
    NODE_RETRYING = "node_retrying"
    NODE_HEALED = "node_healed"
    GRAPH_COMPLETE = "graph_complete"
    GRAPH_ABORTED = "graph_aborted"
    PAUSED = "paused"


@dataclass
class ExecutionEvent:
    status: ExecutionStatus
    node_id: str = ""
    node_label: str = ""
    message: str = ""
    context_snapshot: dict[str, Any] = field(default_factory=dict)


StatusCallback = Callable[[ExecutionEvent], None]


# ---------------------------------------------------------------------------
# Execution config
# ---------------------------------------------------------------------------

@dataclass
class ExecutionConfig:
    max_retries_per_node: int = 2
    retry_delay_seconds: float = 1.0
    step_mode: bool = False          # pause before each node (debug)
    dev_mode: bool = False           # if true, skip AI fallbacks
    initial_context: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Graph Executor
# ---------------------------------------------------------------------------

class GraphExecutor:
    def __init__(
        self,
        graph: ActionGraph,
        config: ExecutionConfig | None = None,
        on_event: StatusCallback | None = None,
    ) -> None:
        self.graph = graph
        self.config = config or ExecutionConfig()
        self.on_event = on_event or (lambda e: None)
        self._context: dict[str, Any] = dict(self.config.initial_context)
        self._paused = False
        self._abort = False

    # ------------------------------------------------------------------
    # Public control
    # ------------------------------------------------------------------

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def abort(self) -> None:
        self._abort = True

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """
        Execute the graph using a dependency-aware Multi-Source token system.
        Raises FailSafeException immediately if PyAutoGUI detects corner move.
        """
        import pyautogui  # type: ignore
        pyautogui.FAILSAFE = False  # Disable emergency corner stop
        self._emit(ExecutionStatus.STARTED)
        
        # 1. Identify Back-Edges using DFS to prevent loop deadlocks
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
            
        # Prioritize DFS starting from GlobalStartNodes first, then entry_node_id
        start_nodes = []
        for nid, node in self.graph.nodes.items():
            if isinstance(node, GlobalStartNode):
                start_nodes.append(nid)
        
        if self.graph.entry_node_id and self.graph.entry_node_id in self.graph.nodes:
            if self.graph.entry_node_id not in start_nodes:
                start_nodes.append(self.graph.entry_node_id)
                
        # Run DFS on prioritized nodes first
        for nid in start_nodes:
            if nid not in visited:
                dfs(nid)
                
        # Then run on any remaining disconnected components
        for nid in self.graph.nodes:
            if nid not in visited:
                dfs(nid)

        # 2. Compute Forward In-Degree
        forward_in_degree = {nid: 0 for nid in self.graph.nodes}
        for e in self.graph.edges:
            if (e.source_id, e.target_id, e.label) not in back_edges:
                forward_in_degree[e.target_id] += 1

        # 3. Identify Initial Nodes (Multi-source)
        # Any node with 0 forward dependencies is a start node
        initial_nodes = [nid for nid, deg in forward_in_degree.items() if deg == 0]

        # 4. Token Tracking
        # node_tokens: how many forward tokens received
        # node_exec_requests: how many of those were EXECUTE (vs DEAD/CANCEL)
        node_tokens = {nid: 0 for nid in self.graph.nodes}
        node_exec_requests = {nid: 0 for nid in self.graph.nodes}
        
        from collections import deque
        # queue stores: (target_node_id, is_execute, is_back_edge)
        queue: deque[tuple[str, bool, bool]] = deque()
        
        for sn in initial_nodes:
            forward_in_degree[sn] += 1 # Add virtual edge for the initial kick
            queue.append((sn, True, False))

        try:
            while queue and not self._abort:
                nid, is_exec, is_back_edge = queue.popleft()
                
                if is_back_edge:
                    # Back-edges instantly satisfy dependencies for a new loop iteration
                    node_tokens[nid] = forward_in_degree[nid]
                    node_exec_requests[nid] = 1 if is_exec else 0
                else:
                    node_tokens[nid] += 1
                    if is_exec:
                        node_exec_requests[nid] += 1
                        
                # Check if all forward dependencies are met
                if node_tokens[nid] < forward_in_degree[nid]:
                    continue
                    
                should_execute = (node_exec_requests[nid] > 0)
                
                # Reset for future iterations
                node_tokens[nid] = 0
                node_exec_requests[nid] = 0
                
                node = self.graph.nodes.get(nid)
                if not node:
                    continue
                    
                out_edges = adj.get(nid, [])
                
                def push_tokens(label_to_exec: str | list[str], skip_others: bool = True) -> None:
                    if isinstance(label_to_exec, str):
                        label_to_exec = [label_to_exec]
                    for e in out_edges:
                        is_be = (e.source_id, e.target_id, e.label) in back_edges
                        if e.label in label_to_exec:
                            queue.append((e.target_id, True, is_be))
                        elif skip_others:
                            queue.append((e.target_id, False, is_be))

                if not should_execute or not node.enabled:
                    if not node.enabled:
                        log.debug("Node '%s' disabled. Skipping.", nid)
                    # Propagate DEAD token
                    push_tokens([], skip_others=True)
                    continue
                    
                while self._paused and not self._abort:
                    import time; time.sleep(0.1)
                if self._abort: raise AbortException()
                
                # Execute Node
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
                        
                    # Removed hardcoded 0.5s sleep to improve throughput
                    
                    # Custom token logic for loops to prevent DEAD token flooding
                    if isinstance(node, (ForLoopNode, IterateNode, DynamicIterateNode)):
                        if result.next_edge == EdgeLabel.LOOP_BODY:
                            # Loop continues: emit EXEC to body, hold END
                            push_tokens([EdgeLabel.LOOP_BODY.value], skip_others=False)
                        else:
                            # Loop ends: emit EXEC to END, DEAD to body
                            push_tokens([EdgeLabel.LOOP_END.value], skip_others=True)
                    else:
                        # Normal nodes: emit EXEC to chosen edge, DEAD to others
                        push_tokens([result.next_edge.value], skip_others=True)
                else:
                    self._emit(ExecutionStatus.NODE_FAILED, node_id=nid, message=result.error)
                    
                    error_edges = [e for e in out_edges if e.label == EdgeLabel.ERROR]
                    if error_edges:
                        log.info("Routing to error edge from '%s'", nid)
                        push_tokens([EdgeLabel.ERROR.value], skip_others=True)
                        continue
                        
                    from cognitive_automator.graph_model import OnErrorAction
                    if node.on_error == OnErrorAction.CONTINUE:
                        log.warning("Node '%s' failed but on_error is CONTINUE.", nid)
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
            log.error("Graph execution aborted: %s\n%s", exc, traceback.format_exc())
        return self._context

    def _walk(self, node_id: str | None) -> None:
        pass # Deprecated in favor of token queue

    def _execute_with_retry(self, node: AnyNode) -> NodeResult:  # type: ignore[type-arg]
        import time
        last_result = NodeResult(success=False, error="Not executed")
        
        # Use node-specific retry settings
        max_retries = node.retry_count
        retry_delay = node.retry_delay

        for attempt in range(max_retries + 1):
            if self._abort:
                raise AbortException()
                
            if attempt > 0:
                self._emit(ExecutionStatus.NODE_RETRYING,
                           node_id=node.id,
                           message=f"Retry {attempt}/{max_retries}")
                
                # Sleep in small chunks to remain responsive to abort
                remaining = retry_delay
                while remaining > 0:
                    if self._abort:
                        raise AbortException()
                    step = min(remaining, 0.1)
                    time.sleep(step)
                    remaining -= step
            
            last_result = self._dispatch(node)
            if last_result.success:
                return last_result
        return last_result

    def _dispatch(self, node: AnyNode) -> NodeResult:  # type: ignore[type-arg]
        """Route node to its executor."""
        llm_cfg = self.graph.llm_config
        ctx = self._context

        # Add abort check for executors that support it
        kwargs: dict[str, Any] = {}
        import inspect
        _executor_sig_cache: dict[Callable, inspect.Signature] = getattr(self.__class__, '_executor_sig_cache', {})
        if not hasattr(self.__class__, '_executor_sig_cache'):
            self.__class__._executor_sig_cache = _executor_sig_cache

        def _call_executor(func: Callable[..., NodeResult], *args: Any, **kwargs: Any) -> NodeResult:
            if func not in _executor_sig_cache:
                _executor_sig_cache[func] = inspect.signature(func)
            sig = _executor_sig_cache[func]
            if "abort_signal" in sig.parameters:
                kwargs["abort_signal"] = lambda: self._abort
            if "emit_info" in sig.parameters:
                kwargs["emit_info"] = lambda msg: self._emit(ExecutionStatus.NODE_INFO, node_id=node.id, node_label=node.label, message=msg)
            return func(*args, **kwargs)

        if isinstance(node, MouseNode):
            return _call_executor(execute_mouse, node, ctx)
        if isinstance(node, NavigatorNode):
            return _call_executor(execute_navigator, node, ctx)
        if isinstance(node, KeyboardNode):
            return _call_executor(execute_keyboard, node, ctx)
        if isinstance(node, ClipboardNode):
            return _call_executor(execute_clipboard, node, ctx)
        if isinstance(node, LocateAndClickNode):
            return _call_executor(execute_locate_and_click, node, ctx, dev_mode=self.config.dev_mode, llm_config=llm_cfg)
        if isinstance(node, LocateElementNode):
            return _call_executor(execute_locate_element, node, ctx, dev_mode=self.config.dev_mode, llm_config=llm_cfg)
        if isinstance(node, GenerativeOCRNode):
            return _call_executor(execute_generative_ocr, node, ctx, llm_cfg)
        if isinstance(node, LLMJudgmentNode):
            return _call_executor(execute_judgment, node, ctx, llm_cfg)
        if isinstance(node, LLMExtractionNode):
            return _call_executor(execute_extraction, node, ctx, llm_cfg)
        if isinstance(node, LLMGenerativeNode):
            return _call_executor(execute_generative, node, ctx, llm_cfg)
        if isinstance(node, WaitNode):
            return _call_executor(execute_wait, node, ctx, dev_mode=self.config.dev_mode, llm_config=llm_cfg)
        if isinstance(node, BranchNode):
            return _call_executor(execute_branch, node, ctx)
        if isinstance(node, IterateNode):
            return _call_executor(execute_iterate, node, ctx)
        if isinstance(node, DynamicIterateNode):
            return _call_executor(execute_dynamic_iterate, node, ctx)
        if isinstance(node, ForLoopNode):
            return _call_executor(execute_for_loop, node, ctx, self.graph)
        if isinstance(node, SubGraphNode):
            return self._execute_subgraph(node)
        if isinstance(node, CompareNode):
            return _call_executor(execute_compare, node, ctx)
        if isinstance(node, VisionExtractionNode):
            return _call_executor(execute_vision_extraction, node, ctx, llm_cfg)
        if isinstance(node, VisionImageNode):
            return _call_executor(execute_vision_image, node, ctx)
        if isinstance(node, WriteFileNode):
            return _call_executor(execute_write_file, node, ctx)
        if isinstance(node, CSVDataLoaderNode):
            return _call_executor(execute_csv_data_loader, node, ctx)
        if isinstance(node, CSVWriterNode):
            return _call_executor(execute_csv_writer, node, ctx)
        if isinstance(node, ScreenshotterNode):
            return _call_executor(execute_screenshotter, node, ctx)
        if isinstance(node, FileDropNode):
            return _call_executor(execute_file_drop, node, ctx)
        if isinstance(node, GlobalStartNode):
            from cognitive_automator.nodes.executors import execute_global_start
            return _call_executor(execute_global_start, node, ctx)
        if isinstance(node, GlobalEndNode):
            from cognitive_automator.nodes.executors import execute_global_end
            return _call_executor(execute_global_end, node, ctx)

        return NodeResult(success=False, error=f"Unknown node type: {type(node).__name__}")

    def _execute_subgraph(self, node: SubGraphNode) -> NodeResult:
        from cognitive_automator.serializer import load_graph
        try:
            sub_graph = load_graph(node.sub_graph_path)
            sub_config = ExecutionConfig(
                initial_context={
                    k: self._context.get(v, "")
                    for k, v in node.input_mapping.items()
                }
            )
            sub_executor = GraphExecutor(sub_graph, sub_config, self.on_event)
            sub_context = sub_executor.run()
            # Map outputs back
            for out_key, ctx_key in node.output_mapping.items():
                if out_key in sub_context:
                    self._context[ctx_key] = sub_context[out_key]
            return NodeResult(success=True)
        except Exception as exc:
            return NodeResult(success=False, error=str(exc))

    def _get_next_node(self, node_id: str, preferred_label: EdgeLabel) -> str | None:
        G = self.graph.to_nx()
        successors = list(G.successors(node_id))
        if not successors:
            return None
        # Find edge matching preferred label
        for succ in successors:
            edge_data = G.get_edge_data(node_id, succ, {})
            if edge_data.get("label") == preferred_label.value:
                return succ
        # Fall back to DEFAULT
        for succ in successors:
            edge_data = G.get_edge_data(node_id, succ, {})
            if edge_data.get("label") == EdgeLabel.DEFAULT.value:
                return succ
        # Last resort: first successor
        return successors[0]

    def _emit(self, status: ExecutionStatus, node_id: str = "",
              node_label: str = "", message: str = "") -> None:
        event = ExecutionEvent(
            status=status,
            node_id=node_id,
            node_label=node_label,
            message=message,
            context_snapshot=dict(self._context),
        )
        try:
            self.on_event(event)
        except Exception:  # noqa: BLE001
            pass   # Never let callback crash the executor


class AbortException(Exception):
    pass
