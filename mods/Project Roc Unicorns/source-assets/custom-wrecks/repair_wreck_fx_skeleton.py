"""Add FX slots to existing accepted wrecks; preserve vertex/index bytes exactly."""
from pathlib import Path
from types import SimpleNamespace
import sys,struct,json
import numpy as np
SRC=Path(__file__).resolve().parent;MOD=SRC.parents[1]
sys.path.insert(0,str(MOD/'source-assets/GGA1401'))
from supcom_binary import write_scm
from wreck_skeleton import fx_skeleton
OUT=Path('F:/FAF-Development/outputs/VaelItha_Wreck_Death_Fix_v8');report=[]
for uid in ['GGA2404']:
    live=struct.unpack_from('<4s11I',(MOD/f'units/{uid}/{uid}_lod0.scm').read_bytes())[3]
    for lod in [0,1]:
        p=MOD/f'props/{uid}_wreck/{uid}_wreck_lod{lod}.scm';old=p.read_bytes();h=struct.unpack_from('<4s11I',old)
        rows=[struct.unpack_from('<16f4B',old,h[4]+i*68) for i in range(h[6])]
        indices=struct.unpack_from('<'+'H'*h[8],old,h[7]);assert all(v[16:]==(0,0,0,0) for v in rows)
        skeleton=fx_skeleton(np.array([v[:3] for v in rows]),live)
        mesh=SimpleNamespace(vertices=rows,indices=indices);write_scm(mesh,p,*skeleton)
        new=p.read_bytes();nh=struct.unpack_from('<4s11I',new)
        assert old[h[4]:h[4]+h[6]*68]==new[nh[4]:nh[4]+nh[6]*68]
        assert old[h[7]:h[7]+h[8]*2]==new[nh[7]:nh[7]+nh[8]*2]
        assert nh[3]==live
        report.append({'unit':uid,'lod':lod,'old_bones':h[3],'new_bones':nh[3],'vertices_identical':True,'indices_identical':True})
(OUT/'mesh_repair_validation.json').write_text(json.dumps(report,indent=2));print('STATIC_WRECK_FX_SKELETON_REPAIRED',json.dumps(report))
