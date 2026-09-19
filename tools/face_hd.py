import sys

ROOT = "D:/tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/vendor")

import glfw
from OpenGL import GL as gl
from PIL import Image

from app.config import Config
from app.renderer import PetRenderer
from mmdpy import pmxpy_load

W, H = 900, 900
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "facehd", None, None)
glfw.make_context_current(win)

cfg = Config()
cfg.auto_frame = False
cfg.window_width, cfg.window_height = W, H
r = PetRenderer(cfg)
r.load()
r.set_expression("neutral")
m = r.morph
m.reset()
m.update()

raw = pmxpy_load.load(str(cfg.resolve_model()))
mats = getattr(raw, "materials", None) or getattr(raw, "material", None) or []
with open(ROOT + "/_mats.txt", "w", encoding="utf-8") as fh:
    for i, mm in enumerate(mats):
        fh.write(f"{i:3d} {getattr(mm,'name','')!r} tex={getattr(mm,'texture_index',None)}\n")
    fh.write("BROW MORPHS: " + repr([n for n in m.name2idx if "眉" in n or "まゆ" in n]) + "\n")
    fh.write("ALL MORPHS: " + repr(list(m.name2idx.keys())) + "\n")
print("wrote _mats.txt", flush=True)


def render(fov, hgt, dist, path):
    cfg.cam_fov = fov
    cfg.cam_height = hgt
    cfg.cam_distance = dist
    gl.glClearColor(0.10, 0.10, 0.12, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    r.draw(W, H)
    gl.glFinish()
    gl.glReadBuffer(gl.GL_BACK)
    data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    Image.frombytes("RGB", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM).save(path)
    print("saved", path, flush=True)


render(16.0, 16.9, 6.2, ROOT + "/face_hd.png")
render(8.0, 16.9, 4.2, ROOT + "/mouth_hd.png")
