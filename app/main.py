"""Application entry point and main loop."""
from __future__ import annotations

import queue
import random
import time

import OpenGL.GL as gl
import glfw

from .agent import LocalAgent
from .config import Config
from .hotkey import start_hotkey
from .net import BridgeClient
from .renderer import PetRenderer
from .ui import PetUI
from .voice import Voice
from .window import PetWindow

MOOD_TO_EXPRESSION = {
    "happy": "happy",
    "smile": "smile",
    "sad": "sad",
    "angry": "angry",
    "surprised": "surprised",
    "shy": "shy",
    "thinking": "thinking",
    "idle": "idle",
    "sleepy": "sleepy",
    "cute": "cute",
}

KEYWORDS = [
    (("哈哈", "开心", "好耶", "棒", "喜欢", "嘿嘿"), "happy"),
    (("诶嘿", "嘻嘻", "可爱"), "cute"),
    (("抱歉", "难过", "对不起", "呜呜", "叹气"), "sad"),
    (("哼", "生气", "讨厌", "不许"), "angry"),
    (("咦", "哇", "竟然", "居然", "真的吗"), "surprised"),
    (("嗯…", "让我想想", "考虑", "也许"), "thinking"),
    (("害羞", "脸红", "别说了"), "shy"),
]


def pick_expression(text: str) -> str:
    for words, name in KEYWORDS:
        if any(w in text for w in words):
            return name
    return "neutral"


