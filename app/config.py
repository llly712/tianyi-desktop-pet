"""Persistent configuration for the desktop pet."""
from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent
    RES_ROOT = Path(getattr(sys, "_MEIPASS", ROOT))
else:
    ROOT = Path(__file__).resolve().parent.parent
    RES_ROOT = ROOT

CONFIG_PATH = ROOT / "config.json"


@dataclass
class Config:
    # rendering
    model_path: str = "models/tianyi_model/TID Blue Lolita.Ver.pmx"
    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    auto_frame: bool = True
    cam_distance: float = 38.0
    cam_height: float = 10.0
    cam_fov: float = 30.0
    view_mode: str = "full"  # "full" or "half"

    # window
    window_width: int = 360
    window_height: int = 540
    window_x: int = -1
    window_y: int = -1
    always_on_top: bool = True
    click_through: bool = False
    fps: int = 60
    render_scale: float = 2.0

    # astrbot bridge
    ws_url: str = ""
    ws_token: str = ""

    # voice
    tts_enabled: bool = True
    tts_provider: str = "ppio"
    ppio_base_url: str = "https://api.ppinfra.com"
    ppio_api_key: str = ""
    tts_model: str = "minimax-speech-2.8-hd"
    tts_voice_id: str = "voice_d7c7acb7-bfa3-4c8e-aa47-ae823b0428c6"
    tts_speed: float = 1.1
    tts_voice: str = "zh-CN-XiaoyiNeural"
    tts_rate: str = "+10%"
    tts_pitch: str = "+15Hz"

    # agent (Open Interpreter, runs in .venv-agent)
    agent_enabled: bool = True
    agent_prefix: str = "agent:"
    agent_model: str = "deepseek/deepseek-flash"
    agent_api_key: str = ""
    agent_api_base: str = "https://api.deepseek.com/v1"
    agent_auto_run: bool = True
    agent_instructions: str = "始终使用简体中文回答，语气自然、简洁。"
    agent_context_window: int = 128000
    agent_max_tokens: int = 4096

    # behaviour
    expressions_enabled: bool = True
    blink_enabled: bool = True
    eye_lid: float = 0.18
    greet_on_start: bool = True
    greet_tts: bool = False
    greet_text: str = "诶嘿~ 洛天依上线啦！"
    default_expression: str = "neutral"

    # ui
    font_path: str = "C:/Windows/Fonts/Deng.ttf"
    font_size: int = 18

    def resolve_model(self) -> Path:
        p = Path(self.model_path)
        return p if p.is_absolute() else (RES_ROOT / p)

    def save(self) -> None:
        data = dataclasses.asdict(self)
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        if CONFIG_PATH.exists():
            try:
                raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return cfg
            valid = {f.name for f in dataclasses.fields(cls)}
            for k, v in raw.items():
                if k in valid:
                    setattr(cfg, k, v)
        return cfg
