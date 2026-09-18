"""Background WebSocket client for the AstrBot pet_bridge plugin.

Protocol (see astrbot_plugin_pet_bridge/main.py):
  out: {"type": "chat", "data": {"text": ...}}
       {"type": "agent_result", "data": {"request_id": ..., "result": ...}}
       {"type": "ready"}
  in:  {"type": "reply", "data": {"text": ..., "mood": ...}}
       {"type": "pong"}
       {"type": "ready_ack"}
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Callable

try:
    from websockets.asyncio.client import connect as ws_connect
except ImportError:  # pragma: no cover
    from websockets.client import connect as ws_connect


class BridgeClient:
    def __init__(
        self,
        url: str,
        token: str = "",
        on_message: Callable[[dict], None] | None = None,
        on_status: Callable[[bool, str], None] | None = None,
    ) -> None:
        self.url = url
        self.token = token
        self.on_message = on_message or (lambda msg: None)
        self.on_status = on_status or (lambda ok, info: None)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ws = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="bridge", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._main())

    async def _main(self) -> None:
        while True:
            try:
                async with ws_connect(
                    self.url, ping_interval=20, ping_timeout=20, max_size=2 ** 20
                ) as ws:
                    self._ws = ws
                    self.on_status(True, "")
                    await ws.send(json.dumps({"type": "ready"}))
                    async for raw in ws:
                        if isinstance(raw, (bytes, bytearray)):
                            raw = raw.decode("utf-8", "replace")
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        self.on_message(msg)
            except Exception as exc:  # noqa: BLE001
                self.on_status(False, f"{type(exc).__name__}: {exc}")
            finally:
                self._ws = None
            await asyncio.sleep(3.0)

    def send(self, payload: dict) -> bool:
        loop, ws = self._loop, self._ws
        if loop is None or ws is None:
            return False
        try:
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps(payload, ensure_ascii=False)), loop
            )
            return True
        except Exception:  # noqa: BLE001
            return False

    def chat(self, text: str) -> bool:
        return self.send({"type": "chat", "data": {"text": text}})

    def agent_result(self, request_id: str, result: Any) -> bool:
        return self.send(
            {"type": "agent_result", "data": {"request_id": request_id, "result": result}}
        )
