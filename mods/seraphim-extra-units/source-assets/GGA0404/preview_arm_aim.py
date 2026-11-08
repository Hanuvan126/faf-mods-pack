from pathlib import Path
import struct,sys,numpy as np
from PIL import Image,ImageDraw
p=Path('mods/seraphim-extra-units/source-assets/GGA0404').resolve();sys.path.insert(0,str(p));import model_helpers as h
u=p.parents[1]/'units/GGA0404';f=u/'GGA0404_lod0.scm';raw=f.read_bytes();hdr=struct.unpack_from('<4s11I',raw);info=[]
for i in range(hdr[3]):
 b=struct.unpack_from('<16f3f4f4i',raw,hdr[2]+i*108);off=b[23];name=raw[off:raw.index(b'\0',off)].decode();info.append((name,-np.array(b[12:15]),b[24]))
lookup={name:i for i,(name,_,_) in enumerate(info)};v,faces=h.load_scm(f)
def rotate(v,yaw,pitch):
 a=np.radians(yaw);b=np.radians(pitch);cy,sy=np.cos(a),np.sin(a);cx,sx=np.cos(b),np.sin(b)
 return v@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]).T@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]).T
imgs=[]
for label,yaw,pitch in [('neutral',0,0),('right',40,-20),('left',-40,20)]:
 out=v.copy()
 for side in ('Left','Right'):
  idx=lookup[side+'ArmVisual'];pivot=info[idx][1];mask=v[:,16]==idx
  out[mask,:3]=rotate(v[mask,:3]-pivot,yaw,pitch)+pivot
  for k in (3,6,9):out[mask,k:k+3]=rotate(v[mask,k:k+3],yaw,pitch)
  aim=lookup[side+'Aim'];muzzle=lookup[side+'Muzzle'];assert np.allclose(info[idx][1],info[aim][1]);assert info[idx][2]==info[aim][2]
  print(side,label,'vertices',int(mask.sum()),'rotated muzzle',np.round(rotate(info[muzzle][1]-pivot,yaw,pitch)+pivot,3),flush=True)
 h.load_scm=lambda _: (out,faces);target=p/f'GGA0404_arm_{label}.png';h.render_scm(f,u,target,30,18,size=400);imgs.append(Image.open(target).convert('RGB'))
canvas=Image.new('RGB',(1200,425),(20,22,26));draw=ImageDraw.Draw(canvas)
for i,im in enumerate(imgs):canvas.paste(im,(400*i,25));draw.text((400*i+8,5),('neutral','yaw +40 / pitch -20','yaw -40 / pitch +20')[i],fill='white')
canvas.save(p/'GGA0404_arm_aim_views.png')
