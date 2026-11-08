from pathlib import Path
import sys,json,shutil,struct,math
from types import SimpleNamespace
from PIL import Image,ImageDraw
p=Path(__file__).parent;sys.path.insert(0,str(p.parent))
from supcom_binary import write_scm,save_dds_dxt5
mod=p.parents[2];unit=mod/'units/GGA2301';backup=p/'backup-before-comet'
if not backup.exists():shutil.copytree(unit,backup)
stage=p/'runtime';stage.mkdir(exist_ok=True)
u=stage/'units/GGA2301';u.mkdir(parents=True,exist_ok=True)
for lod in [0,1]:
 d=json.loads((p/f'lod{lod}.json').read_text());write_scm(SimpleNamespace(vertices=d['vertices'],indices=d['indices']),u/f'GGA2301_lod{lod}.scm',d['names'],d['parents'],d['pivots'])
# Small padded palette atlas: markings have real geometry and independent team-mask islands.
a=Image.new('RGBA',(256,64),(44,49,56,0));sp=Image.new('RGBA',(256,64),(170,165,0,0));n=Image.new('RGBA',(256,64),(128,128,255,128))
colors=[(44,49,56,0),(90,96,105,0),(19,23,28,0),(110,110,110,255),(235,240,255,0)]
specs=[(180,165,0,0),(220,195,0,0),(110,120,0,0),(125,140,180,0),(130,160,255,0)]
for i,(c,ss) in enumerate(zip(colors,specs)):
 ImageDraw.Draw(a).rectangle((i*32,0,(i+1)*32-1,63),fill=c);ImageDraw.Draw(sp).rectangle((i*32,0,(i+1)*32-1,63),fill=ss)
for name,im in [('albedo',a),('specteam',sp),('normalsTS',n)]:
 im.save(p/f'{name}_source.png');save_dds_dxt5(im,u/f'GGA2301_{name}.dds',independent_channels=True)
shutil.copy2(unit/'GGA2301_mesh.bp',u/'GGA2301_mesh.bp')
# Dark collapsed wreck, independent mesh with a root bone only.
d=json.loads((p/'lod1.json').read_text());verts=[]
for v in d['vertices']:
 w=list(v);w[1]=max(.05,w[1]*.37);w[0]+= .12*math.sin(w[2]*2)*w[1];w[16]=0;w[12]=w[14]=2.5/8;verts.append(w)
write_scm(SimpleNamespace(vertices=verts,indices=d['indices']),u/'GGA2301_wreck.scm',['GGA2301'],[-1],[(0,0,0)])
(u/'GGA2301_wreck_mesh.bp').write_text("MeshBlueprint { LODs = { { MeshName = '/mods/Project Roc Unicorns/units/GGA2301/GGA2301_wreck.scm', AlbedoName = '/mods/Project Roc Unicorns/units/GGA2301/GGA2301_albedo.dds', SpecularName = '/mods/Project Roc Unicorns/units/GGA2301/GGA2301_specteam.dds', NormalsName = '/mods/Project Roc Unicorns/units/GGA2301/GGA2301_normalsTS.dds', LookupName = '/textures/environment/Falloff_seraphim_lookup.dds', ShaderName = 'Seraphim', LODCutoff = 215, } }, }\n")
# Own luminous projectile geometry, not a copied game model.
pr=stage/'projectiles/GGP2301';pr.mkdir(parents=True,exist_ok=True);vs=[];ix=[]
for j in range(13):
 lat=math.pi*j/12
 for k in range(24):
  lng=2*math.pi*k/24;normal=(math.sin(lat)*math.cos(lng),math.cos(lat),math.sin(lat)*math.sin(lng));pos=tuple(.055*x for x in normal)
  tangent=(-math.sin(lng),0,math.cos(lng));bt=(normal[1]*tangent[2]-normal[2]*tangent[1],normal[2]*tangent[0]-normal[0]*tangent[2],normal[0]*tangent[1]-normal[1]*tangent[0])
  vs.append(pos+normal+tangent+bt+(.5,.5,.5,.5)+(0,))
for j in range(12):
 for k in range(24):
  a0=j*24+k;b=j*24+(k+1)%24;c=b+24;d0=a0+24;ix.extend([a0,b,c,a0,c,d0])
# Reverse if sphere winding faces inward.
import numpy as np
v0=np.array([vs[i][:3] for i in ix[72:75]])
if np.dot(np.cross(v0[1]-v0[0],v0[2]-v0[0]),v0.mean(0))<0:
 ix=[k for i in range(0,len(ix),3) for k in (ix[i],ix[i+2],ix[i+1])]
write_scm(SimpleNamespace(vertices=vs,indices=ix),pr/'GGP2301_lod0.scm',['GGP2301'],[-1],[(0,0,0)])
for name,color in [('albedo',(225,210,255,0)),('specteam',(80,120,255,0)),('normalsTS',(128,128,255,128))]:save_dds_dxt5(Image.new('RGBA',(32,32),color),pr/f'GGP2301_{name}.dds',independent_channels=True)
print('PACKED',stage)