class App:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.inbox: "queue.Queue[tuple]" = queue.Queue()
        self.input_text = ""
        self.ws_connected = False
        self.status = "连接中..."
        self._dragging = False
        self._grab = (0, 0)
        self.agent: LocalAgent | None = None

    # ------------------------------------------------------------- callbacks
    def _on_message(self, msg: dict) -> None:
        self.inbox.put(("msg", msg))

    def _on_status(self, ok: bool, info: str) -> None:
        self.inbox.put(("status", (ok, info)))

    def _toggle_click_through(self) -> None:
        self.inbox.put(("click_through", not self.cfg.click_through))

    # ------------------------------------------------------------------- run
    def run(self, snapshot: str | None = None) -> None:
        window = PetWindow(self.cfg)
        renderer = PetRenderer(self.cfg).load()
        ui = PetUI(self.cfg)

        voice = Voice(
            self.cfg,
            on_start=lambda d: self.inbox.put(("speak_start", d)),
            on_end=lambda: self.inbox.put(("speak_end", None)),
        )
        voice.start()

        bridge = BridgeClient(
            self.cfg.ws_url,
            self.cfg.ws_token,
            on_message=self._on_message,
            on_status=self._on_status,
        )
        bridge.start()

        if self.cfg.agent_enabled:
            self.agent = LocalAgent(self.cfg, on_event=lambda e: self.inbox.put(("agent", e)))

        start_hotkey(self._toggle_click_through)

        if self.cfg.greet_on_start:
            ui.set_bubble(self.cfg.greet_text, ttl=8)
            renderer.set_expression(self.cfg.default_expression or "idle")
            if self.cfg.tts_enabled and self.cfg.greet_tts:
                voice.say(self.cfg.greet_text)

        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        last = time.monotonic()
        frame = 0

        try:
            while not window.should_close():
                now = time.monotonic()
                dt = min(0.1, now - last)
                last = now

                window.begin_frame()

                self._drain_inbox(renderer, ui, voice)
                self._handle_drag(window)

                sw, sh = window.begin_scene(
                    window.width, window.height, getattr(self.cfg, "render_scale", 1.0)
                )
                gl.glClearColor(0.0, 0.0, 0.0, 0.0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
                renderer.update(dt)
                renderer.draw(sw, sh)
                window.end_scene(window.width, window.height)

                actions = ui.draw(self, window.width, window.height)
                self._apply_actions(actions, window, renderer, ui, voice, bridge)

                window.end_frame()

                frame += 1
                if snapshot and frame == 5:
                    renderer.snapshot(snapshot)
                    break
        finally:
            if self.agent:
                self.agent.stop()
            self._save_window_position(window)
            self.cfg.save()
            window.destroy()

    # ------------------------------------------------------------- internals
    def _drain_inbox(self, renderer: PetRenderer, ui: PetUI, voice: Voice) -> None:
        while True:
            try:
                kind, payload = self.inbox.get_nowait()
            except queue.Empty:
                return
            if kind == "status":
                self.ws_connected, self.status = payload
            elif kind == "speak_start":
                renderer.start_talking(float(payload))
            elif kind == "speak_end":
                renderer.stop_talking()
            elif kind == "click_through":
                if payload:
                    center = random.choice(["smile", "wink", "cute"])
                    renderer.set_expression(center)
            elif kind == "msg":
                self._handle_message(payload, renderer, ui, voice)
            elif kind == "agent":
                self._handle_agent_event(payload, renderer, ui, voice)

    def _handle_message(self, msg: dict, renderer, ui, voice) -> None:
        mtype = msg.get("type", "")
        if mtype == "reply":
            data = msg.get("data", {})
            text = str(data.get("text", "")).strip()
            if not text:
                return
            ui.set_bubble(text)
            mood = str(data.get("mood", "")).lower()
            renderer.set_expression(MOOD_TO_EXPRESSION.get(mood) or pick_expression(text))
            if self.cfg.tts_enabled:
                voice.say(text)
        elif mtype == "ready_ack":
            self.status = "已连接"

    def _handle_agent_event(self, evt: dict, renderer, ui, voice) -> None:
        etype = evt.get("type", "")
        if etype == "status":
            if evt.get("text") == "ready":
                self.status = "agent 就绪"
        elif etype == "assistant":
            text = str(evt.get("text", "")).strip()
            if text:
                ui.set_bubble(text)
                renderer.set_expression(pick_expression(text))
                if self.cfg.tts_enabled:
                    voice.say(text)
        elif etype == "code":
            ui.set_bubble("正在执行代码…", ttl=4)
            renderer.set_expression("thinking")
        elif etype == "confirmation":
            ui.set_bubble("需要确认操作（已跳过）", ttl=4)
        elif etype == "done":
            renderer.set_expression("smile")
        elif etype == "error":
            ui.set_bubble(f"agent 出错：{evt.get('text', '')}", ttl=10)
            renderer.set_expression("sad")

    def _handle_drag(self, window: PetWindow) -> None:
        left = glfw.get_mouse_button(window.window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        if not left or window.wants_mouse():
            self._dragging = False
            return
        cx, cy = glfw.get_cursor_pos(window.window)
        wx, wy = window.position()
        gx, gy = wx + cx, wy + cy
        if not self._dragging:
            self._dragging = True
            self._grab = (gx - wx, gy - wy)
            return
        nx = int(gx - self._grab[0])
        ny = int(gy - self._grab[1])
        if (nx, ny) != (wx, wy):
            glfw.set_window_pos(window.window, nx, ny)

    def _apply_actions(self, actions, window, renderer, ui, voice, bridge) -> None:
        for kind, value in actions:
            if kind == "send":
                prefix = self.cfg.agent_prefix
                if self.agent and prefix and value.lower().startswith(prefix.lower()):
                    task = value[len(prefix):].strip()
                    if task and self.agent.send(task):
                        ui.set_bubble(f"你：{task}", ttl=4)
                        renderer.set_expression("thinking")
                    else:
                        ui.set_bubble("agent 没启动呢…", ttl=4)
                elif bridge.chat(value):
                    ui.set_bubble(f"你：{value}", ttl=4)
                    renderer.set_expression("thinking")
                else:
                    ui.set_bubble("还没连上 AstrBot 呢…", ttl=4)
            elif kind == "expression":
                renderer.set_expression(value)
            elif kind == "click_through":
                window.set_click_through(bool(value))
                window.set_always_on_top(bool(value) and self.cfg.always_on_top)
            elif kind == "always_on_top":
                window.set_always_on_top(bool(value))
            elif kind == "reframe":
                renderer.auto_frame()
            elif kind == "save":
                self.cfg.save()
            elif kind == "quit":
                window.request_close()

    def _save_window_position(self, window: PetWindow) -> None:
        try:
            self.cfg.window_x, self.cfg.window_y = window.position()
        except Exception:  # noqa: BLE001
            pass


def main(snapshot: str | None = None) -> None:
    cfg = Config.load()
    App(cfg).run(snapshot)
