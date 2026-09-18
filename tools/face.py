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

W, H = 540, 810
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "face", None, None)
glfw.make_context_current(win)

cfg = Config()
cfg.auto_frame = False
r = PetRenderer(cfg)
r.load()

p = cfg.resolve_model()
raw = pmxpy_load.load(str(p))
print("raw attrs:", [k for k in dir(raw) if not k.startswith("__")], flush=True)
mats = getattr(raw, "materials", None) or getattr(raw, "material", None) or []
print("materials:", len(mats), flush=True)
for i, m in enumerate(mats):
    name = getattr(m, "name", "")
    tex = getattr(m, "texture_index", getattr(m, "texture", None))
    sph = getattr(m, "sphere_texture_index", None)
    mode = getattr(m, "sphere_mode", None)
    diff = getattr(m, "diffuse", None)
    alpha = getattr(m, "alpha", None)
    mark = ""
    low = str(name).lower()
    if any(k in str(name) for k in ("目", "瞳", "眼", "eye", "瞳")) or any(
        k in low for k in ("eye", "iris", "pupil", "hitomi")
    ):
        mark = "  <== EYE"
    print(
        f"{i:3d} name={name!r} tex={tex} sph={sph} mode={mode} diff={diff} alpha={alpha}{mark}",
        flush=True,
    )

cfg.cam_fov = 26.0
cfg.cam_height = 16.4
cfg.cam_distance = 8.6
gl.glClearColor(0.0, 0.0, 0.0, 1.0)
gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
r.draw(W, H)
gl.glFinish()
gl.glReadBuffer(gl.GL_BACK)
data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
img = Image.frombytes("RGB", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM)
img.save(ROOT + "/face.png")
print("saved face.png", flush=True)
