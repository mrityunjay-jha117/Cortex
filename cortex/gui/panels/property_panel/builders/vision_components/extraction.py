"""
=============================================================================
 EXTRACTION.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import json
from cortex.graph_model import VisionExtractionNode

class VisionExtractionMixin:
    def _build_vision_extraction(self, node: VisionExtractionNode) -> None:
        bbox_str = f"{node.bbox[0]},{node.bbox[1]},{node.bbox[2]},{node.bbox[3]}"
        def set_bbox(v: str) -> None:
            parts = [int(x.strip()) for x in v.split(",") if x.strip()]
            if len(parts) == 4:
                self._set(node, "bbox", tuple(parts)) # type: ignore
        self._form_layout.addRow("BBox (L,T,R,B)", self._line_edit(bbox_str, set_bbox)) # type: ignore
        self._form_layout.addRow("Model", self._line_edit(node.model, lambda v: self._set(node, "model", v))) # type: ignore
        self._form_layout.addRow("Prompt", self._plain_text(node.prompt_template, lambda v: self._set(node, "prompt_template", v))) # type: ignore
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        
        schema_edit = self._plain_text( # type: ignore
            json.dumps(node.output_schema, indent=2) if node.output_schema else "{}",
            lambda v: self._set_schema(node, v) # type: ignore
        )
        self._form_layout.addRow("JSON Schema", schema_edit) # type: ignore
