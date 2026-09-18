
import OpenGL.GL as gl
import numpy as np
from . import mmdpy_shader
from . import mmdpy_type
from . import mmdpy_bone


class mmdpyMesh:
    def __init__(self, index: int, shader: mmdpy_shader.mmdpyShader,
                 vertex: list[mmdpy_type.mmdpyTypeVertex], face: list[int],
                 material: mmdpy_type.mmdpyTypeMaterial, bone: list[mmdpy_bone.mmdpyBone],
                 orig: list[int] | None = None):
        self.index: int = index
        self.shader: mmdpy_shader.mmdpyShader = shader
        self.both_side_flag = material.both_side_flag
        self.name: str = str(getattr(material, "name", ""))
        _low = self.name.lower()
        self.no_depth: bool = (
            self.name in ("眼白", "眼瞳", "eye_hi")
            or "eye" in _low
            or ("眼" in self.name and "眉" not in self.name)
        )
        ver: list[np.ndarray] = []
        uv: list[np.ndarray] = []
        bone_id: list[np.ndarray] = []
        bone_weight: list[np.ndarray] = []
        for v in vertex:
            ver.append(v.ver)
            uv.append(v.uv)
            bone_id.append(v.bone_id)
            bone_weight.append(v.bone_weight)

        self.vertex: np.ndarray = np.asarray(ver, dtype=np.float32)
        self.uv: np.ndarray = np.asarray(uv, dtype=np.float32)
        self.bone_id: np.ndarray = np.asarray(bone_id, dtype=np.float32)
        self.bone_weight: np.ndarray = np.asarray(bone_weight, dtype=np.float32)
        self.face: np.ndarray = np.asarray(face, dtype=np.uint16)
        self.orig_indices: np.ndarray = np.asarray(
            orig if orig is not None else [], dtype=np.int32)
        self.material: mmdpy_type.mmdpyTypeMaterial = material
        self.bone: list[mmdpy_bone.mmdpyBone] = bone
        self.glsl_info: mmdpy_type.glslInfoClass = self.shader.set_buffers(self.vertex, self.uv, self.face)
        self.shader.set_bone(self.glsl_info, self.bone_id, self.bone_weight)
        self.shader.set_texture(self.glsl_info, self.material.texture)
        self.shader.set_material(self.glsl_info, self.material)

    def draw(self) -> None:
        self.shader.set_bone_matrix(self.glsl_info, [x.local_matrix for x in self.bone])
        if self.no_depth:
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthMask(gl.GL_FALSE)
        else:
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthMask(gl.GL_TRUE)
        if self.both_side_flag or self.no_depth:
            gl.glDisable(gl.GL_CULL_FACE)
        else:
            gl.glEnable(gl.GL_CULL_FACE)
            gl.glFrontFace(gl.GL_CCW)
            # gl.glCullFace(gl.GL_FRONT)
            gl.glCullFace(gl.GL_BACK)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        self.shader.draw(self.glsl_info)
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_CULL_FACE)
