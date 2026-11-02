"""Apply approved artist sketches to current source; keep accepted runtime intact otherwise."""
import bpy,math,struct,json
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
SRC=Path(__file__).resolve().parent;UNIT=SRC.parents[1]/'units/GGA2404';OUT=Path('F:/FAF-Development/outputs/VaelItha_Lower_Petals_v10')
bpy.ops.wm.open_mainfile(filepath=str(SRC/'GGA2404_source.blend'));scene=bpy.context.scene;rig=bpy.data.objects['GGA2404'];parts=[o for o in scene.objects if o.type=='MESH' and o.get('asset_part')];materials=list(parts[0].data.materials)
def mesh(name,verts,faces,mat,bone,smooth,uv):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
 for m in materials:me.materials.append(m)
 for p in me.polygons:p.material_index=mat;p.use_smooth=smooth
 layer=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  for li in p.loop_indices:
   u,v=uv[me.loops[li].vertex_index];layer.data[li].uv=((mat%4+(20+u*216)/256)/4,1-(mat//4+(20+v*216)/256)/2)
 ob['rig_bone']=bone;ob['asset_part']=True;parts.append(ob);return ob
exec(compile((SRC/'apply_lower_petals.py').read_text(),str(SRC/'apply_lower_petals.py'),'exec'))
report=apply_lower_petals(parts,mesh)
for ob in parts:
 if not ob.get('lower_petal_v10'):continue
 ob.parent=rig;g=ob.vertex_groups.new(name=ob['rig_bone']);g.add(list(range(len(ob.data.vertices))),1,'REPLACE');mod=ob.modifiers.new('Rigid skeletal deformation','ARMATURE');mod.object=rig
exec(compile((SRC/'native_export.py').read_text(),str(SRC/'native_export.py'),'exec'))
report['native_mesh']={str(i):write_scm(UNIT/f'GGA2404_lod{i}.scm',parts,i==1) for i in [0,1]}
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'GGA2404_source.blend'))
(OUT/'report.json').write_text(json.dumps(report,indent=2));print('LOWER_PETALS_COMPLETE',report['petals'],flush=True)
