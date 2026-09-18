"""Text-to-speech (PPIO MiniMax / edge-tts), played through pygame, driving lip sync."""
from __future__ import annotations

import asyncio
import json
import queue
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

import edge_tts


class Voice:
    def __init__(
        self,
        cfg,
        on_start: Callable[[float], None] | None = None,
        on_end: Callable[[], None] | None = None,
    ) -> None:
        self.cfg = cfg
        self.on_start = on_start or (lambda duration: None)
        self.on_end = on_end or (lambda: None)
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread = threading.Thread(target=self._worker, name="voice", daemon=True)
        self._pygame = None

    def start(self) -> None:
        self._thread.start()

    def say(self, text: str) -> None:
        text = (text or "").strip()
        if text:
            self._queue.put(text)

    def _worker(self) -> None:
        import pygame

        self._pygame = pygame
        pygame.mixer.init()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        out = Path(tempfile.gettempdir()) / "tianyi_tts.mp3"

        while True:
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            started = False
            try:
                reported = loop.run_until_complete(self._synthesize(text, out))
                pygame.mixer.music.load(str(out))
                pygame.mixer.music.play()
                duration = reported or 0.0
                if not duration:
                    try:
                        duration = pygame.mixer.Sound(str(out)).get_length()
                    except Exception:
                        duration = max(1.0, len(text) * 0.22)
                self.on_start(duration)
                started = True
                while pygame.mixer.music.get_busy():
                    time.sleep(0.04)
            except Exception:
                if not started:
                    self.on_start(max(1.0, len(text) * 0.22))
            finally:
                self.on_end()

    async def _synthesize(self, text: str, path: Path) -> float:
        provider = (getattr(self.cfg, "tts_provider", "ppio") or "ppio").lower()
        if provider == "edge":
            await self._synthesize_edge(text, path)
            return 0.0
        try:
            return self._synthesize_ppio(text, path)
        except Exception as exc:
            print(f"[voice] ppio tts failed ({exc}); falling back to edge-tts", flush=True)
            await self._synthesize_edge(text, path)
            return 0.0

    def _synthesize_ppio(self, text: str, path: Path) -> float:
        base = (getattr(self.cfg, "ppio_base_url", "https://api.ppinfra.com") or "").rstrip("/")
        model = getattr(self.cfg, "tts_model", "minimax-speech-2.8-hd")
        url = f"{base}/v3/{model}"
        payload = {
            "text": text,
            "stream": False,
            "output_format": "url",
            "voice_setting": {
                "voice_id": getattr(self.cfg, "tts_voice_id", ""),
                "speed": float(getattr(self.cfg, "tts_speed", 1.1)),
            },
            "audio_setting": {"format": "mp3"},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {getattr(self.cfg, 'ppio_api_key', '')}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail[:300]}") from exc
        data = result.get("data") or {}
        audio_url = data.get("audio")
        if not audio_url:
            raise RuntimeError(f"no audio in response: {json.dumps(result, ensure_ascii=False)[:300]}")
        with urllib.request.urlopen(audio_url, timeout=60) as resp:
            path.write_bytes(resp.read())
        length_ms = (result.get("extra_info") or {}).get("audio_length") or 0
        return float(length_ms) / 1000.0

    async def _synthesize_edge(self, text: str, path: Path) -> None:
        communicate = edge_tts.Communicate(
            text,
            self.cfg.tts_voice,
            rate=self.cfg.tts_rate,
            pitch=self.cfg.tts_pitch,
        )
        await communicate.save(str(path))
