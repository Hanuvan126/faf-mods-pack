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


bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parents[2]/'ShaVeyr.blend'))
scene=bpy.context.scene;scene.frame_set(1)
source=[o for o in scene.objects if o.type=='MESH' and not o.name.startswith('Studio')]
def matid(o):
 n=o.data.materials[0].name if o.data.materials else ''
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
curves=[]
for o in scene.objects:
 if o.type=='CURVE' and any('Team' in m.name for m in o.data.materials if m):
  for sp in o.data.splines:
   pts=[list(o.matrix_world@Vector(p.co[:3])) for p in sp.points]
   curves.append(dict(name=o.name,bone=bone(o),points=pts,width=o.data.bevel_depth*2))
(OUT/'ornament_curves.json').write_text(json.dumps(curves))
reports=[]
for lod in [0,1]:
 rr=[];ii=[];lookup={};parts=[]
 for original in source:
  name=original.name;ring=len(original.data.vertices) in [320,400,480,800] and len(original.data.polygons)==len(original.data.vertices)
  if lod==1 and (name.startswith('White accelerator') or name.startswith('Barrel dark') or name.startswith('Machined muzzle') or name.startswith('Bearing white')):continue
  ob=original.copy();ob.data=original.data.copy();scene.collection.objects.link(ob)
  if ring:
   nprof=len(original.data.vertices)//80
   if name.startswith('Barrel armored'):profiles=[0,2,4,6,8,9] if lod==0 else [0,4,9]
   else:profiles=list(range(nprof)) if lod==0 else [0,nprof//2]
   segments=20 if lod==0 and name.startswith(('Barrel armored','Machined muzzle')) else (12 if lod==0 else 8)
   verts=[]
   for j in profiles:
    for k in range(segments):
     x=k*80/segments;lo=int(x);t=x-lo
     verts.append(original.data.vertices[j*80+lo].co.lerp(original.data.vertices[j*80+(lo+1)%80].co,t))
   ff=[]
   for j in range(len(profiles) if len(profiles)>2 else 1):
    for k in range(segments):ff.append((j*segments+k,j*segments+(k+1)%segments,((j+1)%len(profiles))*segments+(k+1)%segments,((j+1)%len(profiles))*segments+k))
   me=bpy.data.meshes.new(name+' clean rings');me.from_pydata(verts,[],ff);me.update();ob.data=me
  else:
   if name.startswith('Sculpted'):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    rm=ob.modifiers.new('Far clean pedestal','REMESH');rm.mode='VOXEL';rm.voxel_size=.035 if lod==0 else .065;rm.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rm.name)
   tris=sum(len(p.vertices)-2 for p in ob.data.polygons)
   target=(950 if lod==0 else 210) if name.startswith('Sculpted') else ((850 if lod==0 else 170) if name.startswith('Wide turtle') else (120 if lod==0 else 24))
   bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
   dec=ob.modifiers.new('Part budget','DECIMATE');dec.ratio=min(1,target/tris);dec.use_symmetry=name.startswith(('Sculpted','Wide'));dec.symmetry_axis='X';bpy.ops.object.modifier_apply(modifier=dec.name)
  me=ob.data
  for p in me.polygons:p.use_smooth=True
  me.update();me.calc_loop_triangles();normalmat=ob.matrix_world.to_3x3().inverted().transposed();m=matid(original);bid=bone(original)
  uvlay=me.uv_layers.get('GameUV') or me.uv_layers.new(name='GameUV')
  for tri in me.loop_triangles:
   center=sum((ob.matrix_world@me.vertices[k].co for k in tri.vertices),Vector())/3
   sector=round((math.atan2(center.y,center.x)+math.pi/2)/(2*math.pi/3))
   for li,vid in zip(tri.loops,tri.vertices):
    v=me.vertices[vid];p=ob.matrix_world@v.co;n=(normalmat@v.normal).normalized();uv=((m+.5)/8,.05)
    if name.startswith('Wide') and n.z>.1:uv=(.02+.46*(p.x+2.5)/5,.15+.8*(p.y+2.5)/5)
    elif name.startswith('Sculpted') and n.dot(Vector((p.x,p.y,0)).normalized())>.2:
     rel=(math.atan2(p.y,p.x)-(-math.pi/2+sector*2*math.pi/3)+math.pi)%(2*math.pi)-math.pi
     uv=(.52+.46*(rel*1.4+1.5)/3,.15+.8*p.z/2.5)
    if n.length<.5:n=(normalmat@tri.normal).normalized()
    uvlay.data[li].uv=(uv[0],1-uv[1])
    n=Vector((n.x,n.z,-n.y));t=n.cross(Vector((0,1,0)))
    if t.length<.01:t=n.cross(Vector((1,0,0)))
    t.normalize();bt=n.cross(t).normalized();row=(p.x,p.z,-p.y,*n,*t,*bt,*uv,*uv,bid)
    key=tuple(round(float(x),6) for x in row)
    if key not in lookup:lookup[key]=len(rr);rr.append(row)
    ii.append(lookup[key])
  parts.append((name,len(me.loop_triangles)));ob.hide_render=True;ob.hide_set(True)
 write_scm(RUNTIME/f'GGA2302_lod{lod}.scm',rr,ii)
 reports.append(dict(lod=lod,vertices=len(rr),triangles=len(ii)//3,bones=len(bones),parts=parts));print(reports[-1],flush=True)
(OUT/'geometry.json').write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ShaVeyr_parts.blend'))
