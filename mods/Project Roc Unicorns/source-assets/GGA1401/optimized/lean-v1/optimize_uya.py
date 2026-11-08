from pathlib import Path
import sys,struct,zipfile,shutil,json
import numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())
SRC=ROOT/'mods/Project Roc Unicorns/source-assets/GGA1401'
UNIT=ROOT/'mods/Project Roc Unicorns/units/GGA1401'
OUT=ROOT/'outputs/UyaIava_Optimization'
OUT.mkdir(exist_ok=True);(OUT/'original').mkdir(exist_ok=True);(OUT/'runtime').mkdir(exist_ok=True)
if not (OUT/'before.zip').exists():
 with zipfile.ZipFile(OUT/'before.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in UNIT.iterdir():
   if p.is_file():z.write(p,p.name);shutil.copy2(p,OUT/'original'/p.name)
sys.path.insert(0,str(SRC))
from supcom_binary import write_scm
original=(OUT/'original/GGA1401_lod0.scm').read_bytes();oh=struct.unpack_from('<4s11I',original)
def retain_bones(path):
 data=bytearray(path.read_bytes());h=struct.unpack_from('<4s11I',data);assert h[11]==oh[11]
 for i in range(h[11]):
  b=list(struct.unpack_from('<16f3f4f4i',original,oh[2]+108*i));new=struct.unpack_from('<16f3f4f4i',data,h[2]+108*i)
  assert original[b[23]:original.index(b'\0',b[23])]==data[new[23]:data.index(b'\0',new[23])]
  b[23]=new[23];struct.pack_into('<16f3f4f4i',data,h[2]+108*i,*b)
 path.write_bytes(data)
stats={}
for lod in [0,1]:
 code=(SRC/'generate_caldera.py').read_text()
 code=code[:code.index('def main(')]
 code=code.replace('3 if m.detail >= 40 else 2','2' if lod==0 else '1')
 code=code.replace('3 if m.detail>=40 else 2','2' if lod==0 else '1')
 code=code.replace('3 if m.detail>=32 else 2','2' if lod==0 else '1')
 code=code.replace('12 if m.detail>=32 else 8','8' if lod==0 else '4')
 code=code.replace('20 if m.detail>=32 else 12','12' if lod==0 else '8')
 code=code.replace('math.pi,8,endpoint=False)','math.pi,4,endpoint=False)' if lod==0 else 'math.pi,3,endpoint=False)')
 env={'__file__':str(SRC/'generate_caldera.py'),'__name__':'optimized_generator'};exec(compile(code,str(SRC/'generate_caldera.py'),'exec'),env)
 if lod==1:env['tube']=lambda *args,**kwargs:None
 mesh=env['build_mesh'](20 if lod==0 else 10)
 # Weld tangent splits only: UV seams, normal splits and bone ownership stay separate.
 groups={};verts=[];indices=[];sums=[];bits=[]
 for old in mesh.indices:
  v=mesh.vertices[old];key=tuple(round(float(x),6) for x in v[:6]+v[12:16])+(int(v[16]),)
  if key not in groups:
   groups[key]=len(verts);verts.append(v);sums.append(np.zeros(3));bits.append(np.zeros(3))
  j=groups[key];indices.append(j);sums[j]+=v[6:9];bits[j]+=v[9:12]
 for j,v in enumerate(verts):
  n=np.array(v[3:6]);t=sums[j]-n*np.dot(n,sums[j]);t/=max(np.linalg.norm(t),1e-12)
  b=np.cross(n,t);b*=1 if np.dot(b,bits[j])>=0 else -1
  verts[j]=v[:6]+tuple(t)+tuple(b)+v[12:]
 mesh.vertices,mesh.indices=verts,indices
 path=OUT/f'runtime/GGA1401_lod{lod}.scm';write_scm(mesh,path,env['NAMES'],env['PARENTS'],env['PIVOTS']);retain_bones(path)
 stats[f'lod{lod}']={'vertices':len(mesh.vertices),'triangles':len(mesh.indices)//3,'bytes':path.stat().st_size}
 print(stats,flush=True)
(OUT/'geometry.json').write_text(json.dumps(stats,indent=2))
