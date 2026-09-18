"""imgui overlay: chat bubble, input bar, context menu and settings.

Theme: minimal, accent colour #66ccff.
"""
from __future__ import annotations

import time

import imgui

from . import expressions

ACCENT = (0.40, 0.80, 1.00)  # #66ccff

BASE_FLAGS = (
    imgui.WINDOW_NO_TITLE_BAR
    | imgui.WINDOW_NO_RESIZE
    | imgui.WINDOW_NO_MOVE
    | imgui.WINDOW_NO_SAVED_SETTINGS
    | imgui.WINDOW_NO_SCROLLBAR
    | imgui.WINDOW_NO_COLLAPSE
)
BUBBLE_FLAGS = BASE_FLAGS | imgui.WINDOW_ALWAYS_AUTO_RESIZE

EXPRESSION_MENU = [
    "idle", "smile", "happy", "cute", "shy", "wink", "star", "heart",
    "thinking", "surprised", "sad", "angry", "sleepy", "serious", "tongue",
]


def _apply_theme() -> None:
    imgui.style_colors_dark()
    s = imgui.get_style()
    s.window_rounding = 12.0
    s.frame_rounding = 10.0
    s.grab_rounding = 10.0
    s.scrollbar_rounding = 10.0
    s.window_border_size = 1.0
    s.frame_border_size = 0.0
    s.window_padding = imgui.Vec2(10.0, 10.0)
    s.frame_padding = imgui.Vec2(10.0, 6.0)
    s.item_spacing = imgui.Vec2(8.0, 7.0)

    r, g, b = ACCENT
    s.colors[imgui.COLOR_TEXT] = imgui.Vec4(0.90, 0.94, 1.00, 1.00)
    s.colors[imgui.COLOR_TEXT_DISABLED] = imgui.Vec4(0.50, 0.56, 0.66, 1.00)
    s.colors[imgui.COLOR_WINDOW_BACKGROUND] = imgui.Vec4(0.05, 0.07, 0.10, 0.78)
    s.colors[imgui.COLOR_CHILD_BACKGROUND] = imgui.Vec4(0.08, 0.10, 0.14, 0.60)
    s.colors[imgui.COLOR_BORDER] = imgui.Vec4(r, g, b, 0.40)
    s.colors[imgui.COLOR_FRAME_BACKGROUND] = imgui.Vec4(0.12, 0.15, 0.20, 0.90)
    s.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = imgui.Vec4(0.16, 0.20, 0.27, 0.95)
    s.colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = imgui.Vec4(r, g, b, 0.25)
    s.colors[imgui.COLOR_BUTTON] = imgui.Vec4(r, g, b, 0.30)
    s.colors[imgui.COLOR_BUTTON_HOVERED] = imgui.Vec4(r, g, b, 0.55)
    s.colors[imgui.COLOR_BUTTON_ACTIVE] = imgui.Vec4(r, g, b, 0.80)
    s.colors[imgui.COLOR_HEADER] = imgui.Vec4(r, g, b, 0.30)
    s.colors[imgui.COLOR_HEADER_HOVERED] = imgui.Vec4(r, g, b, 0.50)
    s.colors[imgui.COLOR_HEADER_ACTIVE] = imgui.Vec4(r, g, b, 0.70)
    s.colors[imgui.COLOR_CHECK_MARK] = imgui.Vec4(r, g, b, 1.00)
    s.colors[imgui.COLOR_SLIDER_GRAB] = imgui.Vec4(r, g, b, 0.70)
    s.colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = imgui.Vec4(r, g, b, 1.00)
    s.colors[imgui.COLOR_SEPARATOR] = imgui.Vec4(r, g, b, 0.22)
    s.colors[imgui.COLOR_POPUP_BACKGROUND] = imgui.Vec4(0.06, 0.08, 0.12, 0.96)
    s.colors[imgui.COLOR_SCROLLBAR_BACKGROUND] = imgui.Vec4(0.08, 0.10, 0.14, 0.60)
    s.colors[imgui.COLOR_SCROLLBAR_GRAB] = imgui.Vec4(r, g, b, 0.40)
    s.colors[imgui.COLOR_SCROLLBAR_GRAB_HOVERED] = imgui.Vec4(r, g, b, 0.60)
    s.colors[imgui.COLOR_SCROLLBAR_GRAB_ACTIVE] = imgui.Vec4(r, g, b, 0.80)
    s.colors[imgui.COLOR_TITLE_BACKGROUND] = imgui.Vec4(0.06, 0.08, 0.12, 0.90)
    s.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = imgui.Vec4(r, g, b, 0.40)
    s.colors[imgui.COLOR_TITLE_BACKGROUND_COLLAPSED] = imgui.Vec4(0.06, 0.08, 0.12, 0.60)


