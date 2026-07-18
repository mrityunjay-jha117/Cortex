"""
gui/widgets/recording_overlay.py — Always-on-top transparent overlay widget.

Shows during training/recording session:
- Status indicator (recording / paused)
- Node count + elapsed time
- Pause, Add Logic Node, Stop buttons
- Capture Image  → ScreenRegionSelector → LocateElementNode + MouseNode (single click)
- Extract Data   → DataExtractionDialog  → ClipboardNode + LLMExtractionNode
- Image Loop     → ScreenRegionSelector → LocateAll + DynamicIterateNode + body recording
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from cognitive_automator.graph_model import (
    ActionGraph, EdgeLabel,
)
from cognitive_automator.recorder.hooker import EventHooker, RawEventType
from cognitive_automator.recorder.translator import translate_events
from cognitive_automator.serializer import new_graph


# ---------------------------------------------------------------------------
# Helpers for graph assembly
# ---------------------------------------------------------------------------

def _merge(main: ActionGraph, sub: ActionGraph) -> None:
    """Copy all nodes and edges from sub into main (mutates main in-place)."""
    for nid, node in sub.nodes.items():
        main.nodes[nid] = node
        if main.entry_node_id is None:
            main.entry_node_id = nid
    for edge in sub.edges:
        main.edges.append(edge)


def _sub_tail(sub: ActionGraph) -> str | None:
    """Return the last node in sub that has no outgoing DEFAULT edge."""
    if not sub.nodes:
        return None
    sourced = {e.source_id for e in sub.edges if e.label == EdgeLabel.DEFAULT}
    for nid in reversed(list(sub.nodes)):
        if nid not in sourced:
            return nid
    return list(sub.nodes)[-1]


# ---------------------------------------------------------------------------
# Overlay widget
# ---------------------------------------------------------------------------

class RecordingOverlay(QWidget):
    """
    Minimal always-on-top overlay displayed while recording.
    Transparent background, no window frame, stays above all windows.
    """
    recording_finished = pyqtSignal(object)   # ActionGraph

    def __init__(self, automation_name: str = "Recorded Automation",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = automation_name
        self._hooker = EventHooker()
        self._start_time = time.monotonic()
        self._paused = False
        self._chronological_stream: list[Any] = [] # Stores both RawEvent and BaseNode

        # Loop tracking state
        self._loop_ranges: list[dict] = []
        self._current_loop: dict | None = None   # {"start_idx", "locate", "iter", "click"}
        self._csv_loop_ranges: list[dict] = []
        self._current_csv_loop: dict | None = None   # {"type", "start_idx", "iter"}

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 205)

        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.move(geo.right() - 300, geo.top() + 40)

        self._build_ui()
        self._hooker.start()

        self._event_poll_timer = QTimer(self)
        self._event_poll_timer.timeout.connect(self._check_events)
        self._event_poll_timer.start(100)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(500)

    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QWidget#overlay {
                background-color: rgba(13, 14, 24, 220);
                border: 1px solid #7B61FF;
                border-radius: 10px;
            }
            QPushButton {
                background-color: rgba(30, 30, 50, 200);
                color: #E0E0F0;
                border: 1px solid #2A2B3A;
                border-radius: 5px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7B61FF;
                border-color: #7B61FF;
            }
        """)

        container = QWidget(self)
        container.setObjectName("overlay")
        container.setGeometry(0, 0, 280, 205)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        # Header row
        header_row = QHBoxLayout()
        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #FF4444; font-size: 14px;")
        header_row.addWidget(self._dot)

        title = QLabel("RECORDING")
        title.setStyleSheet("color: #E0E0F0; font-size: 11px; font-weight: bold; letter-spacing: 2px;")
        header_row.addWidget(title)
        header_row.addStretch()

        self._timer_label = QLabel("00:00")
        self._timer_label.setStyleSheet("color: #7B61FF; font-size: 12px; font-family: 'Consolas';")
        header_row.addWidget(self._timer_label)
        layout.addLayout(header_row)

        # Stats row
        self._stats_label = QLabel("0 events queued")
        self._stats_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._stats_label)

        # Row 1: Pause / Logic / Stop
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(5)

        self._pause_btn = QPushButton("⏸ Pause")
        self._pause_btn.setToolTip("Toggle Pause/Resume (Ctrl+Alt+P)")
        self._pause_btn.clicked.connect(self._toggle_pause)
        btn_row1.addWidget(self._pause_btn)

        logic_btn = QPushButton("＋ Logic")
        logic_btn.setToolTip("Add an LLM Logic node (Ctrl+Alt+Space)")
        logic_btn.clicked.connect(self._add_logic_node)
        btn_row1.addWidget(logic_btn)

        stop_btn = QPushButton("⏹ Stop")
        stop_btn.setToolTip("Stop recording and save (Ctrl+Alt+S)")
        stop_btn.setStyleSheet("background: rgba(255,100,100,180); border-color: #FF6B6B; color: white;")
        stop_btn.clicked.connect(self._stop_recording)
        btn_row1.addWidget(stop_btn)
        layout.addLayout(btn_row1)

        # Row 2: Capture Image / Extract Data
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(5)

        capture_btn = QPushButton("📷 Capture Image")
        capture_btn.setToolTip(
            "Draw a region on screen — creates an Image Search node. (Ctrl+Alt+I)\n"
            "At run-time PyAutoGUI will locate that image and click it."
        )
        capture_btn.setStyleSheet("background: rgba(0,100,80,200); border-color: #00C9A7; color: #E0E0F0;")
        capture_btn.clicked.connect(self._start_image_capture)
        btn_row2.addWidget(capture_btn)

        extract_btn = QPushButton("🔍 Extract Data")
        extract_btn.setToolTip(
            "Read clipboard text and extract structured data with an LLM. (Ctrl+Alt+D)\n"
            "Creates ClipboardRead + LLMExtraction nodes."
        )
        extract_btn.setStyleSheet("background: rgba(60,40,120,200); border-color: #7B61FF; color: #E0E0F0;")
        extract_btn.clicked.connect(self._add_extraction_nodes)
        btn_row2.addWidget(extract_btn)
        layout.addLayout(btn_row2)

        # Row 3: Image Loop | CSV Loop
        btn_row3 = QHBoxLayout()
        btn_row3.setSpacing(5)

        self._loop_btn = QPushButton("🔄 Image Loop")
        self._loop_btn.setToolTip(
            "Capture a reference image — the runtime finds ALL matches (Ctrl+Alt+L)\n"
            "and executes your recorded body for EACH one.\n"
            "Click again to mark the end of the loop body."
        )
        self._loop_btn.setStyleSheet("background: rgba(80,60,0,200); border-color: #FFC107; color: #E0E0F0;")
        self._loop_btn.clicked.connect(self._toggle_image_loop)
        btn_row3.addWidget(self._loop_btn)

        self._csv_loop_btn = QPushButton("📋 CSV Loop")
        self._csv_loop_btn.setToolTip(
            "Select a CSV or Excel file — the runtime iterates over each row (Ctrl+Alt+C)\n"
            "and executes your recorded body once per row.\n"
            "Click again to mark the end of the loop body."
        )
        self._csv_loop_btn.setStyleSheet("background: rgba(0,60,120,200); border-color: #4CAFFF; color: #E0E0F0;")
        self._csv_loop_btn.clicked.connect(self._toggle_csv_loop)
        btn_row3.addWidget(self._csv_loop_btn)

        layout.addLayout(btn_row3)

        # Hint
        hint = QLabel("Ctrl+Alt + P: Pause | S: Stop | Space: Logic | I: Image | D: Data | L: Loop | C: CSV")
        hint.setStyleSheet("color: #777; font-size: 8px;")
        layout.addWidget(hint)

        # Dot blink timer
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_dot)
        self._blink_timer.start(600)
        self._dot_on = True

    # ------------------------------------------------------------------
    # Clock / stats
    # ------------------------------------------------------------------

    def _blink_dot(self) -> None:
        if not self._paused:
            self._dot_on = not self._dot_on
            self._dot.setStyleSheet(
                f"color: {'#FF4444' if self._dot_on else 'transparent'}; font-size: 14px;"
            )

    def _update_clock(self) -> None:
        if self._paused:
            return
        elapsed = int(time.monotonic() - self._start_time)
        m, s = divmod(elapsed, 60)
        self._timer_label.setText(f"{m:02d}:{s:02d}")
        self._stats_label.setText(f"{self._hooker.event_queue.qsize()} events queued")

    # ------------------------------------------------------------------
    # Recording controls
    # ------------------------------------------------------------------

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        if self._paused:
            self._pause_btn.setText("▶ Resume")
            self._dot.setStyleSheet("color: #FFC107; font-size: 14px;")
        else:
            self._pause_btn.setText("⏸ Pause")
            self._dot.setStyleSheet("color: #FF4444; font-size: 14px;")

    def _check_events(self) -> None:
        dpr = self.devicePixelRatioF()
        for ev in self._hooker.drain():
            if ev.type == RawEventType.HOTKEY_INTERRUPT:
                self._add_logic_node()
            elif ev.type == RawEventType.HOTKEY_PAUSE:
                self._toggle_pause()
            elif ev.type == RawEventType.HOTKEY_STOP:
                self._stop_recording()
            elif ev.type == RawEventType.HOTKEY_CAPTURE:
                self._start_image_capture()
            elif ev.type == RawEventType.HOTKEY_EXTRACT:
                self._add_extraction_nodes()
            elif ev.type == RawEventType.HOTKEY_LOOP:
                self._toggle_image_loop()
            elif ev.type == RawEventType.HOTKEY_CSV_LOOP:
                self._toggle_csv_loop()
            elif not self._paused:
                # pynput coordinates are physical on Windows when process is DPI aware.
                # Only scale if we are on other platforms that might still use logical.
                if ev.type in (RawEventType.MOUSE_CLICK, RawEventType.MOUSE_MOVE, RawEventType.MOUSE_SCROLL):
                    import sys
                    if sys.platform != "win32":
                        ev.x = int(ev.x * dpr)
                        ev.y = int(ev.y * dpr)
                self._chronological_stream.append(ev)

    # ------------------------------------------------------------------
    # Logic node injection
    # ------------------------------------------------------------------

    def _add_logic_node(self) -> None:
        from cognitive_automator.gui.widgets.logic_inject_dialog import LogicInjectDialog
        dialog = LogicInjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            node = dialog.get_node()
            if node:
                self._chronological_stream.append(node)

    # ------------------------------------------------------------------
    # Image capture (single click)
    # ------------------------------------------------------------------

    def _start_image_capture(self) -> None:
        was_paused = self._paused
        self._paused = True
        self.hide()

        from cognitive_automator.gui.widgets.screen_region_selector import ScreenRegionSelector
        self._selector = ScreenRegionSelector()
        self._selector.region_selected.connect(
            lambda r, cp: self._on_region_captured(r, cp, was_paused)
        )
        self._selector.cancelled.connect(lambda: self._on_capture_cancelled(was_paused))
        QTimer.singleShot(150, self._selector.show)
        QTimer.singleShot(200, self._selector.activateWindow)

    def _on_region_captured(self, rect: Any, click_point: Any, was_paused: bool) -> None:
        QTimer.singleShot(500, lambda: self._finish_capture(rect, click_point, was_paused))

    def _finish_capture(self, rect: Any, click_point: Any, was_paused: bool) -> None:
        try:
            import tempfile
            import os
            import pyautogui  # type: ignore
            from cognitive_automator.graph_model import LocateElementNode, MouseNode, MouseAction

            dpr = self.devicePixelRatioF()
            x = int(rect.left() * dpr)
            y = int(rect.top() * dpr)
            w = int(rect.width() * dpr)
            h = int(rect.height() * dpr)

            # Calculate relative offset if a custom click point was picked
            # We scale these by DPR to ensure they are stored as physical pixels
            off_x, off_y = 0, 0
            if click_point:
                lcx, lcy = rect.center().x(), rect.center().y()
                off_x = int((click_point.x() - lcx) * dpr)
                off_y = int((click_point.y() - lcy) * dpr)

            time.sleep(0.5)  # Let UI settle completely
            img = pyautogui.screenshot(region=(x, y, w, h))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            capture_idx = sum(1 for n in self._chronological_stream if hasattr(n, "reference_image_b64"))
            output_key = f"image_pos_{capture_idx}" if capture_idx else "image_pos"

            locate_node = LocateElementNode(
                label="Image Search",
                reference_image_b64=img_b64,
                confidence=0.75,
                grayscale=False,
                output_key=output_key,
            )
            click_node = MouseNode(
                label="Click Image",
                action=MouseAction.CLICK,
                vision_node_id=output_key,
                x_offset=off_x,
                y_offset=off_y,
            )

            self._chronological_stream.append(locate_node)
            self._chronological_stream.append(click_node)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(base64.b64decode(img_b64))
                tmp_path = f.name
            try:
                loc = pyautogui.locateOnScreen(tmp_path, confidence=0.75, grayscale=False)
                if loc is not None:
                    cx, cy = pyautogui.center(loc)
                    # Apply offsets to immediate click
                    cx += off_x
                    cy += off_y
                    time.sleep(0.5)  # Delay before perform as requested
                    pyautogui.click(cx, cy)
                    time.sleep(0.15)
                    self._hooker.drain()
                    self._stats_label.setText(f"Image found & clicked at ({cx},{cy}) ✓")
                else:
                    self._stats_label.setText("Image captured (not found on screen yet — will retry at play-time)")
            finally:
                os.unlink(tmp_path)
        except Exception as exc:
            self._stats_label.setText(f"Capture failed: {exc}")
        finally:
            self._paused = was_paused
            self.show()

    def _on_capture_cancelled(self, was_paused: bool) -> None:
        self._paused = was_paused
        self.show()

    # ------------------------------------------------------------------
    # Image Loop
    # ------------------------------------------------------------------

    def _toggle_image_loop(self) -> None:
        if self._current_loop is None:
            self._start_image_loop()
        else:
            self._end_image_loop()

    def _start_image_loop(self) -> None:
        was_paused = self._paused
        self._paused = True
        self.hide()

        from cognitive_automator.gui.widgets.screen_region_selector import ScreenRegionSelector
        self._loop_selector = ScreenRegionSelector()
        self._loop_selector.region_selected.connect(
            lambda r, cp: self._on_loop_region_captured(r, cp, was_paused)
        )
        self._loop_selector.cancelled.connect(lambda: self._on_capture_cancelled(was_paused))
        QTimer.singleShot(150, self._loop_selector.show)
        QTimer.singleShot(200, self._loop_selector.activateWindow)

    def _on_loop_region_captured(self, rect: Any, click_point: Any, was_paused: bool) -> None:
        QTimer.singleShot(500, lambda: self._finish_loop_capture(rect, click_point, was_paused))

    def _finish_loop_capture(self, rect: Any, click_point: Any, was_paused: bool) -> None:
        try:
            import tempfile
            import os
            import pyautogui  # type: ignore
            from cognitive_automator.graph_model import (
                DynamicIterateNode, LocateElementNode, MouseNode, MouseAction,
            )

            dpr = self.devicePixelRatioF()
            x = int(rect.left() * dpr)
            y = int(rect.top() * dpr)
            w = int(rect.width() * dpr)
            h = int(rect.height() * dpr)

            off_x, off_y = 0, 0
            if click_point:
                lcx, lcy = rect.center().x(), rect.center().y()
                off_x = int((click_point.x() - lcx) * dpr)
                off_y = int((click_point.y() - lcy) * dpr)

            time.sleep(0.5)  # Let UI settle completely
            img = pyautogui.screenshot(region=(x, y, w, h))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            loop_idx = len(self._loop_ranges)
            output_key = f"loop_matches_{loop_idx}" if loop_idx else "loop_matches"
            item_key = f"loop_item_{loop_idx}" if loop_idx else "loop_item"

            locate_node = LocateElementNode(
                label="Find All (Loop)",
                reference_image_b64=img_b64,
                confidence=0.75,
                grayscale=False,
                find_all=True,
                output_key=output_key,
            )
            iter_node = DynamicIterateNode(
                label="For Each Match",
                source_key=output_key,
                output_key=item_key,
            )
            click_node = MouseNode(
                label="Click Match",
                action=MouseAction.CLICK,
                vision_node_id=item_key,
                x_offset=off_x,
                y_offset=off_y,
            )

            # Preview: show how many matches exist right now
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(base64.b64decode(img_b64))
                tmp_path = f.name
            try:
                matches = list(pyautogui.locateAllOnScreen(tmp_path, confidence=0.75, grayscale=False))
                count_msg = f"{len(matches)} matches found" if matches else "no matches found yet"
            finally:
                os.unlink(tmp_path)

            self._current_loop = {
                "start_idx": len(self._chronological_stream),
                "locate": locate_node,
                "iter": iter_node,
                "click": click_node,
            }

            self._loop_btn.setText("⏹ End Loop Body")
            self._loop_btn.setStyleSheet(
                "background: rgba(200,120,0,220); border-color: #FFC107; color: white; font-weight: bold;"
            )
            self._stats_label.setText(f"Loop started — {count_msg}. Record body actions now.")
        except Exception as exc:
            self._current_loop = None
            self._stats_label.setText(f"Loop capture failed: {exc}")
        finally:
            self._paused = was_paused
            self.show()

    def _end_image_loop(self) -> None:
        if self._current_loop is None:
            return
        self._current_loop["end_idx"] = len(self._chronological_stream)
        self._loop_ranges.append(self._current_loop)
        self._current_loop = None
        self._loop_btn.setText("🔄 Image Loop")
        self._loop_btn.setStyleSheet(
            "background: rgba(80,60,0,200); border-color: #FFC107; color: #E0E0F0;"
        )
        self._stats_label.setText(f"Loop body captured ✓  ({len(self._loop_ranges)} loop(s) total)")

    # ------------------------------------------------------------------
    # CSV Loop
    # ------------------------------------------------------------------

    def _toggle_csv_loop(self) -> None:
        if self._current_csv_loop is None:
            self._start_csv_loop()
        else:
            self._end_csv_loop()

    def _start_csv_loop(self) -> None:
        self._paused = True
        self.hide()
        try:
            from PyQt6.QtWidgets import QFileDialog, QInputDialog
            path, _ = QFileDialog.getOpenFileName(
                None, "Select CSV or Excel file", "",
                "Data files (*.csv *.xlsx *.xls);;CSV (*.csv);;Excel (*.xlsx *.xls);;All Files (*)"
            )
            if not path:
                return

            col, ok = QInputDialog.getText(
                None, "Column Name",
                "Column name to iterate over\n(leave blank for first column):"
            )
            if not ok:
                return

            from cognitive_automator.graph_model import IterateNode
            iter_node = IterateNode(
                label=f"CSV Loop: {os.path.basename(path)}",
                csv_file_path=path,
                csv_column=col.strip(),
                output_key="csv_item",
            )
            self._current_csv_loop = {
                "type": "csv",
                "start_idx": len(self._chronological_stream),
                "iter": iter_node,
            }
            self._csv_loop_btn.setText("⏹ End CSV Loop")
            self._csv_loop_btn.setStyleSheet(
                "background: rgba(0,100,200,220); border-color: #4CAFFF; color: white; font-weight: bold;"
            )
            self._stats_label.setText(f"CSV loop: {os.path.basename(path)}. Record body now.")
        except Exception as exc:
            self._current_csv_loop = None
            self._stats_label.setText(f"CSV loop setup failed: {exc}")
        finally:
            self._paused = False
            self.show()

    def _end_csv_loop(self) -> None:
        if self._current_csv_loop is None:
            return
        self._current_csv_loop["end_idx"] = len(self._chronological_stream)
        self._csv_loop_ranges.append(self._current_csv_loop)
        self._current_csv_loop = None
        self._csv_loop_btn.setText("📋 CSV Loop")
        self._csv_loop_btn.setStyleSheet(
            "background: rgba(0,60,120,200); border-color: #4CAFFF; color: #E0E0F0;"
        )
        self._stats_label.setText(
            f"CSV loop body captured ✓  ({len(self._csv_loop_ranges)} csv loop(s) total)"
        )

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

    def _add_extraction_nodes(self) -> None:
        from cognitive_automator.gui.widgets.data_extraction_dialog import DataExtractionDialog
        dialog = DataExtractionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodes = dialog.get_nodes()
            if nodes:
                self._chronological_stream.extend(nodes)
                self._stats_label.setText("Extraction nodes added ✓")

    # ------------------------------------------------------------------
    # Stop + graph assembly
    # ------------------------------------------------------------------

    @staticmethod
    def _graph_tail(graph: ActionGraph) -> str | None:
        if not graph.nodes:
            return None
        sourced = {e.source_id for e in graph.edges if e.label == EdgeLabel.DEFAULT}
        for nid in reversed(list(graph.nodes)):
            if nid not in sourced:
                return nid
        return list(graph.nodes)[-1]

    def _stop_recording(self) -> None:
        # Auto-close any open loops
        if self._current_loop is not None:
            self._end_image_loop()
        if self._current_csv_loop is not None:
            self._end_csv_loop()

        self._hooker.stop()
        self._event_poll_timer.stop()
        self._clock_timer.stop()
        self._blink_timer.stop()

        all_loops = (
            [dict(lp, type="image") for lp in self._loop_ranges]
            + list(self._csv_loop_ranges)
        )
        graph = self._assemble_graph_with_loops(
            self._chronological_stream, all_loops, self._name
        )

        self.recording_finished.emit(graph)
        self.close()

    def _assemble_graph_with_loops(
        self,
        stream: list,
        loop_ranges: list[dict],
        name: str,
    ) -> ActionGraph:
        """
        Build a composite ActionGraph from a chronological stream of events and nodes,
        interleaved with zero or more loop regions.
        """
        if not loop_ranges:
            return translate_events(stream, name)

        main = new_graph(name)
        main.nodes.clear()
        main.edges.clear()
        main.entry_node_id = None

        cursor = 0
        prev_tail_id: str | None = None
        last_iter_id: str | None = None

        for loop_info in sorted(loop_ranges, key=lambda x: x["start_idx"]):
            start_idx = loop_info["start_idx"]
            end_idx = loop_info["end_idx"]
            iter_node = loop_info["iter"]
            loop_type = loop_info.get("type", "image")

            # --- Pre-loop events/nodes ---
            pre_stream = stream[cursor:start_idx]
            if pre_stream:
                pre_sub = translate_events(pre_stream, "")
                _merge(main, pre_sub)
                pre_entry = pre_sub.entry_node_id
                if prev_tail_id and pre_entry:
                    main.add_edge(prev_tail_id, pre_entry, EdgeLabel.DEFAULT)
                prev_tail_id = _sub_tail(pre_sub)

            body_stream = stream[start_idx:end_idx]
            body_tail_id: str | None = None

            if loop_type == "image":
                locate_node = loop_info["locate"]
                click_node = loop_info["click"]

                main.add_node(locate_node)
                if prev_tail_id:
                    main.add_edge(prev_tail_id, locate_node.id, EdgeLabel.DEFAULT)
                main.add_node(iter_node)
                main.add_edge(locate_node.id, iter_node.id, EdgeLabel.DEFAULT)
                last_iter_id = iter_node.id

                if body_stream:
                    body_sub = translate_events(body_stream, "")
                    _merge(main, body_sub)
                    body_entry = body_sub.entry_node_id
                    main.add_node(click_node)
                    main.add_edge(iter_node.id, click_node.id, EdgeLabel.LOOP_BODY)
                    if body_entry:
                        main.add_edge(click_node.id, body_entry, EdgeLabel.DEFAULT)
                    body_tail_id = _sub_tail(body_sub)
                else:
                    main.add_node(click_node)
                    main.add_edge(iter_node.id, click_node.id, EdgeLabel.LOOP_BODY)
                    body_tail_id = click_node.id

            else:  # csv
                main.add_node(iter_node)
                if prev_tail_id:
                    main.add_edge(prev_tail_id, iter_node.id, EdgeLabel.DEFAULT)
                last_iter_id = iter_node.id

                if body_stream:
                    body_sub = translate_events(body_stream, "")
                    _merge(main, body_sub)
                    body_entry = body_sub.entry_node_id
                    if body_entry:
                        main.add_edge(iter_node.id, body_entry, EdgeLabel.LOOP_BODY)
                    body_tail_id = _sub_tail(body_sub)

            if body_tail_id:
                main.add_edge(body_tail_id, iter_node.id, EdgeLabel.LOOP_BODY)

            prev_tail_id = None   # iter node is now the exit point via LOOP_END
            cursor = end_idx

        # --- Post-loop events/nodes ---
        post_stream = stream[cursor:]
        if post_stream:
            post_sub = translate_events(post_stream, "")
            _merge(main, post_sub)
            post_entry = post_sub.entry_node_id
            if last_iter_id and post_entry:
                main.add_edge(last_iter_id, post_entry, EdgeLabel.LOOP_END)
            elif prev_tail_id and post_entry:
                main.add_edge(prev_tail_id, post_entry, EdgeLabel.DEFAULT)

        return main
