"""Ray checks against exported native SCM, not just the authoring scene."""
from pathlib import Path
import struct,json
import numpy as np
SRC=Path(__file__).resolve().parent;MOD=SRC.parents[1];OUT=Path('F:/FAF-Development/outputs/VaelItha_Selection_Ring_Fix_v7')
def read(p):
 d=p.read_bytes();h=struct.unpack_from('<4s11I',d);v=np.array([struct.unpack_from('<16f4B',d,h[4]+i*68)[:17] for i in range(h[6])]);f=np.frombuffer(d,dtype='<u2',offset=h[7],count=h[8]).reshape(-1,3);return d,h,v,f
def hits(v,f,o,d):
 tri=v[f,:3]*.05;e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];p=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.sum(e1*p,axis=1);mask=abs(det)>1e-10;inv=np.zeros_like(det);inv[mask]=1/det[mask];s=o-tri[:,0];u=np.sum(s*p,axis=1)*inv;q=np.cross(s,e1);w=q@d*inv;t=np.sum(e2*q,axis=1)*inv
 return np.sort(t[mask&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1+1e-7)&(t>.0001)&(t<.386)])
checks=[]
for lod in [0,1]:
 p=MOD/f'units/GGA2404/GGA2404_lod{lod}.scm';raw,h,v,f=read(p);old,oh,ov,of=read(OUT/f'baseline_lod{lod}.scm')
 assert raw[h[2]:h[4]]==old[oh[2]:oh[4]],'Skeleton or bind poses changed'
 assert len(v)<65536 and np.isfinite(v).all() and f.max()<len(v)
 for bone,cx in [(5,-.68),(6,.68)]:
  fs=f[v[f[:,0],16]==bone]
  for axial in [-.025,0,.025]:
   for k in range(64):
    a=2*np.pi*(k+.37)/64;o=np.array([cx+axial,2.9,.16]);d=np.array([0,np.cos(a),np.sin(a)]);ts=hits(v,fs,o,d)
    assert len(ts)==1,(lod,bone,axial,k,ts.tolist())
    assert .383<ts[0]<.386
  checks.append({'lod':lod,'bone':bone,'single_surface_rays':192})
bp=(MOD/'units/GGA2404/GGA2404_unit.bp').read_text();assert 'SelectionThickness = 0.25' in bp
report={'selection_thickness':.25,'single_bore_tests':checks,'skeleton_preserved_both_LODs':True,'new_match_run':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print('NATIVE_BORE_CHECKS_PASS',json.dumps(report))
