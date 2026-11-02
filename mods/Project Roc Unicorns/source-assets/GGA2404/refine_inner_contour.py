"""Keep luminous inner contours on the hull skin, clear of coaming cap jumps."""
import bpy,math,struct,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
SRC=Path(__file__).resolve().parent;UNIT=SRC.parents[1]/'units/GGA2404'
bpy.ops.wm.open_mainfile(filepath=str(SRC/'GGA2404_source.blend'));scene=bpy.context.scene;rig=bpy.data.objects['GGA2404'];parts=[o for o in scene.objects if o.type=='MESH' and o.get('asset_part')]
for bone,sign in [('GondolaL',-1),('GondolaR',1)]:
 hull=next(o for o in parts if o.get('main_gondola') and o['rig_bone']==bone);bv=BVHTree.FromPolygons([v.co for v in hull.data.vertices],[list(p.vertices) for p in hull.data.polygons])
 for ob in [o for o in parts if o['rig_bone']==bone and o.name.startswith('Artist gondola inner luminous contour')]:
  for v in ob.data.vertices:
   hit,n,_,_=bv.ray_cast(Vector((-sign*3,v.co.y,v.co.z)),Vector((sign,0,0)))
   assert hit is not None
   if n.x*sign>0:n=-n
   v.co=hit+n*.0022
  ob.data.update()
  for p in ob.data.polygons:
   if p.normal.x*sign>0:p.flip()
  ob.data.update()
exec(compile((SRC/'native_export.py').read_text(),str(SRC/'native_export.py'),'exec'))
for i in [0,1]:print('INNER_CONTOUR_EXPORT',i,write_scm(UNIT/f'GGA2404_lod{i}.scm',parts,i==1),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'GGA2404_source.blend'))
