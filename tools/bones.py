import os
import sys

ROOT = r"D:\tianyi-pet"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "vendor"))

import glfw  # noqa: E402

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
_win = glfw.create_window(64, 64, "probe", None, None)
glfw.make_context_current(_win)

from mmdpy import model as M  # noqa: E402

m = M(os.path.join(ROOT, "models", "tianyi_model", "TID Blue Lolita.Ver.pmx"))
names = [b.name for b in m.model.bones]
print("bones:", len(names))
hits = [n for n in names if "腕" in n or "ひじ" in n or "肩" in n]
print("arm-ish:", hits)
for probe in ["左腕", "右腕", "左ひじ", "右ひじ", "上半身", "頭", "首"]:
    print(probe, "->", probe in m.model.name2bone)
b = m.model.get_bone_by_name("左腕")
if b is not None:
    print("左腕 level:", b.get_level(), "parent:", b.parent.name if b.parent else None)
glfw.terminate()
