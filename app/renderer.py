"""PMX model loading, camera and per-frame drawing on top of mmdpy."""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
from PIL import Image
from mmdpy import model as MmdpyModel
from mmdpy import pmxpy_load

from . import expressions
from .morph import MorphController


class PetRenderer:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.app: MmdpyModel | None = None
        self.morph: MorphController | None = None

        self.expression = "idle"
        self._blink_clock = random.uniform(1.5, 4.0)
        self._blink_progress = -1.0
        self._lip_clock = 0.0
        self._lip_index = 0
        self._lip_until = 0.0
        self._breath = 0.0

    # ------------------------------------------------------------------ load
    def load(self) -> "PetRenderer":
        path = str(self.cfg.resolve_model())
        if not Path(path).exists():
            raise FileNotFoundError(path)
        self.app = MmdpyModel(path)
        raw = pmxpy_load.load(path)
        self.morph = MorphController(self.app.model, raw)
        if getattr(self.cfg, "auto_frame", True):
            self.auto_frame()
        self.set_expression(getattr(self.cfg, "default_expression", "idle"))
        return self

    def auto_frame(self, margin: float = 1.18) -> None:
        if not self.app:
            return
        ys: list[float] = []
        xs: list[float] = []
        for mesh in self.app.model.meshes:
            v = np.asarray(mesh.vertex, dtype=float)
            if v.size == 0:
                continue
            ys.append(float(v[:, 1].min()))
            ys.append(float(v[:, 1].max()))
            xs.append(float(v[:, 0].min()))
            xs.append(float(v[:, 0].max()))
        if not ys:
            return
        ymin, ymax = min(ys), max(ys)
        xmin, xmax = min(xs), max(xs)
        span_y = ymax - ymin
        span_x = xmax - xmin
        if getattr(self.cfg, "view_mode", "full") == "half":
            ymin = ymax - span_y * 0.62
            span_y = ymax - ymin
            # ignore the T-pose arm span, arms are posed inward at draw time
            span_x = min(span_x, span_y * 0.66)
        cfg = self.cfg
        aspect = cfg.window_width / float(cfg.window_height or 1)
        fov_v = math.radians(cfg.cam_fov)
        fov_h = 2.0 * math.atan(math.tan(fov_v / 2.0) * aspect)
        dist_v = (span_y * margin / 2.0) / math.tan(fov_v / 2.0)
        dist_h = (span_x * margin / 2.0) / math.tan(fov_h / 2.0)
        cfg.cam_height = (ymin + ymax) / 2.0
        cfg.cam_distance = max(dist_v, dist_h)
        cfg.offset_x = 0.0
        cfg.offset_y = 0.0
        print(
            f"[frame] mode={cfg.view_mode} bbox x=[{xmin:.2f},{xmax:.2f}] "
            f"y=[{ymin:.2f},{ymax:.2f}] height={cfg.cam_height:.2f} "
            f"distance={cfg.cam_distance:.2f}",
            flush=True,
        )

    def pose_arms(self, verbose: bool = False) -> None:
        if not self.app:
            return
        m = self.app.model
        poses = (
            ("左腕", -0.52, -0.16),
            ("右腕", 0.52, -0.16),
            ("左ひじ", -0.14, 0.0),
            ("右ひじ", 0.14, 0.0),
        )
        changed = False
        for name, z, x in poses:
            bone = m.get_bone_by_name(name)
            if bone is not None:
                bone.rotZ(z)
                if x:
                    bone.rotX(x)
                changed = True
        if verbose:
            if changed:
                m.update_bone()
            elbow = m.get_bone_by_name("左ひじ")
            if elbow is not None:
                print(
                    "[pose] 左ひじ pos=",
                    np.round(elbow.get_global_matrix()[3, 0:3], 3).tolist(),
                    flush=True,
                )

    # ------------------------------------------------------------- behaviour
    def set_expression(self, name: str) -> None:
        if not self.morph or not self.cfg.expressions_enabled:
            return
        if name not in expressions.EXPRESSIONS:
            return
        self.expression = name
        expressions.apply_expression(self.morph, name)

    def start_talking(self, seconds: float = 3.0) -> None:
        self._lip_until = self._now() + max(0.6, seconds)

    def stop_talking(self) -> None:
        self._lip_until = 0.0
        self._clear_vowels()

    # ------------------------------------------------------------------- tick
    def _now(self) -> float:
        import time

        return time.monotonic()

    def _clear_vowels(self) -> None:
        if not self.morph:
            return
        for name, _ in expressions.VOWELS:
            self.morph.set_weight(name, 0.0)

    def update(self, dt: float) -> None:
        if not self.morph:
            return
        self._update_blink(dt)
        self._update_lipsync(dt)
        self._breath += dt
        self.morph.update()

    def _update_blink(self, dt: float) -> None:
        if not self.cfg.blink_enabled:
            return
        # don't fight an expression that already closes the eyes
        if self.expression in ("close_eye", "happy", "cute", "sleepy"):
            return

        if self._blink_progress < 0.0:
            self._blink_clock -= dt
            if self._blink_clock <= 0.0:
                self._blink_progress = 0.0
            return

        self._blink_progress += dt
        t = self._blink_progress
        if t < 0.06:
            w = t / 0.06
        elif t < 0.10:
            w = 1.0
        elif t < 0.22:
            w = 1.0 - (t - 0.10) / 0.12
        else:
            w = 0.0
            self._blink_progress = -1.0
            self._blink_clock = random.uniform(2.5, 6.5)
        self.morph.set_weight("まばたき", w)

    def _update_lipsync(self, dt: float) -> None:
        if self._lip_until <= 0.0:
            return
        if self._now() > self._lip_until:
            self.stop_talking()
            return
        self._lip_clock -= dt
        if self._lip_clock > 0.0:
            return
        self._lip_clock = random.uniform(0.07, 0.14)
        self._clear_vowels()
        if random.random() < 0.22:
            return
        name, _ = random.choice(expressions.VOWELS)
        self.morph.set_weight(name, random.uniform(0.35, 0.8))

    # ------------------------------------------------------------------ draw
    def draw(self, width: int, height: int) -> None:
        if not self.app:
            return
        cfg = self.cfg

        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = width / float(height) if height else 1.0
        glu.gluPerspective(cfg.cam_fov, aspect, 0.5, 400.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        breath = math.sin(self._breath * 1.4) * 0.25
        glu.gluLookAt(
            0.0, cfg.cam_height, -cfg.cam_distance,
            0.0, cfg.cam_height + breath * 0.2, 0.0,
            0.0, 1.0, 0.0,
        )
        gl.glTranslatef(cfg.offset_x, cfg.offset_y + breath, 0.0)
        gl.glScalef(cfg.scale, cfg.scale, cfg.scale)

        self.pose_arms()
        self.app.draw()

    # ------------------------------------------------------------- debugging
    def snapshot(self, path: str) -> None:
        vp = gl.glGetIntegerv(gl.GL_VIEWPORT)
        w, h = int(vp[2]), int(vp[3])
        gl.glReadBuffer(gl.GL_BACK)
        data = gl.glReadPixels(0, 0, w, h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        img = Image.frombytes("RGBA", (w, h), data)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(path)
