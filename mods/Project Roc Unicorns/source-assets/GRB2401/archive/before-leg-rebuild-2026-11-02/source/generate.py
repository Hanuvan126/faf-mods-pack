from pathlib import Path
import math
import numpy as np
from PIL import Image
from model_helpers import Mesh, render_scm
from supcom_binary import write_scm, save_dds_dxt5

HERE=Path(__file__).resolve().parent
UNIT=HERE.parents[1]/'units'/'GRB2401'
NAMES=['GRB2401','Turret','Turret_Barrel','Muzzle_Left','Muzzle_Right']
PARENTS=[-1,0,1,2,2]
PIVOTS=[(0,0,0),(0,8,0),(0,0,1),(-1.35,0,8),(1.35,0,8)]

def beam(m,a,b,width,depth,bone=0,material='dark',sides=None):
    sides = sides or (8 if m.detail >= 16 else 6)
    a=np.array(a,float); b=np.array(b,float); axis=(b-a)/np.linalg.norm(b-a)
    trial=np.array((0.,1.,0.)) if abs(axis[1])<.9 else np.array((0.,0.,1.))
    u=np.cross(axis,trial); u/=np.linalg.norm(u); v=np.cross(axis,u)
    rings=[]
    for p in (a,b):
        rings.append([tuple(p+u*width*math.cos(i*2*math.pi/sides)+v*depth*math.sin(i*2*math.pi/sides)) for i in range(sides)])
    m.loft(rings,[a,b],bone,material)

def box(m,x,y,z,w,h,d,bone=0,material='armor',bevel=.25):
    # Octagonal footprint produces actual chamfered armor edges.
    b=min(bevel,w*.3,d*.3); rings=[]
    for yy in (y-h/2,y+h/2):
        rings.append([(x-w/2+b,yy,z-d/2),(x+w/2-b,yy,z-d/2),(x+w/2,yy,z-d/2+b),(x+w/2,yy,z+d/2-b),(x+w/2-b,yy,z+d/2),(x-w/2+b,yy,z+d/2),(x-w/2,yy,z+d/2-b),(x-w/2,yy,z-d/2+b)])
    m.loft(rings,[(x,y-h/2,z),(x,y+h/2,z)],bone,material)

def build(detail):
    m=Mesh(detail)
    # Central undercarriage, four articulated mechanical legs, distinct ground contacts.
    box(m,0,4.0,0,6,1.5,6,0,'dark')
    m.column([(2.2,4.1),(2.8,4.6),(2.8,5.8),(2.4,6.2)],0,'joint',sides=detail)
    for sx in (-1,1):
      for sz in (-1,1):
        hip=(sx*2.4,4.4,sz*2.2); knee=(sx*5.1,3.35,sz*4.0); toe=(sx*6.0,.35,sz*4.8)
        beam(m,hip,knee,.65,.72,0,'dark'); beam(m,knee,toe,.55,.65,0,'dark')
        beam(m,(sx*2.7,4.85,sz*2.25),(sx*5.0,3.8,sz*3.9),.42,.38,0,'armor')
        beam(m,(sx*5.25,3.3,sz*4.1),(sx*6.05,.55,sz*4.85),.36,.42,0,'armor')
        beam(m,(sx*5.2,3.8,sz*4),(sx*5.2,3.8,sz*4.3),.75,.75,0,'steel')
        beam(m,(sx*5.2,3.8,sz*4.28),(sx*5.2,3.8,sz*4.36),.43,.43,0,'joint')
        box(m,sx*6.0,.27,sz*4.8,1.15,.55,1.6,0,'edge')
        beam(m,(sx*3.3,4.75,sz*2.75),(sx*4.7,4.0,sz*3.55),.12,.12,0,'team',4)
    # Broad low armored turret, raised panel layers, rear machinery and side vents.
    box(m,0,7.2,0,7.6,2.5,7.3,1,'armor',.7)
    box(m,0,8.6,-.6,6.2,.55,5.6,1,'edge',.65)
    box(m,0,8.94,-.7,4.8,.16,3.4,1,'dark')
    for sx in (-1,1):
      box(m,sx*3.85,7.1,-1.3,.42,1.4,3.2,1,'dark')
      for z in (-2.4,-1.9,-1.4,-.9,-.4): box(m,sx*4.08,7.1,z,.1,.9,.16,1,'steel',.02)
      box(m,sx*2.7,8.91,0,.45,.16,3.1,1,'team')
      box(m,sx*2.3,6.7,-4.0,1.5,1.4,1.05,1,'dark')
      for x in (sx*1.8,sx*2.8): box(m,x,6.6,-4.55,.55,.6,.2,1,'steel')
      # shared pitch joint ensures the two guns aim and fire as a pair
      beam(m,(sx*1.35,8,1),(sx*1.35,8,3.2),.88,.88,2,'joint',detail)
      beam(m,(sx*1.35,8,2.4),(sx*1.35,8,7.9),.49,.49,2,'steel',detail)
      beam(m,(sx*1.35,8,7.5),(sx*1.35,8,8.05),.63,.63,2,'edge',detail)
      beam(m,(sx*1.35,8,8.05),(sx*1.35,8,8.08),.42,.42,2,'dark',detail)
    return m

def textures():
    colors=[(63,65,67),(29,31,34),(90,93,95),(76,80,82),(74,74,76),(45,45,45),(35,35,35),(22,23,25)]
    a=np.zeros((256,512,4),dtype=np.uint8); s=np.zeros_like(a); n=np.zeros_like(a)
    n[:]=(128,128,255,128)
    for i,c in enumerate(colors):
      y=(i//4)*128; x=(i%4)*128
      a[y:y+128,x:x+128,:3]=c; a[y:y+128,x:x+128,3]=255
      s[y:y+128,x:x+128,:]=(130,120,8,255 if i==4 else 0)
    for suffix,data in [('albedo',a),('specteam',s),('normalsTS',n)]:
      im=Image.fromarray(data); im.save(HERE/f'GRB2401_{suffix}_source.png')
      save_dds_dxt5(im,UNIT/f'GRB2401_{suffix}.dds',independent_channels=True)

def main():
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in [(0,16),(1,8)]:
      mesh=build(detail); write_scm(mesh,UNIT/f'GRB2401_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
      print('LOD',lod,'vertices',len(mesh.vertices),'triangles',len(mesh.indices)//3)
    textures()
    for name,az,el in [('front',0,15),('side',90,15),('top',0,80),('perspective',40,25)]:
      render_scm(UNIT/'GRB2401_lod0.scm',HERE,HERE/f'GRB2401_{name}.png',az,el,player=(.9,.08,.06),size=700)
    icon=Image.open(HERE/'GRB2401_perspective.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS)
    for folder in (HERE.parents[1]/'icons'/'units', HERE.parents[1]/'textures'/'ui'/'common'/'icons'/'units'):
      folder.mkdir(parents=True,exist_ok=True)
      save_dds_dxt5(icon,folder/'GRB2401_icon.dds')
if __name__=='__main__': main()


