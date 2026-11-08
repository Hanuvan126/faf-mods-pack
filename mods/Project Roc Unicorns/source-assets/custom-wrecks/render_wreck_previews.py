import bpy,struct
from pathlib import Path
from mathutils import Vector
r=Path('F:/FAF-Development');m=r/'work/faf-upload/mods/Project Roc Unicorns';out=r/'outputs/Local_T3_Massive_Wrecks_v6'
for unit,scale in [('GGA2404',.05)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.world=bpy.data.worlds.new('World');s.world.color=(.16,.16,.16)
 raw=(m/f'props/{unit}_wreck/{unit}_wreck_lod0.scm').read_bytes();h=struct.unpack_from('<4s11I',raw)
 v=[struct.unpack_from('<16f4B',raw,h[4]+i*68) for i in range(h[6])];ix=struct.unpack_from('<'+'H'*h[8],raw,h[7]);faces=[ix[i:i+3] for i in range(0,len(ix),3)]
 me=bpy.data.meshes.new('Native wreck');me.from_pydata([(a[0]*scale,-a[2]*scale,a[1]*scale) for a in v],[],faces);me.update();me.normals_split_custom_set_from_vertices([(a[3],-a[5],a[4]) for a in v]);uv=me.uv_layers.new()
 for p in me.polygons:
  p.use_smooth=True
  for li,vi in zip(p.loop_indices,p.vertices):uv.data[li].uv=(v[vi][12],1-v[vi][13])
 ob=bpy.data.objects.new('Custom '+unit+' corpse',me);s.collection.objects.link(ob)
 mat=bpy.data.materials.new('Decoded charred DDS');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=.2;bs.inputs['Roughness'].default_value=.85
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/f'{unit}_decoded_wreck.png'));tex.image.colorspace_settings.name='Non-Color';mat.node_tree.links.new(tex.outputs[0],bs.inputs['Base Color'])
 noise=mat.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=80;bump=mat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.035;mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs[0],bs.inputs['Normal']);me.materials.append(mat)
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));floor=bpy.context.object;fm=bpy.data.materials.new('Ground');fm.diffuse_color=(.13,.14,.15,1);floor.data.materials.append(fm)
 for pos,power,size in [((3,-5,8),950,5),((-5,0,5),1100,5),((0,6,5),1300,4)]:
  ld=bpy.data.lights.new('Softbox','AREA');ld.energy=power;ld.size=size;light=bpy.data.objects.new('Softbox',ld);s.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.4))-light.location).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);s.collection.objects.link(cam);cam.location=(6,-8,6.4);cam.rotation_euler=(Vector((0,0,.45))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=6.4;s.camera=cam
 s.render.engine='CYCLES';s.cycles.samples=28;s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.filepath=str(out/f'{unit}_wreck_preview.png');bpy.ops.render.render(write_still=True)
 print('WRECK_PREVIEW_DONE',unit,flush=True)
