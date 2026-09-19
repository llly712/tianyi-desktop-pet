import sys
sys.path.insert(0,"D:/tianyi-pet"); sys.path.insert(0,"D:/tianyi-pet/vendor")
import glfw
glfw.init(); glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
w=glfw.create_window(64,64,"x",None,None); glfw.make_context_current(w)
from mmdpy import mmdpy
m=mmdpy.model(); m.load("D:/tianyi-pet/models/tianyi_model/TID Blue Lolita.Ver.pmx")
out=[]
for mesh in m.model.meshes:
    v=mesh.vertex
    xs=[float(p[0]) for p in v]; ys=[float(p[1]) for p in v]; zs=[float(p[2]) for p in v]
    mat=mesh.material
    out.append("%-14s tex=%s nv=%d bbox x[%.1f,%.1f] y[%.1f,%.1f]"%(getattr(mesh,"name",""),getattr(mat,"texture_index",None),len(v),min(xs),max(xs),min(ys),max(ys)))
open("D:/tianyi-pet/_meshes.txt","w",encoding="utf-8").write("\n".join(out))
print("ok", len(m.model.meshes))
