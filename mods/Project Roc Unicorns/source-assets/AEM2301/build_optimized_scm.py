"""Replace SCM geometry with the optimized OBJ, preserving the original skeleton."""
from pathlib import Path
import struct
import numpy as np

root = Path(__file__).resolve().parent
original = root / 'archive' / 'AEM2301_original_lod0.scm'
obj = root / 'source-model' / 'Aeon_Missile_Turret_optimized.obj'
output = root / 'AEM2301_optimized_lod0.scm'
data = original.read_bytes()
h = list(struct.unpack_from('<4s11I', data))
old = np.array([struct.unpack_from('<16f4B', data, h[4]+i*68)[:17] for i in range(h[6])])
oldfaces = np.frombuffer(data, dtype='<u2', count=h[8], offset=h[7]).reshape(-1, 3)
assert all(len(set(old[face,16])) == 1 for face in oldfaces)
positions, uvs, normals, faces = [], [], [], []
for line in obj.read_text(encoding='utf8').splitlines():
    s = line.split()
    if not s: continue
    if s[0] == 'v': positions.append([float(x) for x in s[1:4]])
    elif s[0] == 'vt': uvs.append([float(x) for x in s[1:3]])
    elif s[0] == 'vn': normals.append([float(x) for x in s[1:4]])
    elif s[0] == 'f': faces.append([[int(x)-1 for x in v.split('/')] for v in s[1:]])
positions, uvs, normals, faces = map(np.asarray, (positions, uvs, normals, faces))
assert faces.shape == (3000,3,3)
# Find the closest original vertex, then require a single bone per face.
nearest = []
for i in range(0, len(positions), 100):
    dist = ((positions[i:i+100,None,:]-old[None,:,:3])**2).sum(axis=2)
    nearest.extend(dist.argmin(axis=1))
bone = old[np.array(nearest),16].astype(int)
assert all(len(set(bone[face[:,0]])) == 1 for face in faces), 'Decimation crossed a bone boundary'

# Detect the OBJ/SCM V convention using original UVs at coincident geometry.
samples = faces.reshape(-1,3)[::20]
errors = [0.,0.]
for pi,ti,ni in samples:
    candidates = old[old[:,16] == bone[pi]]
    pd = ((candidates[:,:3]-positions[pi])**2).sum(axis=1)
    close = candidates[pd < pd.min()+1e-8]
    for flip in (0,1):
        uv = uvs[ti].copy()
        if flip: uv[1] = 1-uv[1]
        errors[flip] += ((close[:,12:14]-uv)**2).sum(axis=1).min()
flip = int(errors[1] < errors[0])
verts=[]; indices=[]; cache={}
for face in faces:
    b = bone[face[0,0]]
    candidates = old[old[:,16] == b]
    for pi,ti,ni in face:
        key=(int(pi),int(ti),int(ni),int(b))
        if key not in cache:
            uv=uvs[ti].copy()
            if flip: uv[1]=1-uv[1]
            pd=((candidates[:,:3]-positions[pi])**2).sum(axis=1)
            near=candidates[pd < pd.min()+1e-7]
            src=near[((near[:,12:14]-uv)**2).sum(axis=1).argmin()]
            # Preserve the original normal/tangent basis and secondary UVs;
            # the closest match is chosen in both position and texture space.
            rec=list(src[:16]); rec[:3]=positions[pi]; rec[12:14]=uv; rec[14:16]=uv
            cache[key]=len(verts); verts.append((*rec,int(b)))
        indices.append(cache[key])
assert len(verts)<65536
def pad(n):
    x=32-n%32
    return x+32 if x<4 else x
index_offset=h[4]+68*len(verts)
index_offset+=pad(index_offset)
h[6],h[7],h[8]=len(verts),index_offset,len(indices)
result=bytearray(data[:h[4]])
struct.pack_into('<4s11I',result,0,*h)
for vertex in verts: result.extend(struct.pack('<16f4B',*vertex[:16],vertex[16],0,0,0))
result.extend(b'\xc5'*(index_offset-len(result)-4)+b'TRIS')
result.extend(struct.pack('<%dH'%len(indices),*indices))
output.write_bytes(result)
print('vertices',len(verts),'triangles',len(indices)//3,'UV flip',flip,'UV errors',errors,'bones',np.unique(bone[faces[:,:,0]],return_counts=True))
