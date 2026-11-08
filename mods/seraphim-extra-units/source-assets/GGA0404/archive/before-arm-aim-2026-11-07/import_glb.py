from pathlib import Path
import io,json,struct,math,sys
import numpy as np
from PIL import Image,ImageDraw
from supcom_binary import write_scm,write_sca,save_dds_dxt5
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'units'/'GGA0404'
data=(HERE/'seraphim-walker.glb').read_bytes()
_,version,total,jlen,_=struct.unpack_from('<4sIIII',data)
j=json.loads(data[20:20+jlen]); binstart=20+jlen+8; binary=data[binstart:]
assert version==2 and total==len(data)

def accessor(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]; types={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}; count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]; dtype=np.dtype(types[a['componentType']]); offset=v.get('byteOffset',0)+a.get('byteOffset',0); stride=v.get('byteStride',dtype.itemsize*count)
 return np.ndarray((a['count'],count),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize)).copy()

nodes=j['nodes'][:106]
anim=j['animations'][0]; times=accessor(anim['samplers'][0]['input']).reshape(-1); samples={}
for ch in anim['channels']:
 i=ch['target']['node'];path=ch['target']['path']
 if i>=106 or path=='scale':continue
 sam=anim['samplers'][ch['sampler']];assert np.allclose(accessor(sam['input']).reshape(-1),times);samples[(i,path)]=accessor(sam['output'])

# Merge nodes only when their source animations represent the same rigid motion.
# A rotating group additionally requires an identical pivot. Translation-only
# groups may use different pivots because their orientation never changes.
groups=[];node_group={}
for i,node in enumerate(nodes):
 p=np.array(node.get('translation',(0,0,0)));positions=samples[(i,'translation')]-p;rot=samples[(i,'rotation')]
 for group_index,g in enumerate(groups):
  rep=g[0];pivot=np.array(nodes[rep].get('translation',(0,0,0)));other=samples[(rep,'translation')]-pivot; r2=samples[(rep,'rotation')]
  same_pivot=np.allclose(p,pivot,atol=1e-5)
  no_rotation=np.allclose(rot[:,:3],0,atol=1e-6) and np.allclose(np.abs(rot[:,3]),1,atol=1e-6)
  if (same_pivot or no_rotation) and np.allclose(positions,other,atol=1e-5) and np.allclose(rot,r2,atol=1e-5):
   g.append(i);node_group[i]=group_index+1;break
 else:
  groups.append([i]);node_group[i]=len(groups)

names=['GGA0404']+[nodes[g[0]]['name'] for g in groups]
parents=[-1]+[0]*len(groups)
pivots=[(0,0,0)]+[tuple(nodes[g[0]].get('translation',(0,0,0))) for g in groups]
def add_aim(name,muzzle,parent_node,offset):
 parent=node_group[parent_node]; parent_pivot=np.array(pivots[parent]); target=np.array(nodes[parent_node]['translation'])+np.array(offset)
 aim=len(names);names.extend([name,muzzle]);parents.extend([parent,aim]);pivots.extend([tuple(target-parent_pivot),(0,0,0)])
add_aim('OrbAim','OrbMuzzle',1,(0,0,.3))
add_aim('RightAim','RightMuzzle',98,(0,0,3.6))
add_aim('LeftAim','LeftMuzzle',100,(0,0,3.6))
add_aim('RightAirAim','RightAirMuzzle',98,(0,0,3.6))
add_aim('LeftAirAim','LeftAirMuzzle',100,(0,0,3.6))
assert len(names)<=80, f'Exceeds mesh.fx bone palette: {len(names)}'
class Mesh:pass
mesh=Mesh();mesh.vertices=[];mesh.indices=[]
for index,node in enumerate(nodes):
 for prim in j['meshes'][node['mesh']]['primitives']:
  a=prim['attributes'];pos=accessor(a['POSITION']);normal=accessor(a['NORMAL']);uv=accessor(a['TEXCOORD_0']);inds=accessor(prim['indices']).reshape(-1);mat=prim.get('material',0);base=len(mesh.vertices)
  for p,n,t in zip(pos,normal,uv):
   n=n/max(np.linalg.norm(n),1e-10);basis=np.array([0.,1.,0.]) if abs(n[1])<.95 else np.array([1.,0.,0.]);tan=np.cross(basis,n);tan/=max(np.linalg.norm(tan),1e-10);bit=np.cross(n,tan)
   tex=(float(t[0])*.49,float(t[1])) if mat==7 else (.55+(mat+.5)*.06,.5)
   mesh.vertices.append(tuple(p+np.array(node['translation']))+tuple(n)+tuple(tan)+tuple(bit)+tex+tex+(node_group[index],))
  mesh.indices.extend((inds+base).tolist())
assert len(mesh.vertices)<65536
write_scm(mesh,OUT/'GGA0404_lod0.scm',names,parents,pivots)
# Rebuild the leg poses with a longer foot stride. 2D inverse kinematics
# preserves each original upper/lower leg length and the original joint gaps.
stride_factor = 2.2
def rotate_wxyz(q,v):
 q=np.asarray(q,dtype=float);v=np.asarray(v,dtype=float);xyz=q[1:]
 return v+2*np.cross(xyz,np.cross(xyz,v)+q[0]*v)
def point_at(pose,pivot,point):
 pos,quat=pose
 return np.asarray(pos)+rotate_wxyz(quat,np.asarray(point)-np.asarray(pivot))
