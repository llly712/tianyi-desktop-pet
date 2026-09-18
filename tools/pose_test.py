import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

import glfw  # noqa: E402
import numpy as np  # noqa: E402
import OpenGL.GL as gl  # noqa: E402
import OpenGL.GLU as glu  # noqa: E402
from PIL import Image  # noqa: E402
from mmdpy import model as MmdpyModel, pmxpy_load  # noqa: E402

MODEL = str(ROOT / "models/tianyi_model/TID Blue Lolita.Ver.pmx")
W, H = 360, 540

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "t", None, None)
glfw.make_context_current(win)

app = MmdpyModel(MODEL)
pmxpy_load.load(MODEL)

ys, xs = [], []
for mesh in app.model.meshes:
    v = np.asarray(mesh.vertex, dtype=float)
    ys += [float(v[:, 1].min()), float(v[:, 1].max())]
    xs += [float(v[:, 0].min()), float(v[:, 0].max())]
ymin, ymax = min(ys), max(ys)
cam_h = (ymin + ymax) / 2.0
fov = 30.0
aspect = W / float(H)
dist = ((ymax - ymin) * 1.2 / 2.0) / math.tan(math.radians(fov) / 2.0)
print(f"dist={dist:.2f} cam_h={cam_h:.2f} ymin={ymin:.2f} ymax={ymax:.2f}", flush=True)


def render(path, poses):
    m = app.model
    for name, z, x in poses:
        b = m.get_bone_by_name(name)
        if b is None:
            continue
        if z:
            b.rotZ(z)
        if x:
            b.rotX(x)
    m.update_bone()
    gl.glViewport(0, 0, W, H)
    gl.glClearColor(0.0, 0.0, 0.0, 0.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(fov, aspect, 0.5, 400.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    glu.gluLookAt(0, cam_h, -dist, 0, cam_h, 0, 0, 1, 0)
    app.draw()
    gl.glReadBuffer(gl.GL_BACK)
    data = gl.glReadPixels(0, 0, W, H, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
    img = Image.frombytes("RGBA", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM)
    img.save(path)
    print("saved", path, flush=True)


variants = {
    "g1_z35": [("左腕", -0.35, 0), ("右腕", 0.35, 0)],
    "g2_z50": [("左腕", -0.50, 0), ("右腕", 0.50, 0)],
    "g3_z65": [("左腕", -0.65, 0), ("右腕", 0.65, 0)],
    "g4_z50xf": [("左腕", -0.50, -0.30), ("右腕", 0.50, -0.30)],
    "g5_z50xb": [("左腕", -0.50, 0.30), ("右腕", 0.50, 0.30)],
    "g6_z50elbow": [("左腕", -0.50, 0), ("右腕", 0.50, 0), ("左ひじ", -0.35, 0), ("右ひじ", 0.35, 0)],
}
for name, poses in variants.items():
    render(str(ROOT / f"pose_{name}.png"), poses)

names = list(variants)
imgs = [Image.open(ROOT / f"pose_{n}.png").convert("RGBA") for n in names]
sheet = Image.new("RGBA", (W * 3, H * 2), (40, 40, 46, 255))
for i, im in enumerate(imgs):
    sheet.paste(im, ((i % 3) * W, (i // 3) * H), im)
sheet.save(ROOT / "pose_sheet.png")
print("sheet saved", flush=True)

glfw.terminate()
