from pathlib import Path
import struct,json,hashlib
import numpy as np
from PIL import Image
OUT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())/'outputs/UyaIava_Optimization'
def read(p):
 raw=p.read_bytes();h=struct.unpack_from('<4s11I',raw)
 assert h[0]==b'MODL' and h[1]==5
 v=np.array([struct.unpack_from('<16f4B',raw,h[4]+68*i) for i in range(h[6])]);ix=np.frombuffer(raw,dtype='<u2',offset=h[7],count=h[8])
 assert len(ix)%3==0 and ix.max()<len(v) and np.isfinite(v).all()
 assert (v[:,16]<h[11]).all()
 assert np.max(np.abs(np.linalg.norm(v[:,3:6],axis=1)-1))<.001
 bones=[]
 for i in range(h[11]):
  b=list(struct.unpack_from('<16f3f4f4i',raw,h[2]+108*i));off=b[23];b[23]=raw[off:raw.index(b'\0',off)].decode();bones.append(b)
 return dict(vertices=h[6],triangles=h[8]//3,bones=h[11],bytes=len(raw)),bones,v
before,bb,bv=read(OUT/'original/GGA1401_lod0.scm');report={'before':before,'after':{},'textures':{}}
for lod in [0,1]:
 info,b,v=read(OUT/f'runtime/GGA1401_lod{lod}.scm');assert b==bb
 assert info['triangles']<(13000 if lod==0 else 3500)
 assert np.max(np.abs(v[:,:3].min(0)-bv[:,:3].min(0)))<2
 assert np.max(np.abs(v[:,:3].max(0)-bv[:,:3].max(0)))<2
 report['after']['lod'+str(lod)]=info
for suffix in ['albedo','specteam','normalsTS']:
 p=OUT/f'runtime/GGA1401_{suffix}.dds';data=p.read_bytes();im=Image.open(p);assert im.size==(512,512)
 assert data[84:88]==b'DXT5' and struct.unpack_from('<I',data,28)[0]==10
 assert len(data)==349680
 report['textures'][suffix]={'bytes':len(data),'dimensions':list(im.size),'mip_levels':10}
report['bone_records_unchanged']=True
report['game_tested']=False
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

