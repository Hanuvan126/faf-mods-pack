import bpy, struct, math, json, sys
from pathlib import Path
from mathutils import Vector

REPO=Path('F:/FAF-Development/work/faf-upload')
OUT=Path(__import__('os').environ.get('DUSH_OPT_WORK',str(Path(__file__).resolve().parent/'work')))
ORIG=OUT/'original'; RUNTIME=OUT/'runtime';RUNTIME.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
raw=(ORIG/'GGA0401_lod0.scm').read_bytes();h=struct.unpack_from('<4s11I',raw)
rows=[struct.unpack_from('<16f4B',raw,h[4]+i*68) for i in range(h[6])]
faces=list(zip(*[iter(struct.unpack_from('<%dH'%h[8],raw,h[7]))]*3))
keep=[0,1,2,3,21,22]+list(range(23,33));remap={old:new for new,old in enumerate(keep)}
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

high=mesh_object('Original high detail',faces)
mat=bpy.data.materials.new('Bake source');mat.use_nodes=True;high.data.materials.append(mat)
nodes=mat.node_tree.nodes;nodes.clear();o=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');mat.node_tree.links.new(em.outputs[0],o.inputs[0])
tex=nodes.new('ShaderNodeTexImage');tex.interpolation='Linear'
images={k:bpy.data.images.load(str(ORIG/f'{k}.png')) for k in ['albedo','specteam','normalsTS']}
for im in images.values():im.colorspace_settings.name='Non-Color'

base={}
for bone in [0,21,22]:
 ff=[f for f in faces if rows[f[0]][16]==bone and not (bone==0 and rows[f[0]][13]>.5 and int(rows[f[0]][12]*8)==4)]
 ob=mesh_object('Working'+str(bone),ff);ob['bone']=remap[bone]
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.00001);bpy.ops.object.mode_set(mode='OBJECT')
 base[bone]=ob;ob.hide_render=True;ob.hide_set(True)

from mathutils.bvhtree import BVHTree
source_faces={b:[f for f in faces if rows[f[0]][16]==b and not(b==0 and rows[f[0]][13]>.5 and int(rows[f[0]][12]*8)==4)] for b in [0,21,22]}
coords=[Vector((r[0]/5,-r[2]/5,r[1]/5)) for r in rows]
trees={b:BVHTree.FromPolygons(coords,fs,all_triangles=True) for b,fs in source_faces.items()}
body=[r for r in rows if r[16]==0];xmin=min(r[0] for r in body)-.1;xmax=max(r[0] for r in body)+.1;zmin=min(r[2] for r in body)-.1;zmax=max(r[2] for r in body)+.1
(OUT/'projection.json').write_text(json.dumps(dict(xmin=xmin,xmax=xmax,zmin=zmin,zmax=zmax)))

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

