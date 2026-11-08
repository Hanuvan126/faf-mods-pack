import bpy,math,json
from pathlib import Path
from mathutils import Vector
out=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath='F:/FAF-Development/outputs/IshalThar_A4_Model_09/IshalThar_A4_v09.blend')
bpy.context.scene.frame_set(1)
for o in bpy.context.scene.objects:
 if o.type=='CURVE' and any('Team' in m.name for m in o.data.materials if m):
  o.data.bevel_depth *= 2

objs=[o for o in bpy.context.scene.objects if o.type in {'MESH','CURVE'} and not o.name.startswith('Studio')]
names=['GGA2301','TurretYaw','TurretPitch','GunRecoil','MuzzleLeft','MuzzleRight']
parents=[-1,0,1,2,3,3]
world=[Vector((0,0,0)),bpy.data.objects['TurretYaw'].matrix_world.translation.copy(),bpy.data.objects['TurretPitch'].matrix_world.translation.copy(),bpy.data.objects['TurretPitch'].matrix_world.translation.copy(),bpy.data.objects['MuzzleLeft'].matrix_world.translation.copy(),bpy.data.objects['MuzzleRight'].matrix_world.translation.copy()]
def cv(p):return (p.x,p.z,-p.y)
pivots=[cv(p if parents[i]<0 else p-world[parents[i]]) for i,p in enumerate(world)]
# Export material islands via a padded palette atlas; team curves retain geometry.
def material_id(o):
 n=o.data.materials[0].name if len(o.data.materials) else ''
 if 'Team' in n:return 3
 if 'white' in n.lower():return 4
 if 'Machined' in n:return 1
 if 'Recessed' in n:return 2
 return 0

def bone(o):
 p=o
 while p:
  if p.name=='TurretPitch':return 3
  if p.name=='TurretYaw':return 1
  p=p.parent
 return 0

report=[]
for lod in [0,1]:
 vertices=[];indices=[];lookup={}
 def add(p,n,mat,b,uv=None):
  p=cv(p);n=Vector(cv(n)).normalized();t=n.cross(Vector((0,1,0)))
  if t.length<.01:t=n.cross(Vector((1,0,0)))
  t.normalize();bt=n.cross(t).normalized();uv=uv if uv is not None else ((mat+.5)/8,.05)
  v=tuple(p)+tuple(n)+tuple(t)+tuple(bt)+uv+uv+(b,)
  key=tuple(round(x,6) for x in v)
  if key not in lookup:lookup[key]=len(vertices);vertices.append(v)
  return lookup[key]
 for original in objs:
  mat=material_id(original);b=bone(original)
  if original.type=='CURVE':
   # Thin round strips retain the exact approved surface paths, with fewer longitudinal samples.
   for sp in original.data.splines:
    raw=[original.matrix_world@Vector(p.co[:3]) for p in sp.points]
    pts=[]
    for p in raw:
     if not pts or (p-pts[-1]).length>(.028 if lod==0 else .055):pts.append(p)
    if raw and (not pts or (pts[-1]-raw[-1]).length>.0001):pts.append(raw[-1])
    if len(pts)<2:continue
    ring=[];sides=4 if lod==0 else 3
    for j,p in enumerate(pts):
     tangent=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized()
     a=tangent.cross(Vector((0,0,1)))
     if a.length<.01:a=tangent.cross(Vector((1,0,0)))
     a.normalize();c=tangent.cross(a).normalized()
     rr=[]
     for k in range(sides):
      n=a*math.cos(k*2*math.pi/sides)+c*math.sin(k*2*math.pi/sides)
      rr.append(add(p+n*original.data.bevel_depth,n,mat,b))
     ring.append(rr)
    for r0,r1 in zip(ring,ring[1:]):
     for k in range(sides):
      q=(k+1)%sides;indices.extend([r0[k],r0[q],r1[q],r0[k],r1[q],r1[k]])
   continue
  o=original.copy();o.data=original.data.copy();bpy.context.collection.objects.link(o)
  bpy.context.view_layer.objects.active=o
  tris=sum(len(p.vertices)-2 for p in o.data.polygons)
  if original.name.startswith('Sculpted'):target=5500 if lod==0 else 1800
  elif original.name.startswith('Wide turtle'):target=4200 if lod==0 else 1400
  else:target=650 if lod==0 else 220
  if tris>target:
   mod=o.modifiers.new('Game silhouette LOD','DECIMATE');mod.ratio=target/tris;bpy.ops.object.modifier_apply(modifier=mod.name)
  me=o.data;me.calc_loop_triangles();normalmat=o.matrix_world.to_3x3().inverted().transposed()
  for tri in me.loop_triangles:
   for vid in tri.vertices:
    v=me.vertices[vid];pos=o.matrix_world@v.co;norm=normalmat@v.normal;uv=None
    if mat==0 and original.name.startswith('Wide turtle') and norm.z>.1:
     uv=(.02+.46*(pos.x+2.5)/5,.15+.8*(pos.y+2.5)/5)
    elif mat==0 and original.name.startswith('Sculpted'):
     radial=Vector((pos.x,pos.y,0)).normalized()
     if norm.normalized().dot(radial)>.2:
      center=sum((o.matrix_world@me.vertices[k].co for k in tri.vertices),Vector())/3
      ang=math.atan2(center.y,center.x)
      sector=round((ang+math.pi/2)/(2*math.pi/3))
      relative=math.atan2(pos.y,pos.x)-(-math.pi/2+sector*2*math.pi/3)
      relative=(relative+math.pi)%(2*math.pi)-math.pi
      u=relative*1.4
      uv=(.52+.46*(u+1.5)/3,.15+.8*pos.z/2.5)
    indices.append(add(pos,norm,mat,b,uv))
  bpy.data.objects.remove(o,do_unlink=True)
 assert len(vertices)<65536,len(vertices)
 data={'names':names,'parents':parents,'pivots':pivots,'vertices':vertices,'indices':indices}
 (out/f'lod{lod}.json').write_text(json.dumps(data,separators=(',',':')))
 report.append({'lod':lod,'vertices':len(vertices),'triangles':len(indices)//3})
(out/'geometry_report.json').write_text(json.dumps(report,indent=2));print('EXPORT_COMPLETE',report)

bpy.ops.wm.save_as_mainfile(filepath=str(out/'IshalThar_v10.blend'))
