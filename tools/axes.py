import io
import os
import sys

ROOT = r"D:\tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "vendor"))

import glfw  # noqa: E402
import numpy as np  # noqa: E402

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
_win = glfw.create_window(64, 64, "probe", None, None)
glfw.make_context_current(_win)

from mmdpy import model as M  # noqa: E402

m = M(os.path.join(ROOT, "models", "tianyi_model", "TID Blue Lolita.Ver.pmx"))
mdl = m.model

out = io.StringIO()
larm = mdl.get_bone_by_name("左腕")
if larm is not None:
    out.write(f"左腕 parent={larm.parent.name if larm.parent else None}\n")
for name in ["左腕", "左ひじ", "左肩"]:
    b = mdl.get_bone_by_name(name)
    if b is None:
        out.write(f"{name}: MISSING\n")
        continue
    out.write(f"{name}: parent={b.parent.name if b.parent else None}\n")

elbow = mdl.get_bone_by_name("左ひじ")


def reset():
    for name in ["左腕", "右腕", "左ひじ", "右ひじ", "左肩", "右肩"]:
        b = mdl.get_bone_by_name(name)
        if b is not None:
            b.delta_matrix = np.identity(4)


def elbow_pos():
    mdl.update_bone()
    return elbow.get_global_matrix()[3, 0:3]


reset()
base = elbow_pos()
out.write(f"base elbow={np.round(base, 3).tolist()}\n")

for axis in ("rotX", "rotY", "rotZ"):
    for sign in (1.0, -1.0):
        reset()
        getattr(larm, axis)(0.6 * sign)
        p = elbow_pos()
        out.write(f"左腕 {axis}({0.6*sign:+.1f}) -> elbow={np.round(p, 3).tolist()}\n")

reset()
lsh = mdl.get_bone_by_name("左肩")
if lsh is not None:
    for axis in ("rotX", "rotY", "rotZ"):
        for sign in (1.0, -1.0):
            reset()
            getattr(lsh, axis)(0.5 * sign)
            p = elbow_pos()
            out.write(f"左肩 {axis}({0.5*sign:+.1f}) -> elbow={np.round(p, 3).tolist()}\n")

with open(os.path.join(ROOT, "tools", "axes_out.txt"), "w", encoding="utf-8") as f:
    f.write(out.getvalue())
glfw.terminate()
print("done")
