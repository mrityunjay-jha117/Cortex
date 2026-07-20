"""
=============================================================================
 OCR.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cognitive_automator.graph_model import GenerativeOCRNode

class OCRMixin:
    def _build_ocr(self, node: GenerativeOCRNode) -> None:
        bbox_str = f"{node.bbox[0]},{node.bbox[1]},{node.bbox[2]},{node.bbox[3]}"
        def set_bbox(v: str) -> None:
            parts = [int(x.strip()) for x in v.split(",") if x.strip()]
            if len(parts) == 4:
                self._set(node, "bbox", tuple(parts)) # type: ignore
        self._form_layout.addRow("BBox (L,T,R,B)", self._line_edit(bbox_str, set_bbox)) # type: ignore
        self._form_layout.addRow("Model", self._line_edit(node.model, lambda v: self._set(node, "model", v))) # type: ignore
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        self._form_layout.addRow("System Prompt", self._plain_text(node.system_prompt, lambda v: self._set(node, "system_prompt", v))) # type: ignore
