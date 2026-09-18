"""Bridge to the Open Interpreter worker running in .venv-agent."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

from .config import ROOT


class LocalAgent:
    def __init__(self, cfg, on_event) -> None:
        self.cfg = cfg
        self.on_event = on_event
        self.proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._start()

    # ------------------------------------------------------------- process
    def _python(self) -> str:
        p = ROOT / ".venv-agent" / "Scripts" / "python.exe"
        return str(p) if p.exists() else sys.executable

    def _start(self) -> None:
        worker = ROOT / "tools" / "oi_worker.py"
        payload = {
            "model": self.cfg.agent_model,
            "api_key": self.cfg.agent_api_key,
            "api_base": self.cfg.agent_api_base,
            "context_window": self.cfg.agent_context_window,
            "max_tokens": self.cfg.agent_max_tokens,
            "auto_run": self.cfg.agent_auto_run,
            "instructions": self.cfg.agent_instructions,
        }
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        try:
            self.proc = subprocess.Popen(
                [self._python(), "-u", str(worker), json.dumps(payload, ensure_ascii=False)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags,
            )
        except OSError as exc:
            self.proc = None
            self.on_event({"type": "error", "text": f"无法启动 agent: {exc}"})
            return
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                self.on_event(evt)
            except Exception:  # noqa: BLE001
                pass

    # -------------------------------------------------------------- control
    def send(self, text: str) -> bool:
        return self._write({"type": "chat", "text": text})

    def reset(self) -> bool:
        return self._write({"type": "reset"})

    def _write(self, obj: dict) -> bool:
        with self._lock:
            if not self.proc or self.proc.poll() is not None or not self.proc.stdin:
                return False
            try:
                self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
                self.proc.stdin.flush()
                return True
            except (OSError, ValueError):
                return False

    def stop(self) -> None:
        with self._lock:
            if self.proc and self.proc.poll() is None:
                try:
                    if self.proc.stdin:
                        self.proc.stdin.write('{"type":"quit"}\n')
                        self.proc.stdin.flush()
                except (OSError, ValueError):
                    pass
                try:
                    self.proc.terminate()
                except OSError:
                    pass
