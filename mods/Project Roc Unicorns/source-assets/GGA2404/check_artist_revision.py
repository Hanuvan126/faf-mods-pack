"""Validate ring-face visibility in both exported LODs and preserve prior fixes."""
from pathlib import Path
import numpy as np,json,struct,hashlib
SRC=Path(__file__).resolve().parent;MOD=SRC.parents[1];OUT=Path('F:/FAF-Development/outputs/VaelItha_Artist_Patterns_v9')
probes=json.loads(Path('F:/FAF-Development/outputs/VaelItha_Selection_Ring_Fix_v7/ring_visibility_probes.json').read_text()) if Path('F:/FAF-Development/outputs/VaelItha_Selection_Ring_Fix_v7/ring_visibility_probes.json').exists() else None
if probes is None:
 data=json.loads(Path('F:/FAF-Development/outputs/VaelItha_Selection_Ring_Fix_v7/pattern_geometry.json').read_text())
 probes=[{'bone':o['bone'],'points':o['vertices'][::8]} for o in data if o['name'].startswith(('Ring orbital seal','Ring paired orbit'))]
counts=[]
for lod in [0,1]:
 raw=(MOD/f'units/GGA2404/GGA2404_lod{lod}.scm').read_bytes();h=struct.unpack_from('<4s11I',raw);v=np.array([struct.unpack_from('<16f4B',raw,h[4]+i*68)[:17] for i in range(h[6])]);f=np.frombuffer(raw,dtype='<u2',count=h[8],offset=h[7]).reshape(-1,3)
 checked=0
 for bone,sign,name in [(5,-1,'GondolaL'),(6,1,'GondolaR')]:
  tri=v[f[v[f[:,0],16]==bone],:3]*.05;e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];d=np.array([-sign,0,0]);pv=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.sum(e1*pv,axis=1);mask=abs(det)>1e-10;inv=np.zeros_like(det);inv[mask]=1/det[mask]
  for group in [p for p in probes if p['bone']==name]:
   for p in group['points']:
    target=np.array([p[0],p[2],-p[1]]);o=np.array([sign*3,target[1],target[2]]);limit=abs(o[0]-target[0])-.003
    s=o-tri[:,0];u=np.sum(s*pv,axis=1)*inv;q=np.cross(s,e1);w=q@d*inv;t=np.sum(e2*q,axis=1)*inv
    valid=mask&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1+1e-7)&(t>0)&(t<limit)
    assert not valid.any(),('Ring face occluded',lod,name,p,tri[valid].tolist()[:1]);checked+=1
 counts.append({'lod':lod,'visible_ring_probes':checked})
before=json.loads((OUT/'before_runtime_hashes.json').read_text());changed=[p for p,h in before.items() if hashlib.sha256((MOD/p).read_bytes()).hexdigest()!=h]
assert set(changed)=={'units/GGA2404/GGA2404_lod0.scm','units/GGA2404/GGA2404_lod1.scm'},changed
report={'native_ring_visibility':counts,'changed_runtime_files':changed,'all_other_runtime_files_unchanged':True,'post_change_match_run':False}
(OUT/'artist_validation.json').write_text(json.dumps(report,indent=2));print('ARTIST_REVISION_CHECKS_PASS',json.dumps(report))
