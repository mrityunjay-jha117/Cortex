"""
recorder/translator.py — Translates raw OS events into ActionGraph nodes.

Key behaviours:
- Consecutive key presses within 200ms collapse into a single KeyboardNode(typewrite)
- ctrl+c after a click → ClipboardNode(read)
- Hotkeys (ctrl+v, ctrl+a, etc.) → KeyboardNode(hotkey)
- Only mouse button-press events (not release) become MouseNodes
"""

from __future__ import annotations

import logging
from typing import Sequence

from cognitive_automator.graph_model import (
    ActionGraph,
    BaseNode,
    ClipboardAction,
    ClipboardNode,
    EdgeLabel,
    KeyboardAction,
    KeyboardNode,
    MouseAction,
    MouseNode,
)
from cognitive_automator.recorder.hooker import RawEvent, RawEventType
from cognitive_automator.serializer import new_graph

log = logging.getLogger(__name__)

# Keys treated as modifiers (never collapsed into typewrite text)
_MODIFIER_KEYS = frozenset({"ctrl", "shift", "alt", "cmd", "meta", "fn"})
# Max gap between keystrokes to collapse into a single typewrite
_TYPEWRITE_COLLAPSE_MS = 200


def translate_events(events: Sequence[RawEvent | BaseNode], graph_name: str = "Recorded Automation") -> ActionGraph:
    """
    Convert a list of RawEvents and BaseNodes into an ActionGraph.
    Nodes are added in recording order and connected sequentially.
    """
    graph = new_graph(graph_name)
    prev_node_id: str | None = None

    def add_node(node: BaseNode) -> None:
        nonlocal prev_node_id
        graph.add_node(node)
        if prev_node_id is not None:
            graph.add_edge(prev_node_id, node.id, EdgeLabel.DEFAULT)
        prev_node_id = node.id

    i = 0
    pending_keys: list[str] = []
    pending_start_ts: float | None = None

    def flush_pending_keys() -> None:
        nonlocal pending_keys, pending_start_ts
        if not pending_keys:
            return
        text = "".join(pending_keys)
        node = KeyboardNode(
            action=KeyboardAction.TYPEWRITE,
            text=text,
            label=f'Type "{text[:20]}{"…" if len(text) > 20 else ""}"',
            interval=0.01,
        )
        add_node(node)
        pending_keys = []
        pending_start_ts = None

    while i < len(events):
        ev = events[i]

        # ── Pre-existing Node (Injected)
        if isinstance(ev, BaseNode):
            flush_pending_keys()
            add_node(ev)
            i += 1
            continue

        # ── Raw Event (Hooked)
        if isinstance(ev, RawEvent):
            # ── Control hotkeys
            if ev.type.startswith("hotkey_"):
                flush_pending_keys()
                i += 1
                continue

            # ── Mouse scroll
            if ev.type == RawEventType.MOUSE_SCROLL:
                flush_pending_keys()
                total_dy = 0
                while i < len(events) and isinstance(events[i], RawEvent) and events[i].type == RawEventType.MOUSE_SCROLL:
                    total_dy += events[i].scroll_dy
                    i += 1
                
                amount = int(total_dy * 120)
                if amount != 0:
                    node = MouseNode(
                        action=MouseAction.SCROLL,
                        x_coord=ev.x,
                        y_coord=ev.y,
                        scroll_amount=amount,
                        label=f"Scroll {'Up' if amount > 0 else 'Down'} ({abs(amount)})",
                    )
                    add_node(node)
                continue

            # ── Mouse click
            if ev.type == RawEventType.MOUSE_CLICK and ev.pressed:
                flush_pending_keys()

                # Peek: if next meaningful events are ctrl+c, make it a ClipboardNode
                if _is_ctrl_c_ahead(events, i + 1):
                    node = ClipboardNode(
                        action=ClipboardAction.READ,
                        label="Read Clipboard (Ctrl+C)",
                    )
                    add_node(node)
                    # Skip the ctrl+c events
                    i = _skip_ctrl_c(events, i + 1)
                    continue

                action_map = {
                    "left": MouseAction.CLICK,
                    "right": MouseAction.RIGHT_CLICK,
                }
                action = action_map.get(ev.button, MouseAction.CLICK)
                node = MouseNode(
                    action=action,
                    x_coord=ev.x,
                    y_coord=ev.y,
                    label=f"{action.value.replace('_', ' ').title()} ({ev.x}, {ev.y})",
                )
                add_node(node)
                i += 1
                continue

            # ── Key press
            if ev.type == RawEventType.KEY_PRESS:
                key = ev.key

                # Modifier-only press (ctrl, shift, etc.) — skip unless it's a hotkey
                if key in _MODIFIER_KEYS:
                    i += 1
                    continue

                # Check for hotkey: modifier + key (e.g. ctrl+v)
                hotkey = _detect_hotkey(events, i)
                if hotkey:
                    flush_pending_keys()
                    # Map standard hotkeys to dedicated actions
                    modifier = "command" if "cmd" in hotkey else "ctrl"
                    if set(hotkey) == {modifier, "a"}:
                        node = KeyboardNode(
                            action=KeyboardAction.SELECT_ALL,
                            label="Select All",
                        )
                    else:
                        node = KeyboardNode(
                            action=KeyboardAction.HOTKEY,
                            keys=hotkey,
                            label="+".join(hotkey),
                        )
                    add_node(node)
                    i = _skip_hotkey(events, i, hotkey)
                    continue

                # Regular printable character — collapse into typewrite
                if len(key) == 1:
                    now = ev.timestamp
                    if pending_start_ts and (now - pending_start_ts) * 1000 > _TYPEWRITE_COLLAPSE_MS:
                        flush_pending_keys()
                    pending_keys.append(key)
                    pending_start_ts = pending_start_ts or now
                    i += 1
                    continue

                # Special key (enter, tab, backspace…)
                flush_pending_keys()
                node = KeyboardNode(
                    action=KeyboardAction.PRESS,
                    key=key,
                    label=f"Press {key}",
                )
                add_node(node)
                i += 1
                continue

        i += 1

    flush_pending_keys()
    return graph


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_ctrl_c_ahead(events: Sequence[RawEvent | BaseNode], start: int) -> bool:
    """Return True if the next 2 press events are ctrl then c."""
    presses = [e for e in events[start:start + 6]
               if isinstance(e, RawEvent) and e.type == RawEventType.KEY_PRESS]
    keys = [e.key for e in presses[:2]]
    return set(keys) == {"ctrl", "c"}


