"""
=============================================================================
 LAYOUT.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import collections
from cognitive_automator.gui.canvas.base import NODE_W, NODE_H

def auto_layout_graph(scene) -> None:
    """BFS layered layout — fires only when all nodes sit at the default (0, 0)."""
    if not scene._graph or not scene._node_items:
        return
    if not all(abs(n.x) < 1 and abs(n.y) < 1 for n in scene._graph.nodes.values()):
        return

    node_ids = list(scene._graph.nodes.keys())
    entry = scene._graph.entry_node_id or (node_ids[0] if node_ids else None)
    if not entry:
        return

    # BFS from entry to assign a layer (column) to each node
    layers: dict[str, int] = {}
    queue: collections.deque[tuple[str, int]] = collections.deque([(entry, 0)])
    visited = {entry}
    while queue:
        nid, layer = queue.popleft()
        layers[nid] = layer
        for edge in scene._graph.edges:
            if edge.source_id == nid and edge.target_id not in visited:
                visited.add(edge.target_id)
                queue.append((edge.target_id, layer + 1))

    # Disconnected nodes land in column 0
    for nid in node_ids:
        layers.setdefault(nid, 0)

    # Group nodes by layer and assign positions
    layer_groups: dict[int, list[str]] = collections.defaultdict(list)
    for nid, layer in layers.items():
        layer_groups[layer].append(nid)

    H_STEP = NODE_W + 80
    V_STEP = NODE_H + 40
    OFFSET_X = 60
    OFFSET_Y = 60

    for layer, nids in layer_groups.items():
        for i, nid in enumerate(nids):
            x = OFFSET_X + layer * H_STEP
            y = OFFSET_Y + i * V_STEP
            scene._graph.nodes[nid].x = x
            scene._graph.nodes[nid].y = y
            scene._node_items[nid].setPos(x, y)

    scene.refresh_edges()
