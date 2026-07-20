"""
=============================================================================
 LOCATE_OPTIONS.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox

class LocateOptionsMixin:
    def _build_locate_options(self, node) -> None:
        if self._locate_full_pixmap: # type: ignore
            w = self._locate_full_pixmap.width() # type: ignore
            h = self._locate_full_pixmap.height() # type: ignore
            
            def on_x_offset(v: int) -> None:
                self._set(node, "x_offset", v) # type: ignore
                self._refresh_locate_preview(node) # type: ignore
                x_val_label.setText(str(v))

            x_row = QWidget()
            x_layout = QHBoxLayout(x_row)
            x_layout.setContentsMargins(0,0,0,0)
            x_slider = self._slider(node.x_offset, -w//2, w//2, on_x_offset) # type: ignore
            x_val_label = QLabel(str(node.x_offset))
            x_val_label.setFixedWidth(30)
            x_layout.addWidget(x_slider)
            x_layout.addWidget(x_val_label)
            self._form_layout.addRow("X Offset", x_row) # type: ignore

            def on_y_offset(v: int) -> None:
                self._set(node, "y_offset", v) # type: ignore
                self._refresh_locate_preview(node) # type: ignore
                y_val_label.setText(str(v))

            y_row = QWidget()
            y_layout = QHBoxLayout(y_row)
            y_layout.setContentsMargins(0,0,0,0)
            y_slider = self._slider(node.y_offset, -h//2, h//2, on_y_offset) # type: ignore
            y_val_label = QLabel(str(node.y_offset))
            y_val_label.setFixedWidth(30)
            y_layout.addWidget(y_slider)
            y_layout.addWidget(y_val_label)
            self._form_layout.addRow("Y Offset", y_row) # type: ignore

        self._form_layout.addRow("Confidence", self._dspin( # type: ignore
            node.confidence, 0.5, 1.0, lambda v: self._set(node, "confidence", v), step=0.05 # type: ignore
        ))
        grayscale_cb = QCheckBox()
        grayscale_cb.setChecked(node.grayscale)
        grayscale_cb.toggled.connect(lambda v: self._set(node, "grayscale", v)) # type: ignore
        self._form_layout.addRow("Grayscale", grayscale_cb) # type: ignore

        find_all_cb = QCheckBox()
        find_all_cb.setChecked(node.find_all)
        find_all_cb.setToolTip(
            "Find ALL matches on screen and click each one.\n"
            "Useful for lists where multiple identical buttons exist."
        )
        find_all_cb.toggled.connect(lambda v: self._set(node, "find_all", v)) # type: ignore
        self._form_layout.addRow("Find All", find_all_cb) # type: ignore

        self._form_layout.addRow("Timeout (s)", self._dspin(node.timeout_seconds, 1.0, 120.0, lambda v: self._set(node, "timeout_seconds", v))) # type: ignore
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        
        self._add_section("AI Fallback") # type: ignore
        fallback_cb = QCheckBox()
        fallback_cb.setChecked(node.use_fallback)
        fallback_cb.toggled.connect(lambda v: [self._set(node, "use_fallback", v), self._rebuild_form(node)]) # type: ignore
        self._form_layout.addRow("Enable AI Fallback", fallback_cb) # type: ignore

        if node.use_fallback:
            fb_edit = self._plain_text(node.fallback_prompt, lambda v: self._set(node, "fallback_prompt", v)) # type: ignore
            fb_edit.setMaximumHeight(60)
            self._form_layout.addRow("AI Search Prompt", fb_edit) # type: ignore

            self._form_layout.addRow("Model Override", self._line_edit(node.fallback_model_override or "", lambda v: self._set(node, "fallback_model_override", v if v else None))) # type: ignore
            self._add_hint("Describe the element (e.g. 'blue login button'). Only runs if primary image match fails.") # type: ignore
            
            self._form_layout.addRow("Auto-Heal", self._toggle(node.auto_heal, lambda v: self._set(node, "auto_heal", v))) # type: ignore
            self._add_hint("Automatically update coordinates and image if AI succeeds.") # type: ignore
