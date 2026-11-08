"""Generate static, collapsed native wrecks from the mod's own live SCM/DDS."""
from pathlib import Path
from types import SimpleNamespace
from io import BytesIO
import sys,struct,json,math
import numpy as np
from PIL import Image
SRC=Path(__file__).resolve().parent;MOD=SRC.parents[1]
sys.path.insert(0,str(MOD/'source-assets/GGA1401'))
from supcom_binary import write_scm
from wreck_skeleton import fx_skeleton
REPORT={}

def normalized(a):return a/np.maximum(1e-12,np.linalg.norm(a,axis=-1,keepdims=True))
def rotation(x,z):
 cx,sx,cz,sz=math.cos(x),math.sin(x),math.cos(z),math.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1.]])@np.array([[1.,0,0],[0,cx,-sx],[0,sx,cx]])
def load(path):
 d=path.read_bytes();h=struct.unpack_from('<4s11I',d)
 v=np.array([struct.unpack_from('<16f4B',d,h[4]+i*68)[:17] for i in range(h[6])])
 f=np.frombuffer(d,dtype='<u2',count=h[8],offset=h[7]).reshape(-1,3).copy()
 return v,f

def transform(v,unit):
 out=v.copy();p=v[:,:3];n=v[:,3:6];t=v[:,6:9];bt=v[:,9:12]
 for bone in np.unique(v[:,16]).astype(int):
  indices=np.where(v[:,16]==bone)[0];pts=p[indices];norm=n[indices];tang=t[indices]
  if (unit=='GGA0401' and bone in [21,22]) or (unit=='GGA2404' and bone in [5,6]):
   side=-1 if bone in [21,5] else 1
   if unit=='GGA0401':center=np.array([side*4.625,18.2,0]);dest=np.array([side*7,5.5,side*1.0]);mat=rotation(side*.16,-side*.7)
   else:center=np.array([side*13.6,58,3.2]);dest=np.array([side*18,21,3.2+side*3]);mat=rotation(side*.16,-side*.55)
   out[indices,:3]=(pts-center)@mat.T+dest
   out[indices,3:6]=norm@mat.T;out[indices,6:9]=tang@mat.T;out[indices,9:12]=bt[indices]@mat.T
  else:
   scale=.70 if unit=='GGA0401' else .68
   phase=pts[:,0]*.19+pts[:,2]*.14
   out[indices,1]=pts[:,1]*scale+.32*np.sin(phase)
   # Inverse-transpose normal of y'=scale*y+.32*sin(.19*x+.14*z).
   invnorm=norm.copy();invnorm[:,0]-=.32*.19*np.cos(phase)*norm[:,1]/scale
   invnorm[:,2]-=.32*.14*np.cos(phase)*norm[:,1]/scale;invnorm[:,1]/=scale
   out[indices,3:6]=normalized(invnorm)
   tt=tang.copy();tt[:,1]=scale*tang[:,1]+.32*np.cos(phase)*(.19*tang[:,0]+.14*tang[:,2])
   nn=out[indices,3:6];tt-=nn*np.sum(nn*tt,axis=1,keepdims=True);out[indices,6:9]=normalized(tt)
   cross=np.cross(nn,out[indices,6:9]);sign=np.where(np.sum(np.cross(norm,tang)*bt[indices],axis=1)>=0,1,-1)
   out[indices,9:12]=cross*sign[:,None]
 nn=normalized(out[:,3:6]);tt=out[:,6:9];tt=normalized(tt-nn*np.sum(nn*tt,axis=1,keepdims=True))
 sign=np.where(np.sum(np.cross(nn,tt)*out[:,9:12],axis=1)>=0,1,-1)
 out[:,3:6]=nn;out[:,6:9]=tt;out[:,9:12]=np.cross(nn,tt)*sign[:,None]
 out[:,1]-=out[:,1].min()-.25
 out[:,16]=0
 return out

