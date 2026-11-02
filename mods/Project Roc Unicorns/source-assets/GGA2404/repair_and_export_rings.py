"""Repair authoritative source scene and native SCM without rebuilding gameplay."""
import bpy,math,struct,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
SRC=Path(__file__).resolve().parent;UNIT=SRC.parents[1]/'units/GGA2404';OUT=Path('F:/FAF-Development/outputs/VaelItha_Selection_Ring_Fix_v7')
bpy.ops.wm.open_mainfile(filepath=str(SRC/'GGA2404_source.blend'));scene=bpy.context.scene;rig=bpy.data.objects['GGA2404'];parts=[o for o in scene.objects if o.type=='MESH' and o.get('asset_part') and o.get('rig_bone')!='Charge'];materials=list(parts[0].data.materials)
exec(compile((SRC/'native_export.py').read_text(),str(SRC/'native_export.py'),'exec'))
baseline={}
for lod in [0,1]:
 p=OUT/f'baseline_lod{lod}.scm';write_scm(p,parts,lod==1)
 baseline[str(lod)]={'byte_identical':p.read_bytes()==(UNIT/f'GGA2404_lod{lod}.scm').read_bytes()}
print('BASELINE_EXPORT',baseline,flush=True)
def mesh(name,verts,faces,mat,bone,smooth,uv):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
 for m in materials:me.materials.append(m)
 for p in me.polygons:p.material_index=mat;p.use_smooth=smooth
 layer=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  for li in p.loop_indices:
   u,v=uv[me.loops[li].vertex_index];layer.data[li].uv=((mat%4+(20+u*216)/256)/4,1-(mat//4+(20+v*216)/256)/2)
 ob['rig_bone']=bone;ob['asset_part']=True;parts.append(ob);return ob
exec(compile((SRC/'fix_ring_bore.py').read_text(),str(SRC/'fix_ring_bore.py'),'exec'))
report=repair_ring_bores(parts,mesh)
for ob in parts:
 if not ob.get('ring_bore_single_surface'):continue
 ob.parent=rig;g=ob.vertex_groups.new(name=ob['rig_bone']);g.add(list(range(len(ob.data.vertices))),1,'REPLACE');mod=ob.modifiers.new('Rigid skeletal deformation','ARMATURE');mod.object=rig
stats={}
for lod in [0,1]:stats[str(lod)]=write_scm(UNIT/f'GGA2404_lod{lod}.scm',parts,lod==1)
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'GGA2404_source.blend'))
# Pattern authoring information is geometry-based, not a unique UV texture tile.
pattern=[]
for ob in parts:
 mats={p.material_index for p in ob.data.polygons}
 if not (ob.get('decorative_pattern') or 5 in mats):continue
 pattern.append({'name':ob.name,'bone':ob['rig_bone'],'engraved':bool(ob.get('engraved_inlay')),'vertices':[list(v.co) for v in ob.data.vertices],'faces':[list(p.vertices) for p in ob.data.polygons]})
(OUT/'pattern_geometry.json').write_text(json.dumps(pattern))
(OUT/'ring_repair_report.json').write_text(json.dumps({'baseline':baseline,'bores':report,'native_mesh':stats},indent=2));print('RING_REPAIR_EXPORT_COMPLETE',report,stats,flush=True)
