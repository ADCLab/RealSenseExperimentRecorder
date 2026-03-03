"""Reusable keyboard hotkey listeners built on python-evdev."""

from __future__ import annotations

import time
from select import select
from typing import Callable, Dict, Optional, Set

from evdev import InputDevice, ecodes, list_devices


def monitor_ctrl_hotkey(on_release_callback: Callable[[], None], log_fn: Optional[Callable[[str], None]] = None):
    """Watch for Ctrl key releases using python-evdev and call the provided callback.

    Designed for Linux environments where evdev devices are exposed via /dev/input/event*.
    """

    def log_once(message: str):
        nonlocal permission_reported
        if permission_reported:
            return
        permission_reported = True
        if log_fn:
            try:
                log_fn(message)
            except Exception:
                pass

    ctrl_codes = {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL}
    device_map: Dict[int, InputDevice] = {}
    attached_paths: Set[str] = set()
    permission_reported = False

    def attach_devices():
        current_paths = set(attached_paths)
        for path in list_devices():
            if path in current_paths:
                continue
            try:
                device = InputDevice(path)
            except PermissionError:
                log_once(f"Ctrl hotkey listener cannot open {path}; ensure read access to /dev/input/event*.")
                continue
            except (FileNotFoundError, OSError):
                continue

            caps = device.capabilities().get(ecodes.EV_KEY, [])
            if any(code in caps for code in ctrl_codes):
                device_map[device.fd] = device
                attached_paths.add(path)
            else:
                device.close()

    def detach_device(fd: int):
        device = device_map.pop(fd, None)
        if not device:
            return
        attached_paths.discard(getattr(device, "path", ""))
        try:
            device.close()
        except Exception:
            pass

    while True:
        attach_devices()
        if not device_map:
            time.sleep(1)
            continue

        try:
            readable, _, _ = select(device_map, [], [], 1.0)
        except OSError:
            continue

        for fd in readable:
            device = device_map.get(fd)
            if not device:
                continue
            try:
                for event in device.read():
                    if event.type == ecodes.EV_KEY and event.code in ctrl_codes and event.value == 0:
                        try:
                            on_release_callback()
                        except Exception:
                            if log_fn:
                                try:
                                    log_fn("Ctrl hotkey callback raised an exception.")
                                except Exception:
                                    pass
            except OSError:
                detach_device(fd)