class PetUI:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.bubble = ""
        self.bubble_until = 0.0
        self.show_settings = False
        self._themed = False

    def set_bubble(self, text: str, ttl: float = 10.0) -> None:
        self.bubble = (text or "").strip()
        self.bubble_until = time.monotonic() + ttl

    # ---------------------------------------------------------------- drawing
    def draw(self, app, width: int, height: int) -> list[tuple]:
        actions: list[tuple] = []
        if not self._themed:
            _apply_theme()
            self._themed = True

        pad = 10
        if self.bubble and time.monotonic() < self.bubble_until:
            imgui.set_next_window_position(pad, pad, imgui.FIRST_USE_EVER)
            imgui.set_next_window_size(width - pad * 2, 0, imgui.FIRST_USE_EVER)
            imgui.begin("##bubble", flags=BUBBLE_FLAGS)
            imgui.push_text_wrap_pos(width - pad * 4)
            imgui.text_wrapped(self.bubble)
            imgui.pop_text_wrap_pos()
            imgui.end()

        if self.show_settings:
            actions += self._draw_settings(app)

        actions += self._draw_input(app, width, height)

        self._draw_context_menu(app, actions)
        return actions

    # ------------------------------------------------------------- pieces
    def _draw_input(self, app, width: int, height: int) -> list[tuple]:
        actions: list[tuple] = []
        bar_h = 46
        margin = 12
        btn_w = 56
        imgui.set_next_window_position(margin, height - bar_h - margin, imgui.ALWAYS)
        imgui.set_next_window_size(width - margin * 2, bar_h, imgui.ALWAYS)
        imgui.begin("##bar", flags=BASE_FLAGS | imgui.WINDOW_NO_BACKGROUND)

        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 16.0)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, imgui.Vec2(12.0, 9.0))
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, 0.10, 0.13, 0.18, 0.88)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_HOVERED, 0.13, 0.17, 0.23, 0.94)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_ACTIVE, 0.13, 0.17, 0.23, 0.94)
        imgui.set_next_item_width(width - margin * 2 - btn_w - 10)
        entered, value = imgui.input_text(
            "##input", app.input_text, 256, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
        )
        app.input_text = value
        imgui.pop_style_color(3)
        imgui.pop_style_var(2)

        imgui.same_line()
        r, g, b = ACCENT
        imgui.push_style_color(imgui.COLOR_BUTTON, r, g, b, 0.85)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.55, 0.87, 1.00, 0.95)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.30, 0.70, 0.95, 1.00)
        imgui.push_style_color(imgui.COLOR_TEXT, 0.04, 0.07, 0.10, 1.00)
        send = imgui.button("发送", btn_w, 30)
        imgui.pop_style_color(4)

        if (entered or send) and app.input_text.strip():
            actions.append(("send", app.input_text.strip()))
            app.input_text = ""
        imgui.end()
        return actions

    def _draw_settings(self, app) -> list[tuple]:
        actions: list[tuple] = []
        imgui.set_next_window_position(12, 96, imgui.FIRST_USE_EVER)
        imgui.set_next_window_size(248, 0, imgui.FIRST_USE_EVER)
        expanded, opened = imgui.begin("设置", closable=True, flags=BASE_FLAGS)
        if opened:
            imgui.text(f"桥接: {'已连接' if app.ws_connected else '未连接'}")
            if app.status:
                imgui.push_text_wrap_pos(224)
                imgui.text_wrapped(app.status)
                imgui.pop_text_wrap_pos()
            imgui.separator()

            changed, v = imgui.checkbox("半身显示", self.cfg.view_mode == "half")
            if changed:
                self.cfg.view_mode = "half" if v else "full"
                actions.append(("config", None))
                actions.append(("reframe", None))

            changed, v = imgui.checkbox("语音 (TTS)", self.cfg.tts_enabled)
            if changed:
                self.cfg.tts_enabled = v
                actions.append(("config", None))

            changed, v = imgui.checkbox("开屏语音", self.cfg.greet_tts)
            if changed:
                self.cfg.greet_tts = v
                actions.append(("config", None))

            changed, v = imgui.checkbox("点击穿透", self.cfg.click_through)
            if changed:
                actions.append(("click_through", v))

            changed, v = imgui.checkbox("总在最前", self.cfg.always_on_top)
            if changed:
                actions.append(("always_on_top", v))

            changed, v = imgui.checkbox("眨眼", self.cfg.blink_enabled)
            if changed:
                self.cfg.blink_enabled = v
                actions.append(("config", None))

            changed, v = imgui.slider_float("缩放", self.cfg.scale, 0.4, 2.5)
            if changed:
                self.cfg.scale = v
                actions.append(("config", None))

            if imgui.button("保存配置"):
                actions.append(("config", None))
                actions.append(("save", None))
            imgui.same_line()
            if imgui.button("退出"):
                actions.append(("quit", None))
            imgui.end()
        else:
            self.show_settings = False
        return actions

    def _draw_context_menu(self, app, actions: list[tuple]) -> None:
        if imgui.begin_popup_context_window("##ctx", imgui.POPUP_MOUSE_BUTTON_RIGHT):
            if imgui.begin_menu("表情"):
                for name in EXPRESSION_MENU:
                    clicked, _ = imgui.menu_item(name)
                    if clicked:
                        actions.append(("expression", name))
                imgui.end_menu()
            clicked, _ = imgui.menu_item("半身/全身")
            if clicked:
                self.cfg.view_mode = "full" if self.cfg.view_mode == "half" else "half"
                actions.append(("config", None))
                actions.append(("reframe", None))
            clicked, _ = imgui.menu_item("设置")
            if clicked:
                self.show_settings = True
            clicked, _ = imgui.menu_item("窗口置顶")
            if clicked:
                actions.append(("always_on_top", not self.cfg.always_on_top))
            clicked, _ = imgui.menu_item("点击穿透")
            if clicked:
                actions.append(("click_through", not self.cfg.click_through))
            imgui.separator()
            clicked, _ = imgui.menu_item("退出")
            if clicked:
                actions.append(("quit", None))
            imgui.end_popup()
