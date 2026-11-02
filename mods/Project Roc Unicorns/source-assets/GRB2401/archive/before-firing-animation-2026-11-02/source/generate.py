from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from model_helpers import Mesh, render_scm
from supcom_binary import write_scm, write_sca, save_dds_dxt5

HERE=Path(__file__).resolve().parent
UNIT=HERE.parents[1]/'units'/'GRB2401'
NAMES=['GRB2401','Turret','Turret_Barrel','Muzzle_Left','Muzzle_Right']
PARENTS=[-1,0,1,2,2]
PIVOTS=[(0,0,0),(0,7.25,0),(0,0,1),(-1.35,0,12.06),(1.35,0,12.06)]
LEG_SIGNS=[(-1,-1),(-1,1),(1,-1),(1,1)]
for index,(sx,sz) in enumerate(LEG_SIGNS):
    radial=np.array((sx/math.sqrt(2),0,sz/math.sqrt(2)))
    hip=np.array((sx*2.45,5.65,sz*2.3))
    inner=hip+radial*2.15+np.array((0,-2.15,0))
    outer=inner+radial*2.65+np.array((0,2.65,0))
    start=len(NAMES)
    NAMES += [f'Leg{index}_Hip',f'Leg{index}_Inner',f'Leg{index}_Outer']
    PARENTS += [0,start,start+1]
    PIVOTS += [tuple(hip),tuple(inner-hip),tuple(outer-inner)]

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