def _skip_ctrl_c(events: Sequence[RawEvent | BaseNode], start: int) -> int:
    """Advance index past the ctrl+c events."""
    found = 0
    i = start
    while i < len(events) and found < 4:
        ev = events[i]
        if isinstance(ev, RawEvent) and \
           ev.type in (RawEventType.KEY_PRESS, RawEventType.KEY_RELEASE) and \
           ev.key in ("ctrl", "c"):
            found += 1
        i += 1
    return i


def _detect_hotkey(events: Sequence[RawEvent | BaseNode], start: int) -> list[str] | None:
    """
    Look backwards at currently-held modifier keys + this key.
    Returns list like ["ctrl", "v"] if it's a hotkey, else None.
    """
    ev = events[start]
    if not isinstance(ev, RawEvent):
        return None
    
    held_modifiers: list[str] = []
    # Walk backwards to find modifier presses without intervening releases
    for j in range(start - 1, max(start - 10, -1), -1):
        prev = events[j]
        if not isinstance(prev, RawEvent):
            continue
        if prev.type == RawEventType.KEY_RELEASE:
            break
        if prev.type == RawEventType.KEY_PRESS and prev.key in _MODIFIER_KEYS:
            held_modifiers.insert(0, prev.key)
    if held_modifiers and ev.key not in _MODIFIER_KEYS:
        return held_modifiers + [ev.key]
    return None


def _skip_hotkey(events: Sequence[RawEvent | BaseNode], start: int, hotkey: list[str]) -> int:
    """Skip past the hotkey key releases."""
    remaining = set(hotkey)
    i = start + 1
    while i < len(events) and remaining:
        ev = events[i]
        if isinstance(ev, RawEvent) and ev.type == RawEventType.KEY_RELEASE and ev.key in remaining:
            remaining.discard(ev.key)
        i += 1
    return i
