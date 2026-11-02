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
PIVOTS=[(0,0,0),(0,7.25,0),(0,0,1),(-1.35,0,12.06),(1.35,0,12.06)]

def beam(m,a,b,width,depth,bone=0,material='dark',sides=None):
    sides = sides or (8 if m.detail >= 16 else 6)
    a=np.array(a,float); b=np.array(b,float); axis=(b-a)/np.linalg.norm(b-a)
    trial=np.array((0.,1.,0.)) if abs(axis[1])<.9 else np.array((0.,0.,1.))
    u=np.cross(axis,trial); u/=np.linalg.norm(u); v=np.cross(axis,u)
    rings=[]
    for p in (a,b):
        rings.append([tuple(p+u*width*math.cos(i*2*math.pi/sides)+v*depth*math.sin(i*2*math.pi/sides)) for i in range(sides)])
    m.loft(rings,[a,b],bone,material)

def tapered(m, a, b, r0, r1, bone=0, material='armor', sides=6):
    """A solid tapered mechanical limb or claw with a near-pointed end."""
    a=np.asarray(a,float); b=np.asarray(b,float); axis=(b-a)/np.linalg.norm(b-a)
    trial=np.array((0.,1.,0.)) if abs(axis[1])<.9 else np.array((0.,0.,1.))
    u=np.cross(axis,trial); u/=np.linalg.norm(u); v=np.cross(axis,u)
    rings=[[tuple(p+r*(u*math.cos(2*math.pi*i/sides)+v*math.sin(2*math.pi*i/sides)))
            for i in range(sides)] for p,r in ((a,r0),(b,r1))]
    m.loft(rings,[a,b],bone,material)

def joint(m, p, tangent, radius):
    p=np.asarray(p,float); tangent=np.asarray(tangent,float)
    beam(m,p-tangent*.45,p+tangent*.45,radius,radius,0,'steel',12 if m.detail>=16 else 8)
    beam(m,p+tangent*.45,p+tangent*.51,radius*.62,radius*.62,0,'joint',12 if m.detail>=16 else 8)

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
        # The first two segments are coplanar: down 45 degrees, then up
        # at a right angle to the first; the shin descends to a pointed foot.
        radial=np.array((sx/math.sqrt(2),0,sz/math.sqrt(2)))
        tangent=np.array((-sz/math.sqrt(2),0,sx/math.sqrt(2)))
        hip=np.array((sx*2.45,5.65,sz*2.3))
        inner=hip+radial*2.15+np.array((0,-2.15,0))
        outer=inner+radial*2.65+np.array((0,2.65,0))
        ankle=outer+radial*1.15+np.array((0,-4.95,0))
        foot=outer+radial*1.65+np.array((0,-6.12,0))
        # Layered, tapered limbs leave the bent silhouette clearly readable.
        tapered(m,hip,inner,.72,.57,0,'dark',8)
        tapered(m,hip+np.array((0,.22,0)),inner+np.array((0,.22,0)),.55,.39,0,'armor',6)
        tapered(m,inner,outer,.66,.52,0,'dark',8)
        tapered(m,inner+np.array((0,.22,0)),outer+np.array((0,.22,0)),.47,.36,0,'armor',6)
        tapered(m,outer,ankle,.67,.43,0,'dark',8)
        tapered(m,outer+radial*.16,ankle+radial*.16,.48,.31,0,'armor',6)
        for p,r in ((hip,.73),(inner,.69),(outer,.8),(ankle,.43)):
            joint(m,p,tangent,r)
        # Split, ground-reaching talons and an outer swept-back armor spike.
        for side in (-1,1):
            base=ankle+tangent*(side*.23)
            tip=foot+tangent*(side*.38)
            tapered(m,base,tip,.29,.018,0,'edge',5)
        spikebase=outer+radial*.12+np.array((0,.05,0))
        spiketip=outer+radial*1.45+np.array((0,1.45,0))
        tapered(m,spikebase,spiketip,.43,.012,0,'armor',5)
        # Fine army-colour inset sits on the upper surface of the middle limb.
        tapered(m,inner+radial*.4+np.array((0,.55,0)),outer-radial*.35+np.array((0,.3,0)),.105,.07,0,'team',4)
    # Low armored housing. The roof is inset along both flanks and the rear;
    # the real connecting faces are sloped, not a texture or a flat box.
    lower=[(-3.1,6.4,-3.9),(3.1,6.4,-3.9),(3.9,6.4,-3.05),
           (3.9,6.4,3.4),(3.3,6.4,3.8),(-3.3,6.4,3.8),
           (-3.9,6.4,3.4),(-3.9,6.4,-3.05)]
    upper=[(-2.55,8.0,-3.05),(2.55,8.0,-3.05),(3.13,8.0,-2.45),
           (3.13,8.0,3.15),(2.85,8.0,3.55),(-2.85,8.0,3.55),
           (-3.13,8.0,3.15),(-3.13,8.0,-2.45)]
    m.loft([lower,upper],[(0,6.4,0),(0,8.0,0)],1,'armor')
    box(m,0,8.08,-.5,4.8,.16,4.45,1,'edge',.5)
    box(m,0,8.18,-.65,3.8,.08,3.1,1,'dark',.4)
    for sx in (-1,1):
      # Raised top strips follow the inset roof; player colour remains masked.
      box(m,sx*2.5,8.12,.05,.28,.17,2.8,1,'team')
      # Small rear equipment and vents stay within the sloped silhouette.
      box(m,sx*1.75,6.78,-3.85,1.2,.68,.45,1,'dark')
      for x in (sx*1.42,sx*2.08):
          box(m,x,6.78,-4.10,.38,.39,.08,1,'steel',.02)
      # The shared pitch rig holds both weapons. Barrels begin within the
      # front plate and taper continuously towards their forward muzzle.
      beam(m,(sx*1.35,7.25,2.8),(sx*1.35,7.25,3.9),.66,.66,2,'joint',detail)
      tapered(m,(sx*1.35,7.25,3.65),(sx*1.35,7.25,12.94),.53,.29,2,'steel',detail)
      tapered(m,(sx*1.35,7.25,12.92),(sx*1.35,7.25,13.0),.30,.285,2,'edge',detail)
      beam(m,(sx*1.35,7.25,13.0),(sx*1.35,7.25,13.02),.21,.21,2,'dark',detail)
    return m

