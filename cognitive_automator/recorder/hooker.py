"""
recorder/hooker.py — Global OS event hooker using pynput.

Runs mouse + keyboard listeners in daemon threads.
Events are queued in a thread-safe Queue for the Translator to consume.
Ctrl+Shift+Space triggers the interrupt hotkey.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)


class RawEventType(str, Enum):
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    HOTKEY_INTERRUPT = "hotkey_interrupt"
    HOTKEY_PAUSE = "hotkey_pause"
    HOTKEY_STOP = "hotkey_stop"
    HOTKEY_CAPTURE = "hotkey_capture"
    HOTKEY_EXTRACT = "hotkey_extract"
    HOTKEY_LOOP = "hotkey_loop"
    HOTKEY_CSV_LOOP = "hotkey_csv_loop"


@dataclass
class RawEvent:
    type: RawEventType
    timestamp: float = field(default_factory=time.monotonic)
    x: int = 0
    y: int = 0
    button: str = ""
    key: str = ""
    scroll_dx: int = 0
    scroll_dy: int = 0
    pressed: bool = True


_HOTKEY_MAP = {
    frozenset({"ctrl", "alt", "space"}): RawEventType.HOTKEY_INTERRUPT,
    frozenset({"ctrl", "alt", "p"}): RawEventType.HOTKEY_PAUSE,
    frozenset({"ctrl", "alt", "s"}): RawEventType.HOTKEY_STOP,
    frozenset({"ctrl", "alt", "i"}): RawEventType.HOTKEY_CAPTURE,
    frozenset({"ctrl", "alt", "d"}): RawEventType.HOTKEY_EXTRACT,
    frozenset({"ctrl", "alt", "l"}): RawEventType.HOTKEY_LOOP,
    frozenset({"ctrl", "alt", "c"}): RawEventType.HOTKEY_CSV_LOOP,
}


class EventHooker:
    """
    Starts pynput listeners. Call start() to begin recording, stop() to end.
    Events flow into self.event_queue.
    """

    def __init__(self) -> None:
        self.event_queue: queue.Queue[RawEvent] = queue.Queue()
        self._active = threading.Event()
        self._held_keys: set[str] = set()
        self._mouse_listener: Any = None
        self._keyboard_listener: Any = None

    def start(self) -> None:
        try:
            from pynput import mouse, keyboard  # type: ignore
        except ImportError:
            raise ImportError("pip install pynput")

        self._active.set()
        self._ignore_until_release: set[str] = set()

        # Mouse listener
        def on_click(x: int, y: int, button: Any, pressed: bool) -> None:
            if not self._active.is_set():
                return
            self.event_queue.put(RawEvent(
                type=RawEventType.MOUSE_CLICK,
                x=x, y=y,
                button=str(button).replace("Button.", ""),
                pressed=pressed,
            ))

        def on_move(x: int, y: int) -> None:
            pass  # Suppress move events — too noisy; only clicks matter

        def on_scroll(x: int, y: int, dx: int, dy: int) -> None:
            if not self._active.is_set():
                return
            self.event_queue.put(RawEvent(
                type=RawEventType.MOUSE_SCROLL,
                x=x, y=y,
                scroll_dx=dx,
                scroll_dy=dy,
            ))

        self._mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll)
        self._mouse_listener.start()

        # Keyboard listener
        def on_press(key: Any) -> None:
            if not self._active.is_set():
                return
            key_name = _key_to_str(key)
            if not key_name:
                return

            self._held_keys.add(key_name)

            # Check for hotkeys
            for combo, event_type in _HOTKEY_MAP.items():
                if combo.issubset(self._held_keys):
                    # Flag all currently held keys in this combo to be ignored on release
                    for k in combo:
                        self._ignore_until_release.add(k)
                    
                    # Remove any individual key-presses for these keys that were already queued
                    # (This handles the case where Ctrl/Alt were queued before the combo matched)
                    new_q = queue.Queue()
                    while not self.event_queue.empty():
                        item = self.event_queue.get()
                        if not (item.type == RawEventType.KEY_PRESS and item.key in combo):
                            new_q.put(item)
                    self.event_queue = new_q

                    self.event_queue.put(RawEvent(type=event_type))
                    return

            if key_name not in self._ignore_until_release:
                self.event_queue.put(RawEvent(type=RawEventType.KEY_PRESS, key=key_name, pressed=True))

        def on_release(key: Any) -> None:
            key_name = _key_to_str(key)
            if not key_name:
                return
            self._held_keys.discard(key_name)
            
            if key_name in self._ignore_until_release:
                self._ignore_until_release.discard(key_name)
                return

            self.event_queue.put(RawEvent(type=RawEventType.KEY_RELEASE, key=key_name, pressed=False))

        self._keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._keyboard_listener.start()
        log.info("EventHooker started. Hotkeys: Ctrl+Alt + [P|S|Space|I|D|L|C]")

    def stop(self) -> None:
        self._active.clear()
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        log.info("EventHooker stopped. %d events in queue.", self.event_queue.qsize())

    def drain(self) -> list[RawEvent]:
        events: list[RawEvent] = []
        while not self.event_queue.empty():
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events


def _key_to_str(key: Any) -> str:
    from pynput.keyboard import Key, KeyCode
    
    if isinstance(key, Key):
        name = key.name.lower()
    elif isinstance(key, KeyCode):
        if key.char:
            name = key.char.lower()
        else:
            # Handle control characters or VK codes
            if key.vk is not None:
                # Map VK to char (65-90 = A-Z, 48-57 = 0-9)
                if 65 <= key.vk <= 90:
                    name = chr(key.vk).lower()
                elif 48 <= key.vk <= 57:
                    name = chr(key.vk)
                else:
                    name = str(key).strip("'").lower()
            else:
                name = str(key).strip("'").lower()
    else:
        name = str(key).strip("'").lower()

    if name.startswith("key."):
        name = name[4:]
    
    # Canonicalize Left/Right variants
    for mod in ["ctrl", "shift", "alt", "cmd", "meta"]:
        if name.startswith(mod):
            return mod
    return name