def dds(im,path):
 levels=[];current=im
 while True:
  buf=BytesIO();current.save(buf,format='DDS',pixel_format='DXT5');d=buf.getvalue();levels.append(d[128:])
  if current.size==(1,1):break
  size=(max(1,current.width//2),max(1,current.height//2));current=Image.merge('RGBA',tuple(c.resize(size,Image.Resampling.LANCZOS) for c in current.split()))
 hdr=bytearray(d[:128]);struct.pack_into('<I',hdr,8,0xa1007);struct.pack_into('<4I',hdr,12,im.height,im.width,((im.width+3)//4)*((im.height+3)//4)*16,0);struct.pack_into('<I',hdr,28,len(levels));struct.pack_into('<I',hdr,108,0x401008);path.write_bytes(hdr+b''.join(levels))

for unit,source_lods,scale in [('GGA2404',[0,1],.05)]:
 folder=MOD/f'props/{unit}_wreck';folder.mkdir(parents=True,exist_ok=True)
 summary=[]
 for lod,source_lod in enumerate(source_lods):
  v,f=load(MOD/f'units/{unit}/{unit}_lod{source_lod}.scm')
  # Remove all hovering energy-field geometry. The charge sphere is a separate
  # Entity and was never part of the live SCM.
  if unit=='GGA2404':f=f[~np.isin(v[f[:,0],16],[7,8,9,10,11])]
  cent=v[f,:3].mean(axis=1)
  # Small ragged openings, while retaining recognizable petal/ring silhouettes.
  if unit=='GGA0401':hole=((cent[:,0]-11)**2+(cent[:,2]-9)**2<5)&(cent[:,1]>5)
  else:hole=((cent[:,0]+21)**2+(cent[:,2]+8)**2<9)&(cent[:,1]>9)
  f=f[~hole];used,inv=np.unique(f,return_inverse=True);f=inv.reshape(-1,3);v=v[used];out=transform(v,unit)
  mesh=SimpleNamespace(vertices=[tuple(row[:16])+(0,) for row in out],indices=f.flatten().tolist())
  file=folder/f'{unit}_wreck_lod{lod}.scm'
  live_bones=struct.unpack_from('<4s11I',(MOD/f'units/{unit}/{unit}_lod0.scm').read_bytes())[3]
  write_scm(mesh,file,*fx_skeleton(out[:,:3],live_bones))
  assert np.isfinite(out).all() and len(out)<65536
  summary.append({'vertices':len(out),'triangles':len(f),'bounds_game':[(out[:,:3].min(0)*scale).tolist(),(out[:,:3].max(0)*scale).tolist()]})
 if unit=='GGA0401':albedo='GGA0401_approved_albedo';spec='GGA0401_approved_specteam';normal='GGA0401_approved_normalsTS'
 else:albedo='GGA2404_albedo';spec='GGA2404_specteam';normal='GGA2404_normalsTS'
 a=np.asarray(Image.open(MOD/f'units/{unit}/{albedo}.dds').convert('RGB').resize((1024,512)),dtype=float)
 sm=np.asarray(Image.open(MOD/f'units/{unit}/{spec}.dds').convert('RGBA').resize((1024,512)),dtype=float)
 rng=np.random.default_rng(401 if unit=='GGA0401' else 2404)
 coarse=Image.fromarray(rng.integers(30,255,(32,64),dtype=np.uint8)).resize((1024,512),Image.Resampling.BICUBIC)
 soot=np.asarray(coarse)/255
 gray=(18+a.mean(2)*.20+sm[:,:,3]/255*4)*(.40+.60*soot)
 rgba=np.zeros((512,1024,4),np.uint8);rgba[:,:,:3]=np.clip(gray[:,:,None]*np.array([1,.96,.89]),0,255);rgba[:,:,3]=255
 image=Image.fromarray(rgba);dds(image,folder/f'{unit}_wreck_albedo.dds');image.save(SRC/f'{unit}_wreck_albedo.png')
 prop=f'''PropBlueprint {{
    Categories = {{ 'RECLAIMABLE' }},
    Display = {{ MeshBlueprint = '/mods/Project Roc Unicorns/props/{unit}_wreck/{unit}_wreck_mesh' }},
    Economy = {{ ReclaimMassMax = 1, ReclaimTime = 5 }},
    Interface = {{ HelpText = '{"Dush Nai" if unit=="GGA0401" else "Vael-Itha"} wreckage' }},
    Physics = {{ BlockPath = false }},
    ScriptClass = 'Wreckage', ScriptModule = '/lua/wreckage.lua',
    SizeX = 4, SizeY = 1.5, SizeZ = {6 if unit=='GGA0401' else 4},
}}
'''
 (folder/f'{unit}_wreck_prop.bp').write_text(prop,encoding='utf-8')
 parts=[]
 for lod,cutoff in enumerate([160,700]):
  parts.append(f'''        {{
            MeshName = '/mods/Project Roc Unicorns/props/{unit}_wreck/{unit}_wreck_lod{lod}.scm',
            AlbedoName = '/mods/Project Roc Unicorns/props/{unit}_wreck/{unit}_wreck_albedo.dds',
            SpecularName = '/env/common/props/wreckage_noise.dds',
            NormalsName = '/mods/Project Roc Unicorns/units/{unit}/{normal}.dds',
            ShaderName = 'Wreckage', LODCutoff = {cutoff},
        }},''')
 (folder/f'{unit}_wreck_mesh.bp').write_text('MeshBlueprint {\n    LODs = {\n'+'\n'.join(parts)+'\n    },\n}\n',encoding='utf-8')
 p=MOD/f'units/{unit}/{unit}_unit.bp';text=p.read_text();old="Blueprint = '/props/DefaultWreckage/DefaultWreckage_prop.bp'";new=f"Blueprint = '/mods/Project Roc Unicorns/props/{unit}_wreck/{unit}_wreck_prop.bp', UseCustomMesh = true"
 assert old in text or new in text;text=text.replace(old,new);p.write_text(text,encoding='utf-8');REPORT[unit]=summary
(SRC/'wreck_export_report.json').write_text(json.dumps(REPORT,indent=2));print('CUSTOM_WRECKS_READY',json.dumps(REPORT))
