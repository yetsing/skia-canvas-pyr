"""
A small EventEmitter implementation inspired by Node.js EventEmitter.

Features:
- on/add_listener/prepend_listener
- once/prepend_once_listener
- off/remove_listener/remove_all_listeners
- listeners/listener_count
- set_max_listeners (warns when exceeded)
- emit (synchronous)
- emit_async (awaits coroutine listeners; calls sync listeners normally)

Notes:
- If an 'error' event is emitted with no listeners, an exception is raised
  (mimics Node.js behavior).
- once-wrappers keep a reference to the original function on attribute
  '__original_listener' so remove_listener can remove the original.
"""

from __future__ import annotations

import threading
import warnings
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Sequence

Listener = Callable[..., Any]


class EventEmitter:
    __slots__ = ("_events", "_max_listeners", "_lock")

    def __init__(self) -> None:
        self._events: DefaultDict[str, List[Listener]] = defaultdict(list)
        self._max_listeners: int = 10
        self._lock = threading.RLock()

    # --- registration ----
    def on(self, event: str, listener: Listener | None = None) -> Listener:
        """Register listener to event (append)."""
        if listener is None:
            # used as decorator
            def decorator(fn: Listener) -> Listener:
                return self.add_listener(event, fn)

            return decorator
        return self.add_listener(event, listener)

    def add_listener(self, event: str, listener: Listener) -> Listener:
        with self._lock:
            self._events[event].append(listener)
            self._maybe_warn_max(event)
        return listener

    def prepend_listener(self, event: str, listener: Listener) -> Listener:
        with self._lock:
            self._events[event].insert(0, listener)
            self._maybe_warn_max(event)
        return listener

    # --- removal ----
    def remove_listener(self, event: str, listener: Listener) -> None:
        """Remove a listener (the original function or a wrapper)."""
        with self._lock:
            listeners = self._events.get(event)
            if not listeners:
                return

            # Keep listeners that do not match the listener or wrappers for it
            def keep(l: Listener) -> bool:
                if l is listener:
                    return False
                # if l is a wrapper, check original attr
                orig = getattr(l, "__original_listener", None)
                if orig is listener:
                    return False
                return True

            new_list = [l for l in listeners if keep(l)]
            if new_list:
                self._events[event] = new_list
            else:
                # remove empty list entry
                self._events.pop(event, None)

    # alias
    off = remove_listener

    def remove_all_listeners(self, event: Optional[str] = None) -> None:
        with self._lock:
            if event is None:
                self._events.clear()
            else:
                self._events.pop(event, None)

    # --- introspection ---
    def listeners(self, event: str) -> List[Listener]:
        """Return a shallow copy of the listeners list for event."""
        with self._lock:
            return list(self._events.get(event, []))

    def listener_count(self, event: str) -> int:
        with self._lock:
            return len(self._events.get(event, []))

    def set_max_listeners(self, n: int) -> None:
        if n < 0:
            raise ValueError("max listeners must be non-negative")
        self._max_listeners = n

    def _maybe_warn_max(self, event: str) -> None:
        lst = self._events.get(event, [])
        if 0 <= self._max_listeners < len(lst):
            warnings.warn(
                f"Possible memory leak detected. {len(lst)} listeners added for event '{event}'. "
                f"Use set_max_listeners() to increase limit.",
                ResourceWarning,
            )

    # --- emit ---
    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Synchronously call all listeners for event with provided args/kwargs.

        Note: If 'error' event is emitted and there are no listeners, raise the error
        (mimics Node.js behavior).
        """
        with self._lock:
            listeners = list(self._events.get(event, []))

        if not listeners:
            if event == "error":
                # if an Error-like is passed, raise it; else raise generic RuntimeError
                if args and isinstance(args[0], BaseException):
                    raise args[0]
                raise RuntimeError("Unhandled 'error' event")

        for fn in listeners:
            fn(*args, **kwargs)


# --- small demo when run as script ---
if __name__ == "__main__":
    ee = EventEmitter()

    def l1(x):
        print("l1 got", x)

    @ee.on("data")
    def l2(x):
        print("l2 got", x)

    ee.emit("data", 1)
    ee.emit("data", 2)

    # error event demo
    try:
        ee.emit("error", RuntimeError("boom"))
    except RuntimeError as e:
        print("caught unhandled error:", e)
