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
win = glfw.create_window(W, H, "eye", None, None)
glfw.make_context_current(win)

cfg = Config()
cfg.auto_frame = False
cfg.cam_fov = 26.0
cfg.cam_height = 18.3
cfg.cam_distance = 5.2
r = PetRenderer(cfg)
r.load()
raw = pmxpy_load.load(str(cfg.resolve_model()))
tn = getattr(raw, "texture_name", [])
print("textures:", list(enumerate(tn)), flush=True)

raw_names = [str(getattr(m, "name", "")) for m in getattr(raw, "material", [])]
uniq: list = []
for mesh in r.app.model.meshes:
    if all(mesh.material is not u for u in uniq):
        uniq.append(mesh.material)
name_of = {}
for i, mat in enumerate(uniq):
    name_of[id(mat)] = raw_names[i] if i < len(raw_names) else f"mat{i}"
print("material objects:", len(uniq), "raw:", len(raw_names), flush=True)

import numpy as np

for mesh in r.app.model.meshes:
    nm = name_of.get(id(mesh.material), "?")
    if nm in ("臉", "眼白", "眼瞳", "eye_hi", "表情", "hairshadow", "cheek"):
        v = np.asarray(mesh.vertex)
        uv = np.asarray(mesh.uv)
        print(
            f"MESH {nm}: verts={len(v)} faces={len(mesh.face)} "
            f"pos={np.round(v.min(0), 2).tolist()}..{np.round(v.max(0), 2).tolist()} "
            f"uv={np.round(uv.min(0), 3).tolist()}..{np.round(uv.max(0), 3).tolist()} "
            f"texpath={getattr(mesh.material, 'texture_path', '?')} "
            f"both={getattr(mesh.material, 'both_side_flag', '?')}",
            flush=True,
        )


def mname(m):
    return name_of.get(id(m.material), "?")


def render(path, exclude=(), only=None):
    saved = list(r.app.model.meshes)
    if only is not None:
        r.app.model.meshes = [m for m in saved if mname(m) in only]
    elif exclude:
        r.app.model.meshes = [m for m in saved if mname(m) not in exclude]
    gl.glClearColor(0, 0, 0, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    r.draw(W, H)
    gl.glFinish()
    gl.glReadBuffer(gl.GL_BACK)
    data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    Image.frombytes("RGB", (W, H), data).transpose(Image.FLIP_TOP_BOTTOM).save(path)
    r.app.model.meshes = saved
    print("saved", path, flush=True)


render(ROOT + "/face_a.png")
render(ROOT + "/face_b.png", exclude=("eye_hi",))
render(ROOT + "/face_c.png", only=("臉", "眼白", "眼瞳"))
render(ROOT + "/face_d.png", only=("眼瞳", "eye_hi"))
render(ROOT + "/face_e.png", only=("眼白",))

from mmdpy import mmdpy_mesh


def draw_flat(self):
    self.shader.set_bone_matrix(self.glsl_info, [x.local_matrix for x in self.bone])
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    self.shader.draw(self.glsl_info)
    gl.glDisable(gl.GL_TEXTURE_2D)


mmdpy_mesh.mmdpyMesh.draw = draw_flat
render(ROOT + "/face_f.png", only=("臉", "眼白", "眼瞳", "eye_hi"))
