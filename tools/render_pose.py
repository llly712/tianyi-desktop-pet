import os
import sys

ROOT = r"D:\tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "vendor"))

import glfw  # noqa: E402
import numpy as np  # noqa: E402
import OpenGL.GL as gl  # noqa: E402
import OpenGL.GLU as glu  # noqa: E402
from PIL import Image  # noqa: E402

W, H = 360, 540
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(W, H, "pose", None, None)
glfw.make_context_current(win)

from mmdpy import model as M  # noqa: E402

mdl = M(os.path.join(ROOT, "models", "tianyi_model", "TID Blue Lolita.Ver.pmx"))
core = mdl.model


def pose():
    for name, z in (("左腕", -1.30), ("右腕", 1.30), ("左ひじ", -0.20), ("右ひじ", 0.20)):
        b = core.get_bone_by_name(name)
        if b is not None:
            b.rotZ(z)
    core.update_bone()


def shoot(path):
    gl.glViewport(0, 0, W, H)
    gl.glClearColor(0.0, 0.0, 0.0, 0.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(30.0, W / H, 0.5, 400.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    glu.gluLookAt(0.0, 10.0, -42.0, 0.0, 10.0, 0.0, 0.0, 1.0, 0.0)
    mdl.draw()
    gl.glFlush()
    gl.glFinish()
    data = gl.glReadPixels(0, 0, W, H, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
    img = Image.frombytes("RGBA", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM)
    img.save(path)
    glfw.swap_buffers(win)


glfw.poll_events()
shoot(os.path.join(ROOT, "tools", "before.png"))
pose()
print("elbow", np.round(core.get_bone_by_name("左ひじ").get_global_matrix()[3, 0:3], 3).tolist())
shoot(os.path.join(ROOT, "tools", "after.png"))
glfw.terminate()
print("done")
