from pathlib import Path
import math, re
import numpy as np
from PIL import Image,ImageDraw
from supcom_binary import write_scm,save_dds_dxt5,write_sca
from model_helpers import render_scm
HERE=Path(__file__).resolve().parent
SRC=HERE/'steampunk-source'
STAGE=HERE/'steampunk-build'
SCALE=2.0
MATERIALS=['Armor','ArmorLight','Edges','Steel','DarkMetal','Rust','RedOxide','Rubber','Brass','Copper','Cloth','Ivory','Lens','Lamp']
NAMES=['GRB2401','Turret','Turret_Barrel']; PARENTS=[-1,0,1]; PIVOTS=[(0,0,0),(0,5.0,0),(0,1.96,7.0)]
SIGNS=[(-1,-1),(-1,1),(1,-1),(1,1)]
for leg,(sx,sz) in enumerate(SIGNS):
    hip=np.array((sx*1.53103,1.85,sz*1.13794))*SCALE
    knee=np.array((sx*2.0815,.8,sz*1.7145))*SCALE
    ankle=np.array((sx*2.847,1.35,sz*2.338))*SCALE
    index=len(NAMES);NAMES += [f'Leg{leg}_Hip',f'Leg{leg}_Inner',f'Leg{leg}_Outer'];PARENTS += [0,index,index+1];PIVOTS += [tuple(hip),tuple(knee-hip),tuple(ankle-knee)]
LEFT_RELOAD=len(NAMES);LEFT_RECOIL=LEFT_RELOAD+1;RIGHT_RELOAD=LEFT_RELOAD+3;RIGHT_RECOIL=LEFT_RELOAD+4
NAMES += ['Reload_Left','Recoil_Left','Muzzle_Left','Reload_Right','Recoil_Right','Muzzle_Right','Aim_Muzzle']
PARENTS += [2,LEFT_RELOAD,LEFT_RECOIL,2,RIGHT_RELOAD,RIGHT_RECOIL,2]
PIVOTS += [(-1.476,0,0),(0,0,0),(0,0,13.35),(1.476,0,0),(0,0,0),(0,0,13.35),(0,0,13.35)]
# Foot plates may counter-rotate during the collapse; their collision
# detector markers follow these plates and do not override the walking rig.
FOOTVISUAL=len(NAMES)
for leg in range(4):
    NAMES.append(f'FootVisual{leg}');PARENTS.append(3+3*leg+2);PIVOTS.append((0,0,0))
for leg,(sx,sz) in enumerate(SIGNS):
    index=3+3*leg
    ankle=np.asarray(PIVOTS[index])+np.asarray(PIVOTS[index+1])+np.asarray(PIVOTS[index+2])
    foot=np.array((sx*3.33,-.06,sz*2.63))*SCALE
    NAMES.append(f'Foot{leg}');PARENTS.append(FOOTVISUAL+leg);PIVOTS.append(tuple(foot-ankle))
# Objects are removed whole, never by dropping individual faces. Major armor,
# legs, joints, gun barrels, and canvas boots survive both detail levels.
EXCLUDE=('rivet','paint_chip','chipped_paint','gear_tooth','fastener','flange_bolt','_bolt','_screw','piston_seal','gear_spoke','hull_corner_seam','roof_radiator_slat','bearing_rim','barbette_line_clamp','folded_canvas_gun_boot','socketed_circular_barbette','socketed_lower_base_rim','exhaust_flange','barbette_upper_perimeter_pipe','step_tread','barbette_ring_tooth','ankle_external_gear_web','ankle_external_gear_rim','barbette_contour_utility_line','gun_basket_semicircular_hoop')

def include(name,lod):
 n=name.lower()
 if any(x in n for x in EXCLUDE):return False
 for prefix,mod in [('gun_basket_semicircular_hoop',6 if lod==0 else 12),('barbette_contour_utility_line',5 if lod==0 else 10)]:
  if prefix in n:
   m=re.search(prefix+r'(\d+)',n);return bool(m and int(m.group(1))%mod==0)
 if lod==1 and any(w in n for w in ('_bearing_rim','_gear_rim','_gear_web','_hose','_pipe','_conduit','_cable','_cleat','_ladder','lifting_eye','sensor_rim','_bracket','_rail','cooling_fin','grille_rib','step_tread')):return False
 return True

