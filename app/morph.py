"""CPU vertex-morph support for mmdpy (mmdpy has no morph handling at all).

mmdpyMesh stores each vertex's original PMX index (see tools/patch_mmdpy.py), so
morph deltas keyed by PMX vertex id can be mapped back onto the split meshes and
pushed into the position VBO with glBufferSubData.
"""
from __future__ import annotations

import numpy as np
import OpenGL.GL as gl

MORPH_GROUP = 0
MORPH_VERTEX = 1


class MorphController:
    def __init__(self, mmd_model, raw_pmx) -> None:
        self.model = mmd_model
        self.meshes = list(mmd_model.meshes)
        self.base = [np.array(m.vertex, dtype=np.float32, copy=True) for m in self.meshes]

        # original vertex id -> [(mesh_index, local_index), ...]
        self.v2loc: dict[int, list[tuple[int, int]]] = {}
        for mi, mesh in enumerate(self.meshes):
            for li, oi in enumerate(mesh.orig_indices.tolist()):
                self.v2loc.setdefault(int(oi), []).append((mi, li))

        self.names: list[str] = []
        self.types: list[int] = []
        self.payload: list[list] = []
        self.name2idx: dict[str, int] = {}

        for mo in raw_pmx.morph:
            i = len(self.names)
            name = mo.name
            self.names.append(name)
            self.types.append(mo.type)
            if mo.type == MORPH_VERTEX:
                self.payload.append(
                    [(int(v.vertex_id), float(v.vertex[0]), float(v.vertex[1]), float(v.vertex[2]))
                     for v in mo.vertex]
                )
            elif mo.type == MORPH_GROUP:
                self.payload.append([(int(g.grouo_id), float(g.morph_rate)) for g in mo.group])
            else:
                self.payload.append([])
            if name and name not in self.name2idx:
                self.name2idx[name] = i
            eng = getattr(mo, "eng_name", "") or ""
            if eng and eng not in self.name2idx:
                self.name2idx[eng] = i

        self.weights = np.zeros(len(self.names), dtype=np.float32)
        self._leaf_deltas: dict[int, dict[int, tuple[np.ndarray, np.ndarray]]] = {}
        self._dirty = True
        self._last_changed: set[int] = set()

    # -- queries -----------------------------------------------------------
    def has(self, name: str) -> bool:
        return name in self.name2idx

    def weight_of(self, name: str) -> float:
        i = self.name2idx.get(name)
        return float(self.weights[i]) if i is not None else 0.0

    # -- mutation ----------------------------------------------------------
    def set_weight(self, name: str, weight: float) -> bool:
        i = self.name2idx.get(name)
        if i is None:
            return False
        w = max(0.0, min(1.0, float(weight)))
        if abs(float(self.weights[i]) - w) > 1e-6:
            self.weights[i] = w
            self._dirty = True
        return True

    def add_weight(self, name: str, weight: float) -> bool:
        i = self.name2idx.get(name)
        if i is None:
            return False
        return self.set_weight(name, float(self.weights[i]) + float(weight))

    def reset(self) -> None:
        if np.any(self.weights):
            self.weights[:] = 0.0
            self._dirty = True

    # -- internals ---------------------------------------------------------
    def _leaf_delta(self, i: int) -> dict[int, tuple[np.ndarray, np.ndarray]]:
        cached = self._leaf_deltas.get(i)
        if cached is not None:
            return cached
        per_mesh: dict[int, list[tuple[int, float, float, float]]] = {}
        for vid, dx, dy, dz in self.payload[i]:
            for mi, li in self.v2loc.get(vid, ()):
                per_mesh.setdefault(mi, []).append((li, dx, dy, dz))
        out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        for mi, items in per_mesh.items():
            arr = np.asarray(items, dtype=np.float32)
            out[mi] = (arr[:, 0].astype(np.int64), arr[:, 1:4])
        self._leaf_deltas[i] = out
        return out

    def _effective_weights(self) -> np.ndarray:
        eff = np.zeros(len(self.names), dtype=np.float32)

        def rec(i: int, w: float, depth: int) -> None:
            if depth > 8 or w == 0.0:
                return
            if self.types[i] == MORPH_VERTEX:
                eff[i] += w
            elif self.types[i] == MORPH_GROUP:
                for child, rate in self.payload[i]:
                    if 0 <= child < len(self.names):
                        rec(child, w * rate, depth + 1)

        for i, w in enumerate(self.weights):
            if w:
                rec(i, float(w), 0)
        return eff

    def update(self) -> None:
        if not self._dirty:
            return
        self._dirty = False

        eff = self._effective_weights()
        active = np.nonzero(eff > 1e-6)[0]

        pos = [b.copy() for b in self.base]
        changed: set[int] = set()
        for i in active.tolist():
            w = float(eff[i])
            for mi, (li, delta) in self._leaf_delta(i).items():
                pos[mi][li] += w * delta
                changed.add(mi)

        for mi in changed | self._last_changed:
            buf = pos[mi]
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.meshes[mi].glsl_info.glsl_vbo_vertex)
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, buf.nbytes, buf)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        self._last_changed = changed
