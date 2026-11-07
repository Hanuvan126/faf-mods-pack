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

nodes=j['nodes'][:106]; names=['GGA0404']+[n['name'] for n in nodes]+['OrbAim','OrbMuzzle','RightAim','RightMuzzle','LeftAim','LeftMuzzle','RightAirAim','RightAirMuzzle','LeftAirAim','LeftAirMuzzle']
parents=[-1]+[0]*len(nodes)+[2,107,99,109,101,111,99,113,101,115]
pivots=[(0,0,0)]+[tuple(n.get('translation',(0,0,0))) for n in nodes]+[(0,0,.3),(0,0,0),(0,0,3.6),(0,0,0),(0,0,3.6),(0,0,0),(0,0,3.6),(0,0,0),(0,0,3.6),(0,0,0)]
class Mesh:pass
mesh=Mesh();mesh.vertices=[];mesh.indices=[]
for index,node in enumerate(nodes):
 for prim in j['meshes'][node['mesh']]['primitives']:
  a=prim['attributes'];pos=accessor(a['POSITION']);normal=accessor(a['NORMAL']);uv=accessor(a['TEXCOORD_0']);inds=accessor(prim['indices']).reshape(-1); mat=prim.get('material',0);base=len(mesh.vertices)
  for p,n,t in zip(pos,normal,uv):
   n=n/max(np.linalg.norm(n),1e-10);basis=np.array([0.,1.,0.]) if abs(n[1])<.95 else np.array([1.,0.,0.]);tan=np.cross(basis,n);tan/=max(np.linalg.norm(tan),1e-10);bit=np.cross(n,tan)
   # The supplied body atlas occupies the left half; other materials use fixed swatches.
   tex=(float(t[0])*.49,float(t[1])) if mat==7 else (.55+(mat+.5)*.06,.5)
   mesh.vertices.append(tuple(p+np.array(pivots[index+1]))+tuple(n)+tuple(tan)+tuple(bit)+tex+tex+(index+1,))
  mesh.indices.extend((inds+base).tolist())
assert len(mesh.vertices)<65536
write_scm(mesh,OUT/'GGA0404_lod0.scm',names,parents,pivots)
# The source provides rigid node transforms. Scale animation affects only six tiny
# spark objects; SCM/SCA has no scale channel, so their scale is held at bind pose.
anim=j['animations'][0]; times=accessor(anim['samplers'][0]['input']).reshape(-1); samples={}
for ch in anim['channels']:
 i=ch['target']['node'];path=ch['target']['path'];
 if i>=106 or path=='scale':continue
 sam=anim['samplers'][ch['sampler']];assert np.allclose(accessor(sam['input']).reshape(-1),times);samples[(i,path)]=accessor(sam['output'])
frames=[]
for k in range(len(times)):
 frame=[((0,0,0),(1,0,0,0))]
 for i,n in enumerate(nodes):
  p=samples.get((i,'translation'));q=samples.get((i,'rotation'));pos=p[k] if p is not None else pivots[i+1]; r=q[k] if q is not None else (0,0,0,1);r=np.asarray(r,dtype=float);r/=max(np.linalg.norm(r),1e-12);frame.append((tuple(pos),(r[3],r[0],r[1],r[2])))
 frames.append(frame)
# Reverse the supplied cycle: the contact foot must move backward as the unit moves forward.
frames.reverse()
write_sca(OUT/'GGA0404_walk.sca',names[:107],parents[:107],frames,float(times[-1]))
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
print('vertices',len(mesh.vertices),'triangles',len(mesh.indices)//3,'bones',len(names),'frames',len(frames),'duration',times[-1]);print('bounds',np.min(np.asarray(mesh.vertices)[:,:3],axis=0),np.max(np.asarray(mesh.vertices)[:,:3],axis=0));print('animation loop max translation diff',max(np.linalg.norm(np.array(frames[0][i][0])-np.array(frames[-1][i][0])) for i in range(1,107)))
