import bpy, struct, json, shutil, zipfile
from mathutils.bvhtree import BVHTree
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())
SRC=ROOT/'mods/Project Roc Unicorns/source-assets/GGA2404'
UNIT=ROOT/'mods/Project Roc Unicorns/units/GGA2404'
OUT=ROOT/'outputs/VaelItha_Optimization'
OUT.mkdir(exist_ok=True);(OUT/'runtime').mkdir(exist_ok=True);(OUT/'original').mkdir(exist_ok=True)
if not (OUT/'before.zip').exists():
 with zipfile.ZipFile(OUT/'before.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in UNIT.iterdir():
   if p.is_file():z.write(p,p.name);shutil.copy2(p,OUT/'original'/p.name)
bpy.ops.wm.open_mainfile(filepath=str(SRC/'GGA2404_source.blend'))
scene=bpy.context.scene
rig=next(o for o in scene.objects if o.type=='ARMATURE')
objects=[o for o in scene.objects if o.type=='MESH' and o.get('asset_part')]
code=(SRC/'native_export.py').read_text()
code=code.replace("if decimate and len(tmp.data.polygons)>3 and not (ob.get('preserve_aperture') and (ob.get('main_gondola') or ob.get('ring_bore_single_surface'))):", "if decimate and len(tmp.data.polygons)>3:")
code=code.replace("m.ratio=.38", "m.ratio=ob.get('opt_ratio',.4)")
code=code.replace('if decimate:\n', 'if False:\n')
code=code.replace('me.calc_tangents(uvmap=me.uv_layers.active.name)', "if not me.polygons:\n            evaluated.to_mesh_clear();bpy.data.objects.remove(tmp,do_unlink=True);continue\n        me.calc_tangents(uvmap=me.uv_layers.active.name)")
exec(code)
original=(OUT/'original/GGA2404_lod0.scm').read_bytes();oh=struct.unpack_from('<4s11I',original)
def original_bones(path):
 data=bytearray(path.read_bytes());h=struct.unpack_from('<4s11I',data)
 assert h[11]==oh[11]
 for i in range(h[11]):
  old=list(struct.unpack_from('<16f3f4f4i',original,oh[2]+108*i));new=list(struct.unpack_from('<16f3f4f4i',data,h[2]+108*i))
  assert original[old[23]:original.index(b'\0',old[23])]==data[new[23]:data.index(b'\0',new[23])]
  old[23]=new[23];struct.pack_into('<16f3f4f4i',data,h[2]+108*i,*old)
 path.write_bytes(data)
stats={}
def resample_ring(ob,step):
 old=ob.data
 shell=ob.get('through_ring') or ob.get('ring_bore_single_surface')
 if not shell:return False
 n=65;profiles=len(old.vertices)//n
 if profiles*n!=len(old.vertices):return False
 angles=list(range(0,65,step));vs=[old.vertices[p*n+a].co.copy() for p in range(profiles) for a in angles]
 faces=[];meta=[];uvs=[];nn=len(angles)
 for p in range(profiles-1):
  for j,a in enumerate(angles[:-1]):
   poly=old.polygons[p*64+a];end=old.polygons[p*64+a+step-1]
   faces.append((p*nn+j,(p+1)*nn+j,(p+1)*nn+j+1,p*nn+j+1));meta.append((poly.material_index,poly.use_smooth))
   lu=old.uv_layers.active.data
   ud={vi:lu[li].uv.copy() for pol in [poly,end] for vi,li in zip(pol.vertices,pol.loop_indices)}
   uv=[ud[p*n+a],ud[(p+1)*n+a],ud[(p+1)*n+a+step],ud[p*n+a+step]]
   if poly.vertices[1]==p*n+a+1:
    faces[-1]=tuple(reversed(faces[-1]));uv=list(reversed(uv))
   uvs.append(uv)
 me=bpy.data.meshes.new(ob.name+' reduced ring');me.from_pydata(vs,[],faces);me.update()
 for m in old.materials:me.materials.append(m)
 layer=me.uv_layers.new()
 for poly,(mat,smooth),uv in zip(me.polygons,meta,uvs):
  poly.material_index=mat;poly.use_smooth=smooth
  for li,v in zip(poly.loop_indices,uv):layer.data[li].uv=v
 ob.data=me;return True
for lod in [0,1]:
 prepared=[];pairs=[]
 for ob in objects:
  if lod==1 and ob.get('engraved_inlay'):continue
  ratio=.16 if lod==0 else .06
  if ob.get('engraved_inlay'):ratio=.22 if lod==0 else .08
  if ob.get('main_gondola') or ob.get('foundation_petal'):ratio=.50 if lod==0 else .30
  if ob.get('through_ring'):ratio=.35 if lod==0 else .15
  if ob.get('ring_bore_single_surface'):ratio=1 if lod==0 else .5
  if ob['rig_bone'].startswith('Field'):ratio=.45
  tmp=ob.copy();tmp.data=ob.data.copy();scene.collection.objects.link(tmp)
  for m in list(tmp.modifiers):tmp.modifiers.remove(m)
  if not resample_ring(tmp,2 if lod==0 else 4) and len(tmp.data.polygons)>3:
   mod=tmp.modifiers.new('Part simplification','DECIMATE');mod.ratio=ratio
   bpy.context.view_layer.objects.active=tmp
   bpy.ops.object.modifier_apply(modifier=mod.name)
  if tmp.data.polygons:prepared.append(tmp);pairs.append((ob,tmp))
 receivers=[(a,b) for a,b in pairs if a.get('foundation_petal') or a.get('main_gondola') or a.get('through_ring') or a.name.startswith(('Tri-lobed polished crown','Crown sculptural rib'))]
 trees={b:BVHTree.FromPolygons([v.co for v in b.data.vertices],[list(p.vertices) for p in b.data.polygons]) for a,b in receivers}
 originaltrees={a:BVHTree.FromPolygons([v.co for v in a.data.vertices],[list(p.vertices) for p in a.data.polygons]) for a,b in receivers}
 for a,b in pairs:
  if not a.get('engraved_inlay'):continue
  candidates=[(x,y) for x,y in receivers if x['rig_bone']==a['rig_bone']]
  if 'Ring' in a.name or 'ring' in a.name:candidates=[(x,y) for x,y in candidates if x.get('through_ring')]
  if not candidates:continue
  sample=list(a.data.vertices)[::max(1,len(a.data.vertices)//8)]
  x,y=min(candidates,key=lambda xy:sum(originaltrees[xy[0]].find_nearest(v.co)[3] for v in sample))
  for v in b.data.vertices:
   pos,normal,idx,dist=trees[y].find_nearest(v.co)
   if dist<.12:v.co=pos+normal*.003
  b.data.update()
 file=OUT/f'runtime/GGA2404_lod{lod}.scm'
 stats['lod'+str(lod)]=write_scm(file,prepared,False);original_bones(file)
 for tmp in prepared:bpy.data.objects.remove(tmp,do_unlink=True)
 print(lod,stats['lod'+str(lod)],flush=True)
(OUT/'geometry.json').write_text(json.dumps(stats,indent=2))
