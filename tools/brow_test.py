import sys

ROOT = "D:/tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/vendor")

import glfw
from OpenGL import GL as gl
from PIL import Image

import mmdpy.mmdpy_mesh as mmdpy_mesh

_orig_draw = mmdpy_mesh.mmdpyMesh.draw


def patched_draw(self):
    if getattr(self, "name", "") == "hairshadow":
        return
    return _orig_draw(self)


mmdpy_mesh.mmdpyMesh.draw = patched_draw

from app.config import Config
from app.renderer import PetRenderer

W, H = 900, 900
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "brow", None, None)
glfw.make_context_current(win)

cfg = Config()
cfg.auto_frame = False
cfg.window_width, cfg.window_height = W, H
r = PetRenderer(cfg)
r.load()
r.set_expression("neutral")
r.morph.reset()
r.morph.update()

cfg.cam_fov, cfg.cam_height, cfg.cam_distance = 15.0, 17.2, 6.0
gl.glClearColor(0.35, 0.55, 0.75, 1.0)
gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
r.draw(W, H)
gl.glFinish()
gl.glReadBuffer(gl.GL_BACK)
data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
Image.frombytes("RGB", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM).save(ROOT + "/brow_noshadow.png")
print("saved brow_noshadow.png", flush=True)
