from pathlib import Path
import struct,json,math,re
import numpy as np
from PIL import Image
ROOT=Path('F:/FAF-Development/work/faf-upload');OUT=Path(__import__('os').environ.get('SHAVEYR_OPT_WORK',str(Path(__file__).resolve().parent/'work')));RUN=OUT/'runtime'
def scm(path):
 b=path.read_bytes();h=struct.unpack_from('<4s11I',b);r=np.array([struct.unpack_from('<16f4B',b,h[4]+68*i) for i in range(h[6])]);ix=np.array(struct.unpack_from('<%dH'%h[8],b,h[7])).reshape(-1,3);bones={}
 assert h[0]==b'MODL' and h[1]==5 and h[8]%3==0 and ix.max()<len(r)
 assert np.isfinite(r).all() and (r[:,16]<h[11]).all()
 assert np.max(np.abs(np.linalg.norm(r[:,3:6],axis=1)-1))<.001
 assert (np.linalg.norm(np.cross(r[ix[:,1],:3]-r[ix[:,0],:3],r[ix[:,2],:3]-r[ix[:,0],:3]),axis=1)>1e-8).all()
 for j in range(h[11]):
  q=struct.unpack_from('<16f3f4f4i',b,h[2]+108*j);name=b[q[23]:b.index(b'\0',q[23])].decode();bones[name]=q
 return r,ix,bones
old,oi,ob=scm(OUT/'original/GGA2302_lod0.scm');result={}
for lod,limits in [(0,(1,8500)),(1,(1,5000))]:
 r,ix,bones=scm(RUN/f'GGA2302_lod{lod}.scm');assert limits[0]<=len(r)<=limits[1];assert len(bones)==6
 for name,q in bones.items():assert np.allclose(q[:23],ob[name][:23]),name
 assert set(bones)==set(ob)
 assert (3500<=len(ix)<=4500) if lod==0 else (500<=len(ix)<=800)
 # Parent transforms and local pivots retained: this preserves every aim/slide/FX anchor.
 names=list(bones)
 for name,q in bones.items():
  parent=names[q[24]] if q[24]>=0 else None;oldnames=list(ob);oldparent=oldnames[ob[name][24]] if ob[name][24]>=0 else None;assert parent==oldparent
 sizes=[]
 for suffix in ['albedo','specteam','normalsTS']:
  p=RUN/f'GGA2302_{suffix}.dds';data=p.read_bytes();im=Image.open(p);w,h=im.size;count=struct.unpack_from('<I',data,28)[0];offset=128
  assert count==int(math.log2(max(w,h)))+1
  for _ in range(count):offset+=max(1,(w+3)//4)*max(1,(h+3)//4)*16;w=max(1,w//2);h=max(1,h//2)
  assert offset==len(data);sizes.append(len(data))
  if suffix=='albedo':assert np.asarray(im)[:,:,3].max()>200
 result[f'lod{lod}']=dict(vertices=len(r),triangles=len(ix),bones=len(bones),texture_bytes=sum(sizes),bounds_min=r[:,:3].min(0).tolist(),bounds_max=r[:,:3].max(0).tolist())
result['checks']=['SCM bounds and indices','finite coordinates and unit normals','nondegenerate triangles','6 bones and original transforms/parent names','vertex budgets','DDS headers, mip payloads and team masks']
result['game_test']='Not performed';(OUT/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
