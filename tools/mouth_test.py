import sys

ROOT = "D:/tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/vendor")

import glfw
from OpenGL import GL as gl
from PIL import Image

from app.config import Config
from app.renderer import PetRenderer

W, H = 400, 300
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "mouth", None, None)
glfw.make_context_current(win)

cfg = Config()
cfg.auto_frame = False
cfg.window_width, cfg.window_height = W, H
r = PetRenderer(cfg)
r.load()
m = r.morph

NAMES = ["(idle)", "笑い", "にっこり", "にこり", "にやり", "口角上げ"]


def render(morph_name):
    m.reset()
    if morph_name != "(idle)":
        m.set_weight(morph_name, 0.8)
    m.update()
    cfg.cam_fov = 18.0
    cfg.cam_height = 17.2
    cfg.cam_distance = 5.4
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    r.draw(W, H)
    gl.glFinish()
    gl.glReadBuffer(gl.GL_BACK)
    data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    return Image.frombytes("RGB", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM)


imgs = [render(n) for n in NAMES]
cols, rows = 3, 2
sheet = Image.new("RGB", (W * cols, H * rows), (20, 20, 20))
for i, im in enumerate(imgs):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(ROOT + "/mouth_sheet.png")
print("saved", NAMES, flush=True)
