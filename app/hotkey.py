"""Windows global hotkey (Ctrl+Shift+P) so click-through can always be undone."""
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

_user32 = ctypes.windll.user32


def start_hotkey(on_trigger: Callable[[], None], vk: int = 0x50) -> None:
    """vk 0x50 == 'P'."""

    def loop() -> None:
        _user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, vk)
        msg = wintypes.MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                try:
                    on_trigger()
                except Exception:  # noqa: BLE001
                    pass

    threading.Thread(target=loop, name="hotkey", daemon=True).start()
