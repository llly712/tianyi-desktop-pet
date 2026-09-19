import sys

ROOT = "D:/tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/vendor")

import glfw
from OpenGL import GL as gl
from PIL import Image

from app.config import Config
from app.renderer import PetRenderer

W, H = 360, 270
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "mouth2", None, None)
glfw.make_context_current(win)

cfg = Config()
cfg.auto_frame = False
cfg.window_width, cfg.window_height = W, H
r = PetRenderer(cfg)
r.load()
m = r.morph
m.reset()
m.update()

VARIANTS = [
    ("idle", []),
    ("kakuage0.85", [("口角上げ", 0.85)]),
    ("kakuage1.0", [("口角上げ", 1.0)]),
    ("nikori0.8", [("にこり", 0.8)]),
    ("nikori0.4", [("にこり", 0.4)]),
    ("smile_combo", [("口角上げ", 0.80), ("にこり", 0.35)]),
]


def render(pairs):
    m.reset()
    for name, wt in pairs:
        m.set_weight(name, wt)
    m.update()
    cfg.cam_fov = 22.0
    cfg.cam_height = 16.6
    cfg.cam_distance = 7.5
    gl.glClearColor(0.10, 0.10, 0.12, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    r.draw(W, H)
    gl.glFinish()
    gl.glReadBuffer(gl.GL_BACK)
    data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    return Image.frombytes("RGB", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM)


imgs = [render(p) for _, p in VARIANTS]
cols, rows = 3, 2
sheet = Image.new("RGB", (W * cols, H * rows), (20, 20, 20))
for i, im in enumerate(imgs):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(ROOT + "/mouth_sheet2.png")
print("saved mouth_sheet2.png order:", [n for n, _ in VARIANTS], flush=True)
