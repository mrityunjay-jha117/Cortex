"""
=============================================================================
 DISPATCH.PY (engine_components)
=============================================================================
This module is a microservice component for engine_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import logging
import inspect
from typing import Any
from cortex.graph_model import AnyNode, SubGraphNode
from cortex.nodes.executors import NodeResult
from ..registry import EXECUTOR_REGISTRY
from ..models import AbortException, ExecutionStatus

log = logging.getLogger(__name__)

class DispatchMixin:
    def _execute_with_retry(self, node: AnyNode) -> NodeResult:
        import time
        last_result = NodeResult(success=False, error="Not executed")
        max_retries = node.retry_count
        retry_delay = node.retry_delay

        for attempt in range(max_retries + 1):
            if self._abort: raise AbortException() # type: ignore
            if attempt > 0:
                self._emit(ExecutionStatus.NODE_RETRYING, node_id=node.id, message=f"Retry {attempt}/{max_retries}") # type: ignore
                remaining = retry_delay
                while remaining > 0:
                    if self._abort: raise AbortException() # type: ignore
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
        
        if "abort_signal" in sig.parameters: kwargs["abort_signal"] = lambda: self._abort # type: ignore
        if "emit_info" in sig.parameters: kwargs["emit_info"] = lambda msg: self._emit(ExecutionStatus.NODE_INFO, node_id=node.id, node_label=node.label, message=msg) # type: ignore
        if "dev_mode" in sig.parameters: kwargs["dev_mode"] = self.config.dev_mode # type: ignore
        if "llm_config" in sig.parameters: kwargs["llm_config"] = self.graph.llm_config # type: ignore
        if "graph" in sig.parameters: kwargs["graph"] = self.graph # type: ignore
        
        return func(node, self._context, **kwargs) # type: ignore

    def _execute_subgraph(self, node: SubGraphNode) -> NodeResult:
        from cortex.serializer.file_io.load import load_graph
        try:
            sub_graph = load_graph(node.sub_graph_path)
            from cortex.runtime.engine import GraphExecutor # break circular import
            sub_config = self.config.__class__( # type: ignore
                initial_context={k: self._context.get(v, "") for k, v in node.input_mapping.items()} # type: ignore
            )
            sub_executor = GraphExecutor(sub_graph, sub_config, self.on_event) # type: ignore
            sub_context = sub_executor.run()
            for out_key, ctx_key in node.output_mapping.items():
                if out_key in sub_context:
                    self._context[ctx_key] = sub_context[out_key] # type: ignore
            return NodeResult(success=True)
        except Exception as exc:
            return NodeResult(success=False, error=str(exc))
