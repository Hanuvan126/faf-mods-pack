import bpy,math
from pathlib import Path
from mathutils import Vector
p=Path('F:/FAF-Development/work/faf-upload/mods/Project Roc Unicorns/source-assets/GGA2301/comet-v2')
bpy.ops.wm.open_mainfile(filepath=str(p/'IshalThar_v10.blend'))
image=bpy.data.images.load(str(p/'albedo_source.png'),check_existing=True);image.pack()
mat=bpy.data.materials.new('Seraphim metal with approved team-mask fills');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=.27
tex=nodes.new('ShaderNodeTexImage');tex.image=image
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX'
mix.inputs[1].default_value=(.065,.07,.085,1);mix.inputs[2].default_value=(.30,.065,.55,1)
links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(mix.outputs[0],bs.inputs['Base Color'])
for o in bpy.context.scene.objects:
 if o.type=='CURVE' and any('Team' in m.name for m in o.data.materials if m):
  for m in o.data.materials:
   if m.use_nodes:
    b=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if b:
     b.inputs['Metallic'].default_value=1;b.inputs['Roughness'].default_value=.27
     b.inputs['Emission Strength'].default_value=.06
 if o.name not in ['Wide turtle carapace','Sculpted continuous pedestal']:continue
 o.data.materials.clear();o.data.materials.append(mat)
 uv=o.data.uv_layers.get('TeamFillUV') or o.data.uv_layers.new(name='TeamFillUV')
 o.data.uv_layers.active=uv
 nm=o.matrix_world.to_3x3().inverted().transposed()
 for face in o.data.polygons:
  center=o.matrix_world@face.center;normal=nm@face.normal
  sector=round((math.atan2(center.y,center.x)+math.pi/2)/(2*math.pi/3))
  for lid in face.loop_indices:
   pos=o.matrix_world@o.data.vertices[o.data.loops[lid].vertex_index].co
   u,v=.5/8,.05
   if o.name.startswith('Wide') and normal.z>.1:
    u,v=.02+.46*(pos.x+2.5)/5,.15+.8*(pos.y+2.5)/5
   elif o.name.startswith('Sculpted') and normal.normalized().dot(Vector((pos.x,pos.y,0)).normalized())>.2:
    rel=(math.atan2(pos.y,pos.x)-(-math.pi/2+sector*2*math.pi/3)+math.pi)%(2*math.pi)-math.pi
    u,v=.52+.46*(rel*1.4+1.5)/3,.15+.8*pos.z/2.5
   # Blender's image UV origin differs from the game DDS row convention.
   uv.data[lid].uv=(u,1-v)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'IshalThar_v10.blend'))
print('EDITABLE_BLEND_UPDATED')

