from pathlib import Path
from PIL import Image,ImageDraw
from io import BytesIO
import numpy as np,struct,json
OUT=Path(__import__('os').environ.get('DUSH_OPT_WORK', str(Path(__file__).resolve().parent/'work')));RUN=OUT/'runtime'
def dds(im,path):
 chunks=[];current=im;count=0
 while True:
  buf=BytesIO();current.save(buf,format='DDS',pixel_format='DXT5');data=buf.getvalue();chunks.append(data[128:]);count+=1
  if current.size==(1,1):break
  wh=(max(1,current.width//2),max(1,current.height//2));current=Image.merge('RGBA',tuple(c.resize(wh,Image.Resampling.LANCZOS) for c in current.split()))
 hdr=bytearray(data[:128]);struct.pack_into('<I',hdr,8,0xa1007);struct.pack_into('<4I',hdr,12,im.height,im.width,((im.width+3)//4)*((im.height+3)//4)*16,0);struct.pack_into('<I',hdr,28,count);struct.pack_into('<I',hdr,108,0x401008);path.write_bytes(hdr+b''.join(chunks))
b=(OUT/'original/GGA0401_lod0.scm').read_bytes();h=struct.unpack_from('<4s11I',b);rows=[struct.unpack_from('<16f4B',b,h[4]+i*68) for i in range(h[6])];ii=struct.unpack_from('<%dH'%h[8],b,h[7]);proj=json.loads((OUT/'projection.json').read_text())
mask=Image.new('L',(2048,2048));draw=ImageDraw.Draw(mask)
for k in range(0,len(ii),3):
 tri=[rows[i] for i in ii[k:k+3]];r=tri[0]
 if r[16]!=0 or r[13]<.5 or int(r[12]*8)!=4:continue
 xy=[(((v[0]-proj['xmin'])/(proj['xmax']-proj['xmin'])*.96+.02)*2048,((v[2]-proj['zmin'])/(proj['zmax']-proj['zmin'])*.96+.02)*2048) for v in tri]
 draw.polygon(xy,fill=255)
mask=mask.resize((1024,1024),Image.Resampling.LANCZOS);mask.save(OUT/'body_ornament_texture.png')
for suffix in ['albedo','specteam','normalsTS']:
 old=Image.open(OUT/f'original/{suffix}.png').convert('RGBA');sample=old.getpixel((256,1536));a=Image.new('RGBA',(2048,1024),sample)
 a.paste(Image.merge('RGBA',tuple(c.resize((1024,512),Image.Resampling.LANCZOS) for c in old.crop((0,0,4096,1024)).split())),(1024,0))
 a.paste(Image.merge('RGBA',tuple(c.resize((1024,512),Image.Resampling.LANCZOS) for c in old.crop((0,1024,4096,2048)).split())),(1024,512))
 if suffix=='specteam':
  tile=np.array(a.crop((0,0,1024,1024)));t=np.array(mask)/255
  # Preserve metallic response; the baked ornament takes the old team-metal values.
  team=np.array(old.getpixel((2304,1536)))
  for c in range(3):tile[:,:,c]=np.rint(tile[:,:,c]*(1-t)+team[c]*t)
  tile[:,:,3]=np.array(mask);a.paste(Image.fromarray(tile),(0,0))
 for lod,size in [(0,(2048,1024)),(1,(512,256))]:
  im=Image.merge('RGBA',tuple(c.resize(size,Image.Resampling.LANCZOS) for c in a.split()))
  path=RUN/f'GGA0401_optimized_lod{lod}_{suffix}.dds';dds(im,path);Image.open(path).save(OUT/f'decoded_lod{lod}_{suffix}.png')
print('Projection atlas DDS complete')