def textures():
    # Near-black steel, dark recesses, graphite edges. SpecTeam R/G retain
    # reflective metal response; player-colour mask is the alpha of tile 4.
    colors=[(35,38,42),(14,16,19),(57,61,66),(47,51,55),(45,47,49),(28,30,33),(24,26,29),(9,11,13)]
    a=np.zeros((256,512,4),dtype=np.uint8); s=np.zeros_like(a); n=np.zeros_like(a)
    n[:]=(128,128,255,128)
    yy,xx=np.mgrid[0:128,0:128]
    for i,c in enumerate(colors):
      y=(i//4)*128; x=(i%4)*128
      # Controlled tonal variation resembles brushed steel without whitening it.
      variation=1.6*np.sin(xx*.43)+.8*np.sin(yy*.87+xx*.06)
      rgb=np.clip(np.asarray(c)[None,None,:]+variation[:,:,None],0,255).astype(np.uint8)
      a[y:y+128,x:x+128,:3]=rgb; a[y:y+128,x:x+128,3]=255
      spec=(170,165,4,255 if i==4 else 0) if i!=7 else (105,105,3,0)
      s[y:y+128,x:x+128,:]=spec
    for suffix,data in [('albedo',a),('specteam',s),('normalsTS',n)]:
      im=Image.fromarray(data); im.save(HERE/f'GRB2401_{suffix}_source.png')
      save_dds_dxt5(im,UNIT/f'GRB2401_{suffix}.dds',independent_channels=True)

def main():
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in [(0,16),(1,8)]:
      mesh=build(detail); write_scm(mesh,UNIT/f'GRB2401_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
      print('LOD',lod,'vertices',len(mesh.vertices),'triangles',len(mesh.indices)//3)
    textures()
    for name,az,el in [('front',0,15),('side',90,15),('rear',180,15),('top',0,80),('perspective',40,25)]:
      render_scm(UNIT/'GRB2401_lod0.scm',HERE,HERE/f'GRB2401_{name}.png',az,el,player=(.9,.08,.06),size=700)
    render_scm(UNIT/'GRB2401_lod0.scm',HERE,HERE/'GRB2401_blue_team.png',40,25,player=(.06,.23,.95),size=700)
    icon=Image.open(HERE/'GRB2401_perspective.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS)
    for folder in (HERE.parents[1]/'icons'/'units', HERE.parents[1]/'textures'/'ui'/'common'/'icons'/'units'):
      folder.mkdir(parents=True,exist_ok=True)
      save_dds_dxt5(icon,folder/'GRB2401_icon.dds')
if __name__=='__main__': main()


