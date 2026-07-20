"""
=============================================================================
 EXECUTION_GRAPH.PY (engine_components)
=============================================================================
This module is a microservice component for engine_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import GlobalStartNode

def build_adj(graph) -> dict[str, list]:
    adj = {nid: [] for nid in graph.nodes}
    for e in graph.edges:
        adj.setdefault(e.source_id, []).append(e)
    return adj

def find_back_edges(graph, adj) -> set:
    back_edges = set()
    visited = set()
    rec_stack = set()
    
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
        
    start_nodes = [nid for nid, node in graph.nodes.items() if isinstance(node, GlobalStartNode)]
    if graph.entry_node_id and graph.entry_node_id in graph.nodes:
        if graph.entry_node_id not in start_nodes:
            start_nodes.append(graph.entry_node_id)
            
    for nid in start_nodes:
        if nid not in visited:
            dfs(nid)
            
    for nid in graph.nodes:
        if nid not in visited:
            dfs(nid)
            
    return back_edges

def calculate_forward_in_degree(graph, back_edges) -> dict[str, int]:
    forward_in_degree = {nid: 0 for nid in graph.nodes}
    for e in graph.edges:
        if (e.source_id, e.target_id, e.label) not in back_edges:
            forward_in_degree[e.target_id] += 1
    return forward_in_degree
