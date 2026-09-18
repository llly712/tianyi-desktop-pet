"""Open Interpreter worker. Runs inside .venv-agent (separate interpreter process).

Protocol (JSON lines):
  parent -> worker : {"type":"chat","text":...} | {"type":"reset"} | {"type":"quit"}
  worker -> parent : {"type":"assistant"|"code"|"output"|"confirmation"|"status"|"error"|"done", ...}
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

for _stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from interpreter import interpreter  # noqa: E402


def _emit(obj: dict) -> None:
    try:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    except (OSError, ValueError):
        os._exit(0)


_TYPE_MAP = {
    "message": "assistant",
    "code": "code",
    "console": "output",
    "confirmation": "confirmation",
}


def _configure(cfg: dict) -> None:
    interpreter.llm.model = cfg.get("model", "deepseek/deepseek-flash")
    interpreter.llm.api_key = cfg.get("api_key", "")
    interpreter.llm.api_base = cfg.get("api_base", "https://api.deepseek.com/v1")
    interpreter.llm.context_window = int(cfg.get("context_window", 128000))
    interpreter.llm.max_tokens = int(cfg.get("max_tokens", 4096))
    interpreter.auto_run = bool(cfg.get("auto_run", True))
    instructions = cfg.get("instructions")
    if instructions:
        interpreter.custom_instructions = instructions
    interpreter.offline = True
    interpreter.verbose = False


def _chat(text: str) -> None:
    buf: list[str] = []
    buf_key: tuple[str, str] | None = None

    def flush() -> None:
        nonlocal buf, buf_key
        if buf and buf_key:
            _emit({"type": buf_key[0], "language": buf_key[1], "text": "".join(buf)})
        buf = []
        buf_key = None

    try:
        for chunk in interpreter.chat(text, stream=True, display=False):
            mtype = _TYPE_MAP.get(chunk.get("type"))
            role = chunk.get("role")
            content = chunk.get("content")
            if not mtype or role != "assistant":
                continue
            key = (mtype, chunk.get("format", "") or "")
            if key != buf_key:
                flush()
                buf_key = key
            if content:
                buf.append(str(content))
            if chunk.get("end"):
                flush()
        flush()
        _emit({"type": "done"})
    except Exception as exc:  # noqa: BLE001
        flush()
        _emit({"type": "error", "text": f"{type(exc).__name__}: {exc}"})


def main() -> None:
    cfg = {}
    if len(sys.argv) > 1:
        try:
            cfg = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            cfg = {}
    _configure(cfg)
    _emit({"type": "status", "text": "ready"})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = msg.get("type")
        if kind == "chat":
            _chat(str(msg.get("text", "")))
        elif kind == "reset":
            interpreter.messages = []
            _emit({"type": "status", "text": "reset"})
        elif kind == "quit":
            break


if __name__ == "__main__":
    main()
