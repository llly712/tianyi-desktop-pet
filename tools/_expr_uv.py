import sys
sys.path.insert(0,"D:/tianyi-pet"); sys.path.insert(0,"D:/tianyi-pet/vendor")
import glfw
glfw.init(); glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
w=glfw.create_window(64,64,"x",None,None); glfw.make_context_current(w)
from mmdpy import mmdpy
m=mmdpy.model(); m.load("D:/tianyi-pet/models/tianyi_model/TID Blue Lolita.Ver.pmx")
out=[]
for mesh in m.model.meshes:
    if getattr(mesh,"name","")!="表情": continue
    v=mesh.vertex; uv=mesh.uv
    out.append("表情 nv=%d uv_full x[%.3f,%.3f] y[%.3f,%.3f]"%(len(v),min(u[0] for u in uv),max(u[0] for u in uv),min(u[1] for u in uv),max(u[1] for u in uv)))
    top=[(float(v[i][1]),float(v[i][0]),float(v[i][2]),float(uv[i][0]),float(uv[i][1])) for i in range(len(v)) if float(v[i][1])>17.5]
    if top:
        out.append("  top(y>17.5) n=%d  uv x[%.3f,%.3f] y[%.3f,%.3f]  x[%.2f,%.2f]"%(len(top),min(t[3] for t in top),max(t[3] for t in top),min(t[4] for t in top),max(t[4] for t in top),min(t[1] for t in top),max(t[1] for t in top)))
    low=[(float(uv[i][0]),float(uv[i][1]),float(v[i][1])) for i in range(len(v)) if float(v[i][1])<16.9]
    if low:
        out.append("  low(y<16.9) n=%d  uv x[%.3f,%.3f] y[%.3f,%.3f]"%(len(low),min(t[0] for t in low),max(t[0] for t in low),min(t[1] for t in low),max(t[1] for t in low)))
open("D:/tianyi-pet/_expr_uv.txt","w",encoding="utf-8").write("\n".join(out))
print("ok")
