from pathlib import Path
from PIL import Image
from io import BytesIO
import struct
OUT=Path(__import__('os').environ.get('SHAVEYR_OPT_WORK',str(Path(__file__).resolve().parent/'work')))
def dds(im,path):
 chunks=[];current=im;count=0
 while True:
  buf=BytesIO();current.save(buf,format='DDS',pixel_format='DXT5');data=buf.getvalue();chunks.append(data[128:]);count+=1
  if current.size==(1,1):break
  wh=(max(1,current.width//2),max(1,current.height//2));current=Image.merge('RGBA',tuple(c.resize(wh,Image.Resampling.LANCZOS) for c in current.split()))
 hdr=bytearray(data[:128]);struct.pack_into('<I',hdr,8,0xa1007);struct.pack_into('<4I',hdr,12,im.height,im.width,((im.width+3)//4)*((im.height+3)//4)*16,0);struct.pack_into('<I',hdr,28,count);struct.pack_into('<I',hdr,108,0x401008);path.write_bytes(hdr+b''.join(chunks))


import json,math
from PIL import ImageDraw,ImageChops
curves=json.loads((OUT/'ornament_curves.json').read_text());mask=Image.new('L',(4096,4096));draw=ImageDraw.Draw(mask)
for c in curves:
 pts=[]
 for x,y,z in c['points']:
  if c['bone']==3:u,v=.02+.46*(x+2.5)/5,.15+.8*(y+2.5)/5
  else:
   ang=math.atan2(y,x);sector=round((ang+math.pi/2)/(2*math.pi/3));rel=(ang-(-math.pi/2+sector*2*math.pi/3)+math.pi)%(2*math.pi)-math.pi
   u,v=.52+.46*(rel*1.4+1.5)/3,.15+.8*z/2.5
  pts.append((u*4096,v*4096))
 width=max(5,round(c['width']*4096*(.092 if c['bone']==3 else .24)))
 for a,b in zip(pts,pts[1:]):
  if abs(a[0]-b[0])<1000:draw.line([a,b],fill=255,width=width)
mask=mask.resize((512,512),Image.Resampling.LANCZOS);mask.save(OUT/'baked_line_mask.png')
for suffix in ['albedo','specteam','normalsTS']:
 original=Image.open(OUT/f'original/GGA2302_{suffix}.dds').convert('RGBA')
 im=Image.merge('RGBA',tuple(c.resize((512,512),Image.Resampling.LANCZOS) for c in original.split()))
 if suffix=='albedo':im.putalpha(ImageChops.lighter(im.getchannel('A'),mask))
 if suffix=='specteam':
  team=original.getpixel((int(original.width*3.5/8),int(original.height*.05)))
  im=Image.composite(Image.new('RGBA',im.size,team),im,mask)
 p=OUT/f'runtime/GGA2302_{suffix}.dds';dds(im,p)
 for lod in [0,1]:Image.open(p).save(OUT/f'decoded_lod{lod}_{suffix}.png')
