from pathlib import Path
from PIL import Image
from io import BytesIO
import struct
OUT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())/'outputs/UyaIava_Optimization'
def dds(im,path):
 chunks=[];current=im;count=0
 while True:
  buf=BytesIO();current.save(buf,format='DDS',pixel_format='DXT5');data=buf.getvalue();chunks.append(data[128:]);count+=1
  if current.size==(1,1):break
  wh=(max(1,current.width//2),max(1,current.height//2));current=Image.merge('RGBA',tuple(c.resize(wh,Image.Resampling.LANCZOS) for c in current.split()))
 hdr=bytearray(data[:128]);struct.pack_into('<I',hdr,8,0xa1007);struct.pack_into('<4I',hdr,12,im.height,im.width,((im.width+3)//4)*((im.height+3)//4)*16,0);struct.pack_into('<I',hdr,28,count);struct.pack_into('<I',hdr,108,0x401008);path.write_bytes(hdr+b''.join(chunks))
for suffix in ['albedo','specteam','normalsTS']:
 original=Image.open(OUT/f'original/GGA1401_{suffix}.dds').convert('RGBA')
 im=Image.merge('RGBA',tuple(c.resize((512,512),Image.Resampling.LANCZOS) for c in original.split()))
 dds(im,OUT/f'runtime/GGA1401_{suffix}.dds')

