import bpy,struct,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__import__('os').environ.get('DUSH_OPT_WORK',str(Path(__file__).resolve().parent/'work')))
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('World');s.world.color=(.2,.2,.2);s.view_settings.view_transform='AgX'
def material(level):
 m=bpy.data.materials.new(str(level));m.use_nodes=True;nd=m.node_tree.nodes;lk=m.node_tree.links;bs=next(n for n in nd if n.type=='BSDF_PRINCIPLED');bs.inputs['Metallic'].default_value=.85;bs.inputs['Roughness'].default_value=.32
 ts={}
 for k in ['albedo','specteam']:
  t=nd.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/('original/'+k+'.png' if level=='before' else f'decoded_lod{level}_{k}.png')));t.image.colorspace_settings.name='Non-Color';ts[k]=t
 base=nd.new('ShaderNodeMixRGB');base.blend_type='MULTIPLY';base.inputs[0].default_value=1;base.inputs[2].default_value=(1.9,1.9,1.9,1);lk.new(ts['albedo'].outputs[0],base.inputs[1])
 team=nd.new('ShaderNodeMixRGB');lk.new(ts['specteam'].outputs['Alpha'],team.inputs[0]);lk.new(base.outputs[0],team.inputs[1]);team.inputs[2].default_value=(.23,.045,.65,1);lk.new(team.outputs[0],bs.inputs['Base Color']);lk.new(team.outputs[0],bs.inputs['Emission Color'])
 sep=nd.new('ShaderNodeSeparateColor');lk.new(ts['specteam'].outputs[0],sep.inputs[0]);lk.new(sep.outputs['Blue'],bs.inputs['Emission Strength'])
 if False:
  tx=nd.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(OUT/f'baked_lod{level}_normal.png'));tx.image.colorspace_settings.name='Non-Color';nm=nd.new('ShaderNodeNormalMap');lk.new(tx.outputs[0],nm.inputs['Color']);lk.new(nm.outputs[0],bs.inputs['Normal'])
 return m
objects=[]
for level in ['before',0,1]:
 p=OUT/('original/GGA0401_lod0.scm' if level=='before' else f'runtime/GGA0401_lod{level}.scm');raw=p.read_bytes();h=struct.unpack_from('<4s11I',raw);rows=[struct.unpack_from('<16f4B',raw,h[4]+i*68) for i in range(h[6])];faces=list(zip(*[iter(struct.unpack_from('<%dH'%h[8],raw,h[7]))]*3))
 me=bpy.data.meshes.new(str(level));me.from_pydata([(r[0]/5,-r[2]/5,r[1]/5) for r in rows],[],faces);me.update();uv=me.uv_layers.new()
 for poly in me.polygons:
  poly.use_smooth=True
  for li,vi in zip(poly.loop_indices,poly.vertices):uv.data[li].uv=(rows[vi][12],1-rows[vi][13])
 me.normals_split_custom_set_from_vertices([(r[3],-r[5],r[4]) for r in rows]);ob=bpy.data.objects.new(str(level),me);s.collection.objects.link(ob);me.materials.append(material(level));ob.hide_render=True;objects.append(ob)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.04));floor=bpy.context.object;m=bpy.data.materials.new('Floor');m.diffuse_color=(.14,.15,.17,1);floor.data.materials.append(m)
for loc,power,size in [((2,-6,10),1700,7),((-6,0,7),1800,6),((3,6,9),2300,5)]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new('Softbox',d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);s.collection.objects.link(cam);s.camera=cam;d.type='ORTHO';d.ortho_scale=11.7
for ob in objects:
 ob.hide_render=False
 for view,pos in [('perspective',(10,-13,10)),('top',(0,0,16))]:
  cam.location=pos;cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/f'{ob.name}_{view}.png');bpy.ops.render.render(write_still=True)
 ob.hide_render=True
print('RENDER_DONE',flush=True)


