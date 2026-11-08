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

for suffix in ['albedo','specteam','normalsTS']:
 original=Image.open(OUT/f'original/GGA2302_{suffix}.dds').convert('RGBA');original.save(OUT/f'original/{suffix}.png')
 im=Image.merge('RGBA',tuple(c.resize((512,512),Image.Resampling.LANCZOS) for c in original.split()))
 p=OUT/f'runtime/GGA2302_{suffix}.dds';dds(im,p);Image.open(p).save(OUT/f'decoded_lod0_{suffix}.png');Image.open(p).save(OUT/f'decoded_lod1_{suffix}.png')