def rotate_pose_x(pose,delta,pivot,anchor):
 pos,q=pose;w,x,y,z=q;c=math.cos(delta/2);t=math.sin(delta/2)
 rot=(c*w-t*x,c*x+t*w,c*y-t*z,c*z+t*y)
 fixed=point_at(pose,pivot,anchor)
 newpos=fixed-rotate_wxyz(rot,np.asarray(anchor)-np.asarray(pivot))
 return (tuple(newpos),rot)
def solve_knee(start,end,l1,l2,old_knee):
 # Coordinates are (y,z). Clamp to the reachable annulus, keeping the foot
 # at its requested height where possible.
 direction=end-start;distance=np.linalg.norm(direction)
 maxdist=l1+l2-1e-5;mindist=abs(l1-l2)+1e-5
 if distance>maxdist:
  dzmax=math.sqrt(max(0,maxdist*maxdist-direction[0]*direction[0]))
  direction[1]=np.clip(direction[1],-dzmax,dzmax);distance=np.linalg.norm(direction)
 if distance<mindist: direction*=mindist/max(distance,1e-8);distance=mindist
 unit=direction/distance; along=(l1*l1-l2*l2+distance*distance)/(2*distance)
 height=math.sqrt(max(0,l1*l1-along*along));perp=np.array((-unit[1],unit[0]))
 choices=(start+along*unit+height*perp,start+along*unit-height*perp)
 return min(choices,key=lambda v:np.linalg.norm(v-old_knee)),start+direction
frames=[]
for k in range(len(times)):
 frame=[((0,0,0),(1,0,0,0))]
 for group in groups:
  i=group[0];pos=samples[(i,'translation')][k];r=np.asarray(samples[(i,'rotation')][k],dtype=float);r/=max(np.linalg.norm(r),1e-12)
  frame.append((tuple(pos),(r[3],r[0],r[1],r[2])))
 for upper,knee,lower,foot in ((86,92,96,102),(87,93,97,103)):
  a,b,c,d=(node_group[x] for x in (upper,knee,lower,foot))
  original=frame[:]
  hip=np.asarray(nodes[upper]['translation'],dtype=float).copy();hip[1]=10.0
  knee_bind=np.asarray(nodes[knee]['translation'],dtype=float)
  foot_bind=np.asarray(nodes[foot]['translation'],dtype=float)
  h=point_at(original[a],pivots[a],hip)
  ku=point_at(original[a],pivots[a],knee_bind)
  kl=point_at(original[c],pivots[c],knee_bind)
  ankle=point_at(original[c],pivots[c],foot_bind)
  gap=kl-ku
  old_foot_z=point_at(original[d],pivots[d],foot_bind)[2]
  desired=ankle.copy();desired[2]+=(old_foot_z-foot_bind[2])*(stride_factor-1)
  start=h[1:3];end=(desired-gap)[1:3];oldk=ku[1:3]
  l1=np.linalg.norm(oldk-start);l2=np.linalg.norm((ankle-gap)[1:3]-oldk)
  newk,newend=solve_knee(start,end,l1,l2,oldk)
  angle=lambda v:math.atan2(v[1],v[0])
  da=angle(newk-start)-angle(oldk-start)
  dc=angle(newend-newk)-angle((ankle-gap)[1:3]-oldk)
  frame[a]=rotate_pose_x(original[a],da,pivots[a],hip)
  newku=point_at(frame[a],pivots[a],knee_bind)
  shift=newku-ku
  frame[b]=(tuple(np.asarray(original[b][0])+shift),original[b][1])
  lower_pose=rotate_pose_x(original[c],dc,pivots[c],knee_bind)
  frame[c]=(tuple(np.asarray(lower_pose[0])+shift),lower_pose[1])
  newankle=point_at(frame[c],pivots[c],foot_bind)
  frame[d]=(tuple(np.asarray(original[d][0])+newankle-ankle),original[d][1])
 frames.append(frame)
frames.reverse()
animated_count=1+len(groups)
write_sca(OUT/'GGA0404_walk.sca',names[:animated_count],parents[:animated_count],frames,float(times[-1]))
# Original GLB texture plus hand-authored, neutral Seraphim metal swatches.
v=j['bufferViews'][j['images'][0]['bufferView']];img=Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGB').resize((512,1024),Image.Resampling.LANCZOS)
albedo=Image.new('RGBA',(1024,1024),(100,110,120,0));albedo.paste(img,(0,0)); albedo.putalpha(0);d=ImageDraw.Draw(albedo)
colors=[(105,120,135),(143,150,152),(53,65,77),(75,158,225),(155,166,175),(73,83,92),(170,177,180)]
for i,c in enumerate(colors):
 x0=int((.55+i*.06)*1024);x1=int((.55+(i+1)*.06)*1024);d.rectangle((x0,0,x1,1023),fill=(*c,0))
# Fine player-colour accents on the explicit source energy swatch.
d.rectangle((int(.55*1024+3*.06*1024),440,int(.55*1024+4*.06*1024),570),fill=(*colors[3],200))
spec=Image.new('RGBA',(1024,1024),(155,155,0,0));normal=Image.new('RGBA',(1024,1024),(0,128,255,128))
if '--skip-textures' not in sys.argv:
 for label,im in [('albedo',albedo),('specteam',spec),('normalsTS',normal)]:save_dds_dxt5(im,OUT/f'GGA0404_{label}.dds',independent_channels=True)
print('vertices',len(mesh.vertices),'triangles',len(mesh.indices)//3,'bones',len(names),'frames',len(frames),'duration',times[-1]);print('bounds',np.min(np.asarray(mesh.vertices)[:,:3],axis=0),np.max(np.asarray(mesh.vertices)[:,:3],axis=0));print('animation loop max translation diff',max(np.linalg.norm(np.array(frames[0][i][0])-np.array(frames[-1][i][0])) for i in range(1,animated_count)))


