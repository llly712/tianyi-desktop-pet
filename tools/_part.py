import sys
sys.path.insert(0,"D:/tianyi-pet"); sys.path.insert(0,"D:/tianyi-pet/vendor")
import glfw
from OpenGL import GL as gl
from PIL import Image
import mmdpy.mmdpy_mesh as mm
_orig=mm.mmdpyMesh.draw
ONLY=sys.argv[1]
def patched(self):
    if getattr(self,"name","")!=ONLY: return
    return _orig(self)
mm.mmdpyMesh.draw=patched
from app.config import Config
from app.renderer import PetRenderer
W,H=800,800
glfw.init(); glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
win=glfw.create_window(W,H,"p",None,None); glfw.make_context_current(win)
cfg=Config(); cfg.auto_frame=False; cfg.window_width,cfg.window_height=W,H
r=PetRenderer(cfg); r.load(); r.set_expression("neutral"); r.morph.reset(); r.morph.update()
cfg.cam_fov,cfg.cam_height,cfg.cam_distance=15.0,17.2,6.0
gl.glClearColor(0,0,0,0); gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)
r.draw(W,H); gl.glFinish(); gl.glReadBuffer(gl.GL_BACK)
d=gl.glReadPixels(0,0,W,H,gl.GL_RGBA,gl.GL_UNSIGNED_BYTE)
im=Image.frombytes("RGBA",(W,H),d).transpose(Image.FLIP_TOP_BOTTOM)
bg=Image.new("RGB",(W,H),(40,60,80)); bg.paste(im,(0,0),im); bg.save("D:/tianyi-pet/part_%s.png"%ONLY.replace(" ","_"))
print("saved",ONLY)
