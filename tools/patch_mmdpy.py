"""Patch vendored mmdpy for desktop-pet needs.

1. mmdpy_shader.set_buffers: expose the position VBO id on glsl_info so morph
   updates can glBufferSubData into it.
2. mmdpy_mesh.mmdpyMesh: accept and store the original PMX vertex index for each
   local vertex, so morph deltas (keyed by original vertex id) can be mapped.
3. mmdpy_model.mmdpyModel.set_model: track that mapping while building meshes.

Idempotent: re-running is a no-op.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG = ROOT / "vendor" / "mmdpy"


def patch(path: pathlib.Path, old: str, new: str) -> bool:
    src = path.read_text(encoding="utf-8")
    if new in src:
        print(f"  already patched: {path.name}")
        return False
    if old not in src:
        print(f"  PATTERN NOT FOUND in {path.name}")
        sys.exit(1)
    path.write_text(src.replace(old, new, 1), encoding="utf-8")
    print(f"  patched: {path.name}")
    return True


def main() -> None:
    print("patching shader (expose position VBO)...")
    patch(
        PKG / "mmdpy_shader.py",
        "        glsl_info.glsl_vao = glsl_vao\n        glsl_info.face_size = face_size\n        return glsl_info",
        "        glsl_info.glsl_vao = glsl_vao\n"
        "        glsl_info.glsl_vbo_vertex = glsl_vbo_vertex\n"
        "        glsl_info.face_size = face_size\n        return glsl_info",
    )

    print("patching mesh (store original vertex indices)...")
    patch(
        PKG / "mmdpy_mesh.py",
        "                 material: mmdpy_type.mmdpyTypeMaterial, bone: list[mmdpy_bone.mmdpyBone]):",
        "                 material: mmdpy_type.mmdpyTypeMaterial, bone: list[mmdpy_bone.mmdpyBone],\n"
        "                 orig: list[int] | None = None):",
    )
    patch(
        PKG / "mmdpy_mesh.py",
        "        self.face: np.ndarray = np.asarray(face, dtype=np.uint16)",
        "        self.face: np.ndarray = np.asarray(face, dtype=np.uint16)\n"
        "        self.orig_indices: np.ndarray = np.asarray(\n"
        "            orig if orig is not None else [], dtype=np.int32)",
    )

    print("patching model (track mapping)...")
    patch(
        PKG / "mmdpy_model.py",
        "        new_vertex: list[mmdpy_type.mmdpyTypeVertex] = []\n        new_face: list[int] = []",
        "        new_vertex: list[mmdpy_type.mmdpyTypeVertex] = []\n        new_face: list[int] = []\n"
        "        new_orig: list[int] = []",
    )
    patch(
        PKG / "mmdpy_model.py",
        "                new_vertex = []\n                new_face = []",
        "                new_vertex = []\n                new_face = []\n                new_orig = []",
    )
    patch(
        PKG / "mmdpy_model.py",
        "                    new_vertex.append(v)",
        "                    new_vertex.append(v)\n                    new_orig.append(vi)",
    )
    patch(
        PKG / "mmdpy_model.py",
        "                mesh = mmdpy_mesh.mmdpyMesh(len(self.meshes), self.shader, new_vertex, new_face,\n"
        "                                            data.materials[material_id],\n"
        "                                            [self.bones[i] for i in new_bone_id if not i < 0])",
        "                mesh = mmdpy_mesh.mmdpyMesh(len(self.meshes), self.shader, new_vertex, new_face,\n"
        "                                            data.materials[material_id],\n"
        "                                            [self.bones[i] for i in new_bone_id if not i < 0],\n"
        "                                            new_orig)",
    )
    patch(
        PKG / "mmdpy_model.py",
        "        mesh = mmdpy_mesh.mmdpyMesh(len(self.meshes), self.shader, new_vertex, new_face,\n"
        "                                    data.materials[material_id],\n"
        "                                    [self.bones[i] for i in new_bone_id if not i < 0])\n"
        "        self.meshes.append(mesh)\n\n        return True",
        "        mesh = mmdpy_mesh.mmdpyMesh(len(self.meshes), self.shader, new_vertex, new_face,\n"
        "                                    data.materials[material_id],\n"
        "                                    [self.bones[i] for i in new_bone_id if not i < 0],\n"
        "                                    new_orig)\n"
        "        self.meshes.append(mesh)\n\n        return True",
    )
    print("patching adjust (sanitize material name)...")
    patch(
        PKG / "pmxpy_adjust.py",
        "        m = mmdpy_type.mmdpyTypeMaterial()\n        m.diffuse = np.array(mm.diffuse)",
        "        m = mmdpy_type.mmdpyTypeMaterial()\n"
        "        m.name = str(getattr(mm, \"name\", \"\")).replace(\"\\x00\", \"\")\n"
        "        m.diffuse = np.array(mm.diffuse)",
    )

    print("patching mesh (layer eyes without depth / cull)...")
    patch(
        PKG / "mmdpy_mesh.py",
        "        self.both_side_flag = material.both_side_flag\n        ver: list[np.ndarray] = []",
        "        self.both_side_flag = material.both_side_flag\n"
        "        self.name: str = str(getattr(material, \"name\", \"\"))\n"
        "        _low = self.name.lower()\n"
        "        self.no_depth: bool = (\n"
        "            self.name in (\"眼白\", \"眼瞳\", \"eye_hi\")\n"
        "            or \"eye\" in _low\n"
        "            or (\"眼\" in self.name and \"眉\" not in self.name)\n"
        "        )\n"
        "        ver: list[np.ndarray] = []",
    )
    patch(
        PKG / "mmdpy_mesh.py",
        "        if self.both_side_flag:\n"
        "            gl.glDisable(gl.GL_CULL_FACE)\n"
        "        else:\n"
        "            gl.glEnable(gl.GL_CULL_FACE)\n"
        "            gl.glFrontFace(gl.GL_CCW)\n"
        "            # gl.glCullFace(gl.GL_FRONT)\n"
        "            gl.glCullFace(gl.GL_BACK)",
        "        if self.no_depth:\n"
        "            gl.glEnable(gl.GL_DEPTH_TEST)\n"
        "            gl.glDepthMask(gl.GL_FALSE)\n"
        "        else:\n"
        "            gl.glEnable(gl.GL_DEPTH_TEST)\n"
        "            gl.glDepthMask(gl.GL_TRUE)\n"
        "        if self.both_side_flag or self.no_depth:\n"
        "            gl.glDisable(gl.GL_CULL_FACE)\n"
        "        else:\n"
        "            gl.glEnable(gl.GL_CULL_FACE)\n"
        "            gl.glFrontFace(gl.GL_CCW)\n"
        "            # gl.glCullFace(gl.GL_FRONT)\n"
        "            gl.glCullFace(gl.GL_BACK)",
    )
    print("done.")


if __name__ == "__main__":
    main()