def joint(m, p, tangent, radius, bone):
    p=np.asarray(p,float); tangent=np.asarray(tangent,float)
    beam(m,p-tangent*.45,p+tangent*.45,radius,radius,bone,'steel',12 if m.detail>=16 else 8)
    beam(m,p+tangent*.45,p+tangent*.51,radius*.62,radius*.62,bone,'joint',12 if m.detail>=16 else 8)

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
    for index,(sx,sz) in enumerate(LEG_SIGNS):
        hipbone=5+index*3; innerbone=hipbone+1; outerbone=hipbone+2
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
        tapered(m,hip,inner,.72,.57,hipbone,'dark',8)
        tapered(m,hip+np.array((0,.22,0)),inner+np.array((0,.22,0)),.55,.39,hipbone,'armor',6)
        tapered(m,inner,outer,.66,.52,innerbone,'dark',8)
        tapered(m,inner+np.array((0,.22,0)),outer+np.array((0,.22,0)),.47,.36,innerbone,'armor',6)
        tapered(m,outer,ankle,.67,.43,outerbone,'dark',8)
        tapered(m,outer+radial*.16,ankle+radial*.16,.48,.31,outerbone,'armor',6)
        for p,r,bone in ((hip,.73,hipbone),(inner,.69,innerbone),(outer,.8,outerbone),(ankle,.43,outerbone)):
            joint(m,p,tangent,r,bone)
        # Split, ground-reaching talons and an outer swept-back armor spike.
        for side in (-1,1):
            base=ankle+tangent*(side*.23)
            tip=foot+tangent*(side*.38)
            tapered(m,base,tip,.29,.018,outerbone,'edge',5)
        spikebase=outer+radial*.12+np.array((0,.05,0))
        spiketip=outer+radial*1.45+np.array((0,1.45,0))
        tapered(m,spikebase,spiketip,.43,.012,outerbone,'armor',5)
        # Fine army-colour inset sits on the upper surface of the middle limb.
        tapered(m,inner+radial*.4+np.array((0,.55,0)),outer-radial*.35+np.array((0,.3,0)),.105,.07,innerbone,'team',4)
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
    # Each tile is a small authored metal panel: seams, ribs, bolts and edge
    # wear. SpecTeam alpha is the player-colour mask used by the Insect shader.
    colors=[(37,40,44),(17,19,22),(61,65,69),(48,52,56),
            (46,48,51),(28,30,33),(24,26,29),(11,13,15)]
    albedo=Image.new('RGBA',(512,256)); spec=Image.new('RGBA',(512,256)); normals=Image.new('RGBA',(512,256),(128,128,255,128))
    ad=ImageDraw.Draw(albedo); sd=ImageDraw.Draw(spec)
    for i,c in enumerate(colors):
      x=(i%4)*128; y=(i//4)*128
      ad.rectangle((x,y,x+127,y+127),fill=(*c,255))
      sd.rectangle((x,y,x+127,y+127),fill=((105 if i==7 else 170),(105 if i==7 else 165),4,255 if i==4 else 0))
      if i not in (0,1,2,3): continue
      # Fine panel border, bracketed internal panels and rivets; no fixed
      # faction-colour pixels are baked into RGB.
      dark=(max(0,c[0]-18),max(0,c[1]-18),max(0,c[2]-18),255)
      light=(min(255,c[0]+18),min(255,c[1]+18),min(255,c[2]+18),255)
      ad.rectangle((x+5,y+5,x+122,y+122),outline=dark,width=2)
      ad.line([(x+8,y+9),(x+119,y+9)],fill=light,width=1)
      ad.line([(x+9,y+10),(x+9,y+119)],fill=light,width=1)
      ad.polygon([(x+16,y+24),(x+30,y+12),(x+98,y+12),(x+112,y+24),
                  (x+112,y+103),(x+98,y+115),(x+30,y+115),(x+16,y+103)],outline=dark,width=2)
      for yy in (18,110):
        for xx in (23,43,85,105):
          ad.ellipse((x+xx-2,y+yy-2,x+xx+2,y+yy+2),fill=dark)
          ad.point((x+xx-1,y+yy-1),fill=light)
      for yy in range(37,93,9):
          ad.line((x+27,y+yy,x+43,y+yy),fill=dark,width=3)
          ad.line((x+85,y+yy,x+101,y+yy),fill=dark,width=3)
      ad.line((x+50,y+31,x+77,y+31),fill=light,width=1)
      ad.line((x+49,y+32,x+49,y+93),fill=dark,width=2)
      ad.line((x+78,y+32,x+78,y+93),fill=dark,width=2)
      # Segmented team-color plates on primary armor, following Cybran reference.
      if i==0:
        for x0 in (16,88):
          sd.polygon([(x+x0,y+30),(x+x0+13,y+24),(x+x0+22,y+30),
                      (x+x0+22,y+73),(x+x0+13,y+80),(x+x0,y+74)],fill=(120,145,4,205))
          sd.line((x+x0+2,y+53,x+x0+20,y+53),fill=(140,150,4,0),width=2)
    for suffix,im in [('albedo',albedo),('specteam',spec),('normalsTS',normals)]:
      im.save(HERE/f'GRB2401_{suffix}_source.png')
      save_dds_dxt5(im,UNIT/f'GRB2401_{suffix}.dds',independent_channels=True)

def quaternion(axis,angle):
    axis=np.asarray(axis,float); axis/=np.linalg.norm(axis)
    return (math.cos(angle/2),*(axis*math.sin(angle/2)))

def rotation_matrix(q):
    w,x,y,z=q
    return np.array(((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
                     (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
                     (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y))))

# Speed and stride are coordinated in game units. During the 55% stance
# phase the foot moves backwards relative to the body at MOVE_SPEED.
MOVE_SPEED=2.2
MODEL_SCALE=.5
WALK_DURATION=1.05
STANCE_FRACTION=.55

def solve_leg(sx,sz,target,foot_vertices):
    radial=np.array((sx/math.sqrt(2),0,sz/math.sqrt(2)))
    tangent=np.array((-sz/math.sqrt(2),0,sx/math.sqrt(2)))
    hip=np.array((sx*2.45,5.65,sz*2.3))
    inner=hip+radial*2.15+np.array((0,-2.15,0))
    outer=inner+radial*2.65+np.array((0,2.65,0))
    tip=outer+radial*1.65+np.array((0,-6.12,0))
    delta=target-hip
    yaw=math.atan2(delta[0],delta[2])-math.atan2(radial[0],radial[2])
    yaw=(yaw+math.pi)%(2*math.pi)-math.pi
    q0=quaternion((0,1,0),yaw); r0=rotation_matrix(q0)
    p1=inner-hip; p2=outer-inner; p3=tip-outer
    # Solve a planar two-link chain after the fixed first segment. The
    # positive-elbow solution retains the original V-shaped leg silhouette.
    def at_height(y):
        r=math.hypot(delta[0],delta[2])-2.15
        v=y-hip[1]+2.15
        length1=math.hypot(2.65,2.65); length2=math.hypot(1.65,6.12)
        d=math.hypot(r,v)
        if not abs(length1-length2)+1e-6 < d < length1+length2-1e-6:
            raise ValueError(f'Unreachable foot target: {d}')
        alpha=math.atan2(v,r)+math.acos(np.clip((d*d+length1**2-length2**2)/(2*d*length1),-1,1))
        beta=math.atan2(v-length1*math.sin(alpha),r-length1*math.cos(alpha))
        theta=alpha-math.pi/4
        phi=beta-alpha-(math.atan2(-6.12,1.65)-math.pi/4)
        return quaternion(tangent,theta),quaternion(tangent,phi)
    q1,q2=at_height(target[1])
    # The two prongs have finite width and can rotate below the reference
    # tip. Raise the target slightly and resolve, without translating hips.
    for unused in range(4):
        r1=rotation_matrix(q1); r2=rotation_matrix(q2)
        posed=hip+(r0@(p1[:,None]+r1@(p2[:,None]+r2@(foot_vertices-outer).T))).T
        penetration=.015-float(posed[:,1].min())
        if penetration<=.00001: break
        target=target.copy();target[1]+=penetration+.001
        q1,q2=at_height(target[1])
    return (q0,q1,q2)

def walk_animation(mesh):
    # The clip owns only the four leg chains. Turret yaw/pitch stay free.
    selected=[0]+list(range(5,len(NAMES)))
    names=[NAMES[i] for i in selected]
    parents=[-1]+[0 if PARENTS[i]==0 else selected.index(PARENTS[i]) for i in selected[1:]]
    vertices=np.asarray(mesh.vertices); frames=[]
    stride=MOVE_SPEED*WALK_DURATION*STANCE_FRACTION/MODEL_SCALE
    for frame in range(85):
      phase=frame/84
      poses=[(PIVOTS[0],(1,0,0,0))]
      for leg,(sx,sz) in enumerate(LEG_SIGNS):
        t=(phase+(0 if sx*sz>0 else .5))%1
        if t<STANCE_FRACTION:
          zoffset=stride*(.5-t/STANCE_FRACTION); lift=0
        else:
          u=(t-STANCE_FRACTION)/(1-STANCE_FRACTION)
          smooth=u*u*(3-2*u)
          zoffset=stride*(smooth-.5); lift=1.0*math.sin(math.pi*u)
        radial=np.array((sx/math.sqrt(2),0,sz/math.sqrt(2)))
        hip=np.array(PIVOTS[5+leg*3]); outer=hip+np.array(PIVOTS[6+leg*3])+np.array(PIVOTS[7+leg*3])
        tip=outer+radial*1.65+np.array((0,-6.12,0))
        target=tip+np.array((0,lift,zoffset))
        index=5+leg*3; foot=vertices[vertices[:,16]==index+2,:3]
        rotations=solve_leg(sx,sz,target,foot)
        for j in range(3): poses.append((PIVOTS[index+j],rotations[j]))
      frames.append(poses)
    write_sca(UNIT/'GRB2401_walk.sca',names,parents,frames,WALK_DURATION)

def main():
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in [(0,16),(1,8)]:
      mesh=build(detail); write_scm(mesh,UNIT/f'GRB2401_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
      print('LOD',lod,'vertices',len(mesh.vertices),'triangles',len(mesh.indices)//3)
    textures()
    walk_animation(build(16))
    for name,az,el in [('front',0,15),('side',90,15),('rear',180,15),('top',0,80),('perspective',40,25)]:
      render_scm(UNIT/'GRB2401_lod0.scm',HERE,HERE/f'GRB2401_{name}.png',az,el,player=(.9,.08,.06),size=700)
    render_scm(UNIT/'GRB2401_lod0.scm',HERE,HERE/'GRB2401_blue_team.png',40,25,player=(.06,.23,.95),size=700)
    icon=Image.open(HERE/'GRB2401_perspective.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS)
    for folder in (HERE.parents[1]/'icons'/'units', HERE.parents[1]/'textures'/'ui'/'common'/'icons'/'units'):
      folder.mkdir(parents=True,exist_ok=True)
      save_dds_dxt5(icon,folder/'GRB2401_icon.dds')
if __name__=='__main__': main()


