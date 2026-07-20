"""
=============================================================================
 SCENE_STATE.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

class SceneStateMixin:
    def refresh_edges(self) -> None:
        for edge_item in self._edge_items: # type: ignore
            edge_item.update_path()

    def get_node_item(self, node_id: str):
        return self._node_items.get(node_id) # type: ignore

    def set_node_executing(self, node_id: str) -> None:
        for nid, item in self._node_items.items(): # type: ignore
            if nid == node_id:
                item.set_executing(True)

    def set_node_result(self, node_id: str, success: bool) -> None:
        if node_id in self._node_items: # type: ignore
            self._node_items[node_id].set_result(success) # type: ignore

    def reset_all_states(self) -> None:
        for item in self._node_items.values(): # type: ignore
            item.reset_state()
