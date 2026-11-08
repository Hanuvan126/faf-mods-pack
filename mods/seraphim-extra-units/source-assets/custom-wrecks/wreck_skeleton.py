"""Static wreck root plus valid native death-smoke attachment slots."""
import numpy as np
def fx_skeleton(positions,live_bone_count):
    assert live_bone_count>=1
    positions=np.asarray(positions)
    names=['WreckRoot']+[f'WreckFX_{i:02d}' for i in range(1,live_bone_count)]
    parents=[-1]+[0]*(live_bone_count-1)
    selected=np.linspace(0,len(positions)-1,max(0,live_bone_count-1),dtype=int)
    pivots=[(0,0,0)]+[tuple(float(v) for v in positions[i]) for i in selected]
    return names,parents,pivots