def bone_for(name,center):
 s=name.lower()
 for index,(sx,sz) in enumerate(SIGNS):
  tag=('left' if sx<0 else 'right')+'_'+('rear' if sz<0 else 'front')+'_'
  if s.startswith(tag):
   k=3+3*index
   if any(x in s for x in ('foot','shoe')):return FOOTVISUAL+index
   if any(x in s for x in ('ankle','outer_piston','outer_pivot')):return k+2
   if any(x in s for x in ('lower_folded','knee','chrome_rod')):return k+1
   return k
 if any(x in s for x in ('main_long_barrel','main_gun_sleeve','gun_machined_collar','gun_muzzle_crown','deep_dark_barrel_bore')):
  return LEFT_RECOIL if center[0]<0 else RIGHT_RECOIL
 if any(x in s for x in ('folded_canvas_gun_boot','gun_basket')):
  return LEFT_RELOAD if center[0]<0 else RIGHT_RELOAD
 if s.startswith(('stationary_','socketed_','barbette_','lower_transmission')):return 0
 return 1

def norm(x):
 z=np.linalg.norm(x);return x/z if z>1e-10 else np.array((0.,1.,0.))

class IndexedMesh:
 def __init__(self):self.vertices=[];self.indices=[];self.cache={}
 def add(self,points,uvs,bone,mat):
  pts=np.array(points)*SCALE; uv=np.array(uvs); normal=norm(np.cross(pts[1]-pts[0],pts[2]-pts[0]))
  if np.linalg.norm(np.cross(pts[1]-pts[0],pts[2]-pts[0]))<1e-8:return
  tile=MATERIALS.index(mat) if mat in MATERIALS else 0
  # Textures repeat in source. Wrap each corner into the relevant material
  # tile; small seams on triangles crossing a repetition boundary remain a
  # documented limitation of this atlas conversion.
  uv=uv-np.floor(uv); uv[:,1]=1-uv[:,1]
  uv[:,0]=((tile%4)+.04+.92*uv[:,0])/4; uv[:,1]=((tile//4)+.04+.92*uv[:,1])/4
  e1,e2=pts[1]-pts[0],pts[2]-pts[0];a,b=uv[1]-uv[0],uv[2]-uv[0];det=a[0]*b[1]-a[1]*b[0]
  if abs(det)>1e-8: tangent=norm((e1*b[1]-e2*a[1])/det)
  else:tangent=norm(np.cross(normal,(0,1,.01)))
  tangent=norm(tangent-normal*np.dot(normal,tangent));bitangent=norm(np.cross(normal,tangent))
  for pos,tex in zip(pts,uv):
   entry=tuple(pos)+tuple(normal)+tuple(tangent)+tuple(bitangent)+tuple(tex)+tuple(tex)+(bone,)
   key=tuple(round(v,4) for v in entry[:6])+tuple(round(v,4) for v in entry[12:14])+(bone,)
   idx=self.cache.get(key)
   if idx is None:idx=len(self.vertices);self.cache[key]=idx;self.vertices.append(entry)
   self.indices.append(idx)

def build(lod):
 mesh=IndexedMesh();name='';mat='Armor';v=[];uv=[];count=0; omitted=0
 with (SRC/'SiegeWalker.obj').open(encoding='utf8') as f:
  for line in f:
   if line.startswith('o '):name=line[2:].strip()
   elif line.startswith('usemtl '):mat=line[7:].strip()
   elif line.startswith('v '):v.append(tuple(map(float,line.split()[1:4])));v=v[-3:]
   elif line.startswith('vt '):uv.append(tuple(map(float,line.split()[1:3])));uv=uv[-3:]
   elif line.startswith('f '):
    if include(name,lod):
     c=np.mean(v,axis=0);mesh.add(v,uv,bone_for(name,c),mat);count+=1
    else:omitted+=1
 # Replace the 6,912-triangle source gun boots with continuous low-poly
 # folded sleeves; they remain on the independent reload-pivot bones.
 for side in (-1,1):
  bone=LEFT_RELOAD if side<0 else RIGHT_RELOAD;cx=side*1.476;cy=6.96
  segments=12 if lod==0 else 8
  profile=[(5.10,.92,1.08),(5.65,1.04,1.15),(6.20,.86,1.00),
           (6.75,.98,1.08),(7.25,.80,.91),(7.82,.67,.74)]
  for j in range(len(profile)-1):
   z0,x0,y0=profile[j];z1,x1,y1=profile[j+1]
   for k in range(segments):
    a=2*math.pi*k/segments;b=2*math.pi*(k+1)/segments
    # mesh.add expects source-metres; all constants above are model units.
    corners=[(cx+x0*math.cos(a),cy+y0*math.sin(a),z0),
             (cx+x0*math.cos(b),cy+y0*math.sin(b),z0),
             (cx+x1*math.cos(b),cy+y1*math.sin(b),z1),
             (cx+x1*math.cos(a),cy+y1*math.sin(a),z1)]
    for ids in ((0,1,2),(0,2,3)):
      mesh.add([tuple(np.array(corners[t])/SCALE) for t in ids],[(.1,.1),(.9,.1),(.9,.9)],bone,'Cloth')
 print('LOD',lod,'retained',count,'omitted',omitted,'vertices',len(mesh.vertices),'faces',len(mesh.indices)//3,flush=True)
 return mesh

def textures():
 out=Image.new('RGBA',(512,512),(0,0,0,255));sp=Image.new('RGBA',(512,512),(160,160,0,0));normal=Image.new('RGBA',(512,512),(128,128,255,128))
 for i,mat in enumerate(MATERIALS):
  file=SRC/(mat+'_BaseColor.png')
  if file.exists():
   im=Image.open(file).convert('RGB').resize((128,128),Image.Resampling.LANCZOS)
   # Cybran PBR brightens metallic albedo; use dark, neutral graphite like
   # the Cybran reference rather than the original light steampunk armor.
   rgb=np.asarray(im,dtype=np.float32)
   lum=rgb[:,:,0]*.299+rgb[:,:,1]*.587+rgb[:,:,2]*.114
   im=Image.fromarray(np.uint8(np.clip(np.stack((lum*.43,lum*.42,lum*.44),axis=2),0,255))).convert('RGBA')
  else:im=Image.new('RGBA',(128,128),(150,30,30,255) if mat=='Lens' else (180,180,120,255))
  pos=((i%4)*128,(i//4)*128);out.paste(im,pos)
  tile=Image.new('RGBA',(128,128),(75,100,0,235 if mat=='RedOxide' else 0))
  if mat in ('Lamp','Lens'):tile=Image.new('RGBA',(128,128),(60,90,70,0))
  sp.paste(tile,pos)
 STAGE.mkdir(parents=True,exist_ok=True)
 for suffix,im in [('albedo',out),('specteam',sp),('normalsTS',normal)]:
  im.save(STAGE/f'GRB2401_{suffix}_source.png');save_dds_dxt5(im,STAGE/f'GRB2401_{suffix}.dds',independent_channels=True)

def quat(axis,angle):
 axis=np.asarray(axis,float);axis/=np.linalg.norm(axis)
 return (math.cos(angle/2),*(axis*math.sin(angle/2)))

def rot(axis,angle):
 w,x,y,z=quat(axis,angle)
 return np.array(((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
                  (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
                  (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y))))

def leg_pose(leg,angles):
 sx,sz=SIGNS[leg];i=3+3*leg;hip=np.asarray(PIVOTS[i]);p1=np.asarray(PIVOTS[i+1]);p2=np.asarray(PIVOTS[i+2]);
 # Ground contact point from the supplied foot casting, in model units.
 foot=np.array((sx*3.33,.04,sz*2.63))*SCALE
 # The specified .04 m should remain close to the actual sole at .02 m.
 foot[1]=.04
 tangent=np.array((-sz,0,sx),float);tangent/=np.linalg.norm(tangent)
 r0=rot((0,1,0),angles[0]);r1=rot(tangent,angles[1]);r2=rot(tangent,angles[2]);
 out=hip+r0@(p1+r1@(p2+r2@(foot-(hip+p1+p2))))
 return out,(r0,r1,r2),foot,tangent

def solve_foot(leg,target,initial):
 a=np.array(initial,float)
 for i in range(28):
  current,_,_,_=leg_pose(leg,a);error=target-current
  if np.linalg.norm(error)<.004:break
  jac=np.empty((3,3));step=.0001
  for j in range(3):
   nxt=a.copy();nxt[j]+=step;jac[:,j]=(leg_pose(leg,nxt)[0]-current)/step
  update=jac.T@np.linalg.solve(jac@jac.T+np.eye(3)*.0005,error)
  a+=np.clip(update,-.16,.16);a=np.clip(a,-1.4,1.4)
 return a,float(np.linalg.norm(leg_pose(leg,a)[0]-target))

def walk_animation(mesh):
 selected=[0]+list(range(3,15));names=[NAMES[i] for i in selected];parents=[-1]+[0 if PARENTS[i]==0 else selected.index(PARENTS[i]) for i in selected[1:]]
 vertices=np.asarray(mesh.vertices);frames=[];solutions=[np.zeros(3) for _ in SIGNS];first=None;max_error=0;low=999
 duration=1.05;stance=.55;stride=2.2*duration*stance/.5
 for frame in range(85):
  phase=frame/84;poses=[(PIVOTS[0],(1,0,0,0))]
  for leg,(sx,sz) in enumerate(SIGNS):
   t=(phase+(0 if sx*sz>0 else .5))%1
   if t<stance:z=stride*(.5-t/stance);lift=0
   else:
    q=(t-stance)/(1-stance);z=stride*(q*q*(3-2*q)-.5);lift=.7*math.sin(math.pi*q)
   base,_,foot,tangent=leg_pose(leg,(0,0,0));target=base+np.array((0,lift,z)); angles,error=solve_foot(leg,target,solutions[leg]);max_error=max(max_error,error)
   if frame==84 and first is not None:angles=first[leg].copy()
   # Keep all outer-leg geometry above flat ground by raising the target,
   # instead of disconnecting the hip from its mount.
   bone=3+3*leg;footverts=vertices[vertices[:,16]==FOOTVISUAL+leg,:3]
   hip=np.array(PIVOTS[bone]);p1=np.array(PIVOTS[bone+1]);p2=np.array(PIVOTS[bone+2]);outer=hip+p1+p2
   for _ in range(4):
    _,(r0,r1,r2),_,_=leg_pose(leg,angles)
    posed=hip+(r0@(p1[:,None]+r1@(p2[:,None]+r2@(footverts-outer).T))).T
    minimum=float(posed[:,1].min());correction=.01-minimum
    if correction<=.0001 or frame==84:break
    target[1]+=correction+.002;angles,error=solve_foot(leg,target,angles);max_error=max(max_error,error)
   low=min(low,minimum);solutions[leg]=angles.copy()
   rotations=[quat((0,1,0),angles[0]),quat(tangent,angles[1]),quat(tangent,angles[2])]
   for j in range(3):poses.append((PIVOTS[bone+j],rotations[j]))
  if frame==0:first=[x.copy() for x in solutions]
  frames.append(poses)
 print('walk max foot target error',round(max_error,4),'min height',round(low,4),flush=True)
 if max_error>.35 or low<-.02:raise ValueError('Walking IK failed clearance or convergence')
 write_sca(STAGE/'GRB2401_walk.sca',names,parents,frames,duration)

def multiply_quat(a,b):
 w,x,y,z=a;v,i,j,k=b
 return (w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v)

def death_animation(mesh):
    selected=[0]+list(range(3,15))+list(range(FOOTVISUAL,FOOTVISUAL+4))
    names=[NAMES[i] for i in selected]
    parents=[-1]+[0 if PARENTS[i]==0 else selected.index(PARENTS[i]) for i in selected[1:]]
    frames=[];solutions=[np.zeros(3) for _ in SIGNS];vertices=np.asarray(mesh.vertices);minimum=99;maxerr=0
    for frame in range(31):
      t=min(1.0,frame/24);ease=t*t*(3-2*t);drop=2.86*ease
      poses=[((0,-drop,0),(1,0,0,0))];footposes=[]
      for leg,(sx,sz) in enumerate(SIGNS):
        bone=3+3*leg;hip=np.array(PIVOTS[bone]);p1=np.array(PIVOTS[bone+1]);p2=np.array(PIVOTS[bone+2]);outer=hip+p1+p2
        radial=np.array((sx,0,sz),float);radial/=np.linalg.norm(radial)
        tangent=np.array((-sz,0,sx),float);tangent/=np.linalg.norm(tangent)
        tip=np.array((sx*3.33,.02,sz*2.63))*SCALE;relative=tip-outer
        def fk(a):
          r0=rot((0,1,0),a[0])@rot(tangent,a[1]);r1=rot(tangent,a[2]);rf=rot(tangent,-a[1]-a[2])
          return hip+r0@(p1+r1@(p2+rf@relative))
        target=tip+radial*(.8*ease)+np.array((0,drop,0));angles=solutions[leg].copy()
        for unused in range(45):
          err=target-fk(angles)
          if np.linalg.norm(err)<.004:break
          basis=np.eye(3)*.0001;current=fk(angles)
          jac=np.column_stack([(fk(angles+basis[j])-current)/.0001 for j in range(3)])
          update=jac.T@np.linalg.solve(jac@jac.T+np.eye(3)*.0001,err)
          angles+=np.clip(update,-.2,.2);angles=np.clip(angles,-1.5,1.5)
        maxerr=max(maxerr,float(np.linalg.norm(target-fk(angles))))
        solutions[leg]=angles.copy()
        hiprot=multiply_quat(quat((0,1,0),angles[0]),quat(tangent,angles[1]))
        rotations=[hiprot,quat(tangent,angles[2]),(1,0,0,0)]
        for j in range(3):poses.append((PIVOTS[bone+j],rotations[j]))
        footposes.append((PIVOTS[FOOTVISUAL+leg],quat(tangent,-angles[1]-angles[2])))
        footverts=vertices[vertices[:,16]==FOOTVISUAL+leg,:3]
        r0=rot((0,1,0),angles[0])@rot(tangent,angles[1]);r1=rot(tangent,angles[2]);rf=rot(tangent,-angles[1]-angles[2])
        points=hip+(r0@(p1[:,None]+r1@(p2[:,None]+rf@(footverts-outer).T))).T
        minimum=min(minimum,float(points[:,1].min())-drop)
      frames.append(poses+footposes)
    print('death clip max foot error',round(maxerr,4),'lowest foot',round(minimum,4),flush=True)
    if maxerr>.05 or minimum<-.04:raise ValueError('Death pose solver failed')
    write_sca(STAGE/'GRB2401_death.sca',names,parents,frames,3.0)

def main():
 STAGE.mkdir(parents=True,exist_ok=True)
 for lod in (0,1):
  mesh=build(lod)
  if len(mesh.vertices)>65535:raise ValueError('Too many vertices for SCM: '+str(len(mesh.vertices)))
  write_scm(mesh,STAGE/f'GRB2401_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
  if lod==0:
   walk_animation(mesh)
   death_animation(mesh)
 textures()
 for name,az,el in [('perspective',40,22),('front',0,15),('side',90,15),('top',0,80)]:
  render_scm(STAGE/'GRB2401_lod0.scm',STAGE,STAGE/f'GRB2401_{name}.png',az,el,player=(.9,.08,.06),size=700)
if __name__=='__main__':main()


