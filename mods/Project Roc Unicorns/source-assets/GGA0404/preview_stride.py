from pathlib import Path
import struct,sys
import numpy as np
from PIL import Image,ImageDraw
p=Path('mods/Project Roc Unicorns/source-assets/GGA0404').resolve();sys.path.insert(0,str(p));import model_helpers as h
u=p.parents[1]/'units/GGA0404';model=u/'GGA0404_lod0.scm'; raw=model.read_bytes();mh=struct.unpack_from('<4s11I',raw);pivots=[]
for i in range(mh[3]):
 b=struct.unpack_from('<16f3f4f4i',raw,mh[2]+i*108);pivots.append(-np.array(b[12:15]))
s=(u/'GGA0404_walk.sca').read_bytes();a=struct.unpack_from('<4siifiiiii',s);verts,faces=h.load_scm(model)
def rotate(q,v):
 v=np.asarray(v);xyz=q[1:];return v+2*np.cross(xyz,np.cross(xyz,v)+q[0]*v)
views=[]
for frame in (0,4,8,12,16,20):
 off=a[7]+28+frame*a[8]+8;vs=verts.copy()
 for bone in range(a[4]):
  v=struct.unpack_from('<3f4f',s,off+bone*28);pos=np.array(v[:3]);q=np.array(v[3:]);mask=verts[:,16]==bone
  vs[mask,:3]=rotate(q,verts[mask,:3]-pivots[bone])+pos
  for k in (3,6,9):vs[mask,k:k+3]=rotate(q,verts[mask,k:k+3])
 h.load_scm=lambda _: (vs,faces)
 out=p/f'GGA0404_step_{frame:02d}.png';print('render frame',frame,flush=True);h.render_scm(model,u,out,90,8,size=360);views.append(Image.open(out).convert('RGB'))
canvas=Image.new('RGB',(360*3,390*2),(20,22,26));draw=ImageDraw.Draw(canvas)
for i,v in enumerate(views):
 x=(i%3)*360;y=(i//3)*390;canvas.paste(v,(x,y+25));draw.text((x+8,y+5),f'frame {i*4:02d}',fill='white')
canvas.save(p/'GGA0404_stride_contact.png')
