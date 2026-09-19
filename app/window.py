"""GLFW window (transparent, frameless, always-on-top) plus the imgui overlay."""
from __future__ import annotations

import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer


class PetWindow:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        if not glfw.init():
            raise RuntimeError("glfw.init() failed")

        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE if cfg.always_on_top else glfw.FALSE)
        glfw.window_hint(glfw.SCALE_TO_MONITOR, glfw.TRUE)

        self.window = glfw.create_window(
            cfg.window_width, cfg.window_height, "洛天依", None, None
        )
        if not self.window:
            glfw.terminate()
            raise RuntimeError("failed to create window")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        self._place_default()
        self._apply_click_through(cfg.click_through)

        imgui.create_context()
        self.impl = GlfwRenderer(self.window)
        self._load_font()

    # ------------------------------------------------------------------ setup
    def _place_default(self) -> None:
        cfg = self.cfg
        if cfg.window_x >= 0 and cfg.window_y >= 0:
            glfw.set_window_pos(self.window, cfg.window_x, cfg.window_y)
            return
        mon = glfw.get_primary_monitor()
        area = glfw.get_monitor_workarea(mon)
        x = area[0] + area[2] - cfg.window_width - 24
        y = area[1] + area[3] - cfg.window_height - 24
        glfw.set_window_pos(self.window, int(x), int(y))

    def _load_font(self) -> None:
        import imgui.core

        cfg = self.cfg
        io = self.impl.io
        self._font = None
        try:
            ranges = io.fonts.get_glyph_ranges_chinese_full()
            self._font = io.fonts.add_font_from_file_ttf(
                cfg.font_path, cfg.font_size, None, ranges
            )
            print(f"[font] loaded {cfg.font_path} with CJK ranges", flush=True)
        except Exception as exc:
            print(f"[font] CJK load failed ({exc!r}), retrying plain", flush=True)
            try:
                self._font = io.fonts.add_font_from_file_ttf(cfg.font_path, cfg.font_size)
            except Exception as exc2:
                print(f"[font] plain load failed too: {exc2!r}", flush=True)
                return
        self.impl.refresh_font_texture()

    # ------------------------------------------------------------------ state
    @property
    def width(self) -> int:
        return glfw.get_framebuffer_size(self.window)[0]

    @property
    def height(self) -> int:
        return glfw.get_framebuffer_size(self.window)[1]

    def should_close(self) -> bool:
        return glfw.window_should_close(self.window)

    def request_close(self) -> None:
        glfw.set_window_should_close(self.window, True)

    def position(self) -> tuple[int, int]:
        x, y = glfw.get_window_pos(self.window)
        return int(x), int(y)

    def move(self, dx: int, dy: int) -> None:
        x, y = self.position()
        glfw.set_window_pos(self.window, x + int(dx), y + int(dy))

    # ------------------------------------------------------------- rendering
    def _ensure_scene_target(self, w: int, h: int, scale: float) -> None:
        from OpenGL import GL as gl

        tw = max(1, int(round(w * scale)))
        th = max(1, int(round(h * scale)))
        if getattr(self, "_fbo", None) is not None and getattr(self, "_tw", 0) == tw and getattr(self, "_th", 0) == th:
            return
        self._destroy_scene_target()
        self._tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._tex)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, tw, th, 0,
            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None,
        )
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        self._depth = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self._depth)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, tw, th)
        self._fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self._tex, 0
        )
        gl.glFramebufferRenderbuffer(
            gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self._depth
        )
        ok = gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        if not ok:
            self._destroy_scene_target()
            return
        self._tw, self._th = tw, th

    def begin_scene(self, w: int, h: int, scale: float = 1.0):
        """Bind the (super-sampled) scene target; returns the size to render at."""
        from OpenGL import GL as gl

        try:
            if scale and float(scale) > 1.0:
                self._ensure_scene_target(w, h, float(scale))
        except Exception as exc:  # noqa: BLE001
            print(f"[ssaa] disabled: {exc!r}", flush=True)
            self._destroy_scene_target()

        if getattr(self, "_fbo", None) is not None:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
            gl.glViewport(0, 0, self._tw, self._th)
            self._supersample = True
            return self._tw, self._th
        self._supersample = False
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(0, 0, w, h)
        return w, h

    def end_scene(self, w: int, h: int) -> None:
        if not getattr(self, "_supersample", False):
            return
        from OpenGL import GL as gl

        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, self._fbo)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, 0)
        gl.glBlitFramebuffer(
            0, 0, self._tw, self._th,
            0, 0, w, h,
            gl.GL_COLOR_BUFFER_BIT, gl.GL_LINEAR,
        )
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _destroy_scene_target(self) -> None:
        from OpenGL import GL as gl

        if getattr(self, "_fbo", None):
            gl.glDeleteFramebuffers(1, [self._fbo])
            self._fbo = None
        if getattr(self, "_tex", None):
            gl.glDeleteTextures([self._tex])
            self._tex = None
        if getattr(self, "_depth", None):
            gl.glDeleteRenderbuffers(1, [self._depth])
            self._depth = None
        self._tw = self._th = 0

    def begin_frame(self) -> None:
        self.impl.process_inputs()
        imgui.new_frame()
        if getattr(self, "_font", None) is not None:
            imgui.push_font(self._font)

    def end_frame(self) -> None:
        if getattr(self, "_font", None) is not None:
            imgui.pop_font()
        imgui.render()
        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)
        glfw.poll_events()

    # ------------------------------------------------------------- options
    def _apply_click_through(self, enabled: bool) -> None:
        try:
            glfw.set_window_attrib(
                self.window,
                glfw.MOUSE_BUTTON_PASSTHROUGH,
                glfw.TRUE if enabled else glfw.FALSE,
            )
        except Exception:
            pass

    def set_click_through(self, enabled: bool) -> None:
        self.cfg.click_through = enabled
        self._apply_click_through(enabled)

    def set_always_on_top(self, enabled: bool) -> None:
        self.cfg.always_on_top = enabled
        glfw.set_window_attrib(
            self.window, glfw.FLOATING, glfw.TRUE if enabled else glfw.FALSE
        )

    def wants_mouse(self) -> bool:
        return bool(imgui.get_io().want_capture_mouse)

    def destroy(self) -> None:
        try:
            self._destroy_scene_target()
        except Exception:
            pass
        try:
            self.impl.shutdown()
        except Exception:
            pass
        glfw.destroy_window(self.window)
        glfw.terminate()
