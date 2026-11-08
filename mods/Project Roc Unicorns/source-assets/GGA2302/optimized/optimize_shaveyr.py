import bpy, struct, math, json, sys
from pathlib import Path
from mathutils import Vector

REPO=Path('F:/FAF-Development/work/faf-upload')
OUT=Path(__import__('os').environ.get('SHAVEYR_OPT_WORK',str(Path(__file__).resolve().parent/'work')))
ORIG=OUT/'original'; RUNTIME=OUT/'runtime';RUNTIME.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
raw=(ORIG/'GGA2302_lod0.scm').read_bytes();h=struct.unpack_from('<4s11I',raw)
rows=[struct.unpack_from('<16f4B',raw,h[4]+i*68) for i in range(h[6])]
faces=list(zip(*[iter(struct.unpack_from('<%dH'%h[8],raw,h[7]))]*3))
keep=list(range(h[11]));remap={old:new for new,old in enumerate(keep)}
bones=[]
for old in keep:
 q=list(struct.unpack_from('<16f3f4f4i',raw,h[2]+108*old));off=q[23]
 bones.append(dict(name=raw[off:raw.index(b'\0',off)].decode(),data=q,parent=remap[q[24]] if q[24]>=0 else -1))

def mesh_object(name,ff):
 used=sorted(set(v for f in ff for v in f));lookup={v:i for i,v in enumerate(used)}
 me=bpy.data.meshes.new(name);me.from_pydata([(rows[i][0]/5,-rows[i][2]/5,rows[i][1]/5) for i in used],[],[[lookup[v] for v in f] for f in ff]);me.update()
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  p.use_smooth=True
  for li,vi in zip(p.loop_indices,p.vertices):
   r=rows[used[vi]];uv.data[li].uv=(r[12],1-r[13])
 me.normals_split_custom_set_from_vertices([(rows[i][3],-rows[i][5],rows[i][4]) for i in used])
 ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);return ob

def exported(objects):
 rr=[];ii=[];look={}
 for ob in objects:
  me=ob.data;me.calc_loop_triangles();me.calc_tangents(uvmap=me.uv_layers.active.name)
  for tri in me.loop_triangles:
   for li in tri.loops:
    loop=me.loops[li];p=me.vertices[loop.vertex_index].co;n=me.corner_normals[li].vector.copy();t=loop.tangent.copy();u=me.uv_layers.active.data[li].uv
    if n.length<.5:
     pp=[me.vertices[j].co for j in tri.vertices];n=(pp[1]-pp[0]).cross(pp[2]-pp[0])
    n.normalize();t=t-n*t.dot(n)
    if t.length<1e-8:t=n.cross(Vector((0,0,1)))
    if t.length<1e-8:t=n.cross(Vector((1,0,0)))
    t.normalize();bt=n.cross(t)*loop.bitangent_sign
    row=(p.x*5,p.z*5,-p.y*5,n.x,n.z,-n.y,t.x,t.z,-t.y,bt.x,bt.z,-bt.y,u.x,1-u.y,u.x,1-u.y,ob['bone'])
    key=tuple(round(float(a),5) for a in row)
    if key not in look:look[key]=len(rr);rr.append(row)
    ii.append(look[key])
 return rr,ii

def write_scm(path,rr,ii):
 def section(f,tag):
  pad=32-f.tell()%32
  if pad<4:pad+=32
  f.write(b'\xc5'*(pad-4)+tag);return f.tell()
 with path.open('wb') as f:
  f.write(bytes(48));section(f,b'NAME');offs=[]
  for bone in bones:offs.append(f.tell());f.write(bone['name'].encode()+b'\0')
  bo=section(f,b'SKEL')
  for j,bone in enumerate(bones):
   q=bone['data'].copy();q[23]=offs[j];q[24]=bone['parent'];f.write(struct.pack('<16f3f4f4i',*q))
  vo=section(f,b'VTXL')
  for r in rr:f.write(struct.pack('<16f4B',*r,0,0,0))
  io=section(f,b'TRIS');f.write(struct.pack('<%dH'%len(ii),*ii))
  f.seek(0);f.write(struct.pack('<4s11I',b'MODL',5,bo,len(bones),vo,0,len(rr),io,len(ii),0,0,len(bones)))

base=[]
for bone in sorted(set(r[16] for r in rows)):
 ob=mesh_object('Part'+str(bone),[f for f in faces if rows[f[0]][16]==bone]);ob['bone']=bone
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.00001);bpy.ops.object.mode_set(mode='OBJECT')
 ob.hide_render=True;ob.hide_set(True);base.append(ob)
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
coords=[Vector((r[0]/5,-r[2]/5,r[1]/5)) for r in rows]
sourcefaces={ob['bone']:[f for f in faces if rows[f[0]][16]==ob['bone']] for ob in base}
trees={k:BVHTree.FromPolygons(coords,v,all_triangles=True) for k,v in sourcefaces.items()}
far=[]
for source in base:
 ob=source.copy();ob.data=source.data.copy();scene.collection.objects.link(ob);ob.hide_set(False)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Distant silhouette','REMESH');mod.mode='VOXEL';mod.voxel_size=.025;mod.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=mod.name);ob.hide_set(True);far.append(ob)
results=[]
for lod,target in [(0,6500),(1,4500)]:
 ratio=target/len(faces)
 for attempt in range(6):
  obs=[]
  for source in base:
   ob=source.copy();ob.data=source.data.copy();scene.collection.objects.link(ob);ob.hide_set(False)
   bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
   dec=ob.modifiers.new('Simplify','DECIMATE');dec.ratio=ratio;dec.use_symmetry=True;dec.symmetry_axis='X'
   bpy.ops.object.modifier_apply(modifier=dec.name)
   if False:
    uv=ob.data.uv_layers.new(name='UVMap')
    for poly in ob.data.polygons:
     poly.use_smooth=True
     for li,vi in zip(poly.loop_indices,poly.vertices):
      q,n,idx,d=trees[ob['bone']].find_nearest(ob.data.vertices[vi].co);ff=sourcefaces[ob['bone']][idx]
      uv.data[li].uv=barycentric_transform(q,*[coords[j] for j in ff],*[Vector((rows[j][12],1-rows[j][13],0)) for j in ff]).xy
   if False:ob.data.normals_split_custom_set_from_vertices([(0,0,0)]*len(ob.data.vertices))
   obs.append(ob)
  rr,ii=exported(obs);print('LOD',lod,'VERTICES',len(rr),'TRIS',len(ii)//3,flush=True)
  if .93*target<=len(ii)//3<=1.07*target:break
  if attempt==5:raise RuntimeError('Cannot meet budget')
  ratio*=target/(len(ii)//3)
  for ob in obs:bpy.data.objects.remove(ob,do_unlink=True)
 write_scm(RUNTIME/f'GGA2302_lod{lod}.scm',rr,ii)
 results.append(dict(lod=lod,vertices=len(rr),triangles=len(ii)//3,bones=len(bones)))
 for ob in obs:ob.hide_set(True);ob.hide_render=True
(OUT/'geometry.json').write_text(json.dumps(results,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ShaVeyr_optimized.blend'))