def reduce_set(sources,ratio,unwrap):
 result=[]
 for source in sources:
  ob=source.copy();ob.data=source.data.copy();scene.collection.objects.link(ob);ob.hide_set(False);ob.hide_render=False
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  mod=ob.modifiers.new('Controlled simplification','DECIMATE');mod.ratio=min(.95,ratio*5) if source.get('main_gondola',False) else ratio
  if source['bone']==0:mod.use_symmetry=True;mod.symmetry_axis='X'
  bpy.ops.object.modifier_apply(modifier=mod.name)
  for p in ob.data.polygons:p.use_smooth=True
  result.append(ob)
 left=next(o for o in result if o['bone']==4);right=next(o for o in result if o['bone']==5)
 from mathutils import Matrix
 left.data=right.data.copy();left.data.transform(Matrix.Diagonal((-1,1,1,1)));left.data.flip_normals()
 # Preserve source UVs for the main surface; the distant silhouette gets
 # UVs from the closest original surface, then both use a compact projection atlas.
 for ob in result:
  if not ob.data.uv_layers:ob.data.uv_layers.new(name='UVMap')
  uv=ob.data.uv_layers.active
  for poly in ob.data.polygons:
   center=poly.center
   original_bone={0:0,4:21,5:22}[ob['bone']]
   if unwrap:
    nearest,normal,index,dist=trees[original_bone].find_nearest(center)
    srcface=source_faces[original_bone][index]
    sr=rows[srcface[0]];oldcat='gondola' if sr[13]<.5 else int(sr[12]*8)
   else:oldcat=None
   for li,vi in zip(poly.loop_indices,poly.vertices):
    v=ob.data.vertices[vi].co
    if unwrap and oldcat=='gondola':
     q,n,idx,d=trees[original_bone].find_nearest(v)
     ff=source_faces[original_bone][idx]
     from mathutils.geometry import barycentric_transform
     pp=[Vector((rows[j][0]/5,-rows[j][2]/5,rows[j][1]/5)) for j in ff]
     uu=[Vector((rows[j][12],rows[j][13],0)) for j in ff]
     olduv=barycentric_transform(q,*pp,*uu)
     u0,v0=olduv.x,olduv.y
    elif unwrap:u0,v0=(oldcat+.5)/8,.75
    else:u0,v0=uv.data[li].uv.x,1-uv.data[li].uv.y
    if ob['bone']==0:
     u=(v.x*5-xmin)/(xmax-xmin)*.48+.01;vtex=(v.y*-5-zmin)/(zmax-zmin)*.96+.02
    elif v0<.5:u=.5+u0*.5;vtex=v0
    else:u=.5+u0*.5;vtex=.75
    uv.data[li].uv=(u,1-vtex)
 # Recalculate smooth normals from the simplified topology rather than retaining
 # invalid custom normals interpolated across collapsed edges.
 for ob in result:
  ob.data.normals_split_custom_set_from_vertices([(0,0,0)]*len(ob.data.vertices))
 return result

def fit(sources,target,ratio,unwrap):
 for attempt in range(9):
  obs=reduce_set(sources,ratio,unwrap);rr,ii=exported(obs)
  print('FIT',target,attempt,ratio,len(rr),len(ii)//3,flush=True)
  if target*.95<=len(ii)//3<=target*1.05:return obs,rr,ii
  for ob in obs:bpy.data.objects.remove(ob,do_unlink=True)
  ratio=max(.0005,min(.95,ratio*target/(len(ii)//3)))
 raise RuntimeError('Cannot fit geometry budget')

# Fuse the closely stacked hull surfaces before reduction to prevent intersections.
root_source=base[0].copy();root_source.data=base[0].data.copy();scene.collection.objects.link(root_source);root_source.hide_set(False)
bpy.ops.object.select_all(action='DESELECT');root_source.select_set(True);bpy.context.view_layer.objects.active=root_source
mod=root_source.modifiers.new('Continuous hull','REMESH');mod.mode='VOXEL';mod.voxel_size=.045;mod.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=mod.name)
root_source.hide_render=True;root_source.hide_set(True)
base[21]['main_gondola']=True;base[22]['main_gondola']=True
lod0,r0,i0=fit([root_source,base[21],base[22]],4700,.06,True)
base[21]['main_gondola']=False;base[22]['main_gondola']=False
far_sources=[]
for ob in base.values():
 far=ob.copy();far.data=ob.data.copy();scene.collection.objects.link(far);far.hide_set(False)
 bpy.ops.object.select_all(action='DESELECT');far.select_set(True);bpy.context.view_layer.objects.active=far
 mod=far.modifiers.new('Distant silhouette surface','REMESH');mod.mode='VOXEL';mod.voxel_size=.10;mod.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=mod.name)
 far_sources.append(far);far.hide_render=True;far.hide_set(True)
lod1,r1,i1=fit(far_sources,460,.012,True)
for ob in lod1:ob.hide_render=True;ob.hide_set(True)
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
write_scm(RUNTIME/'GGA0401_lod0.scm',r0,i0);write_scm(RUNTIME/'GGA0401_lod1.scm',r1,i1)
(OUT/'geometry.json').write_text(json.dumps(dict(bones=[b['name'] for b in bones],lod0=dict(vertices=len(r0),triangles=len(i0)//3),lod1=dict(vertices=len(r1),triangles=len(i1)//3)),indent=2))
print('GEOMETRY_DONE',flush=True)


high.hide_render=True;high.hide_set(True)
for ob in lod0:ob.name='Optimized main '+str(ob['bone'])
for ob in lod1:ob.name='Optimized distant '+str(ob['bone'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'DushNai_optimized_work.blend'))
print('DONE',flush=True)

