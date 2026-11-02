"""Single luminous bore surface instead of overlapping hull/shell/lining walls.

Run inside generator namespace after engraving, before inset/lift/rig binding;
also supports repairing the existing bound authoring scene.
"""
import bmesh
def repair_ring_bores(parts,create_mesh):
    result=[]
    for bone in ['GondolaL','GondolaR']:
        rim=next(o for o in parts if o.get('through_ring') and o['rig_bone']==bone)
        existing=[o for o in parts if o.get('ring_bore_single_surface') and o['rig_bone']==bone]
        if existing:
            assert len(existing)==1
            result.append({'bone':bone,'already_repaired':True,'radius':existing[0]['bore_radius']})
            continue
        cx,cy,cz=rim['axis_center'];radius=.385;xs=[];removed={}
        for ob in [o for o in parts if o['rig_bone']==bone and (o.get('main_gondola') or o.get('through_ring'))]:
            bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
            faces=[f for f in bm.faces if abs(f.normal.x)<.03 and all(abs(((v.co.y-cy)**2+(v.co.z-cz)**2)**.5-radius)<.0011 for v in f.verts)]
            xs.extend(v.co.x for f in faces for v in f.verts);removed[ob.name]=len(faces)
            assert faces,'Expected old bore wall: '+ob.name
            bmesh.ops.delete(bm,geom=faces,context='FACES');loose=[v for v in bm.verts if not v.link_faces]
            if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
            bm.to_mesh(ob.data);bm.free();ob.data.update()
        for old in [o for o in parts if o['rig_bone']==bone and o.get('inner_ring_glow')]:
            parts.remove(old);bpy.data.objects.remove(old,do_unlink=True)
        # Keep the original 64-sided aperture radius and span all removed walls.
        lo,hi=min(xs),max(xs);n=64;verts=[];uv=[]
        for j,x in enumerate([lo,hi]):
            for k in range(n+1):
                a=2*pi*k/n;verts.append((x,cy+radius*cos(a),cz+radius*sin(a)));uv.append((k/n,j))
        faces=[(k,n+1+k,n+2+k,k+1) for k in range(n)] # normals toward aperture
        ob=create_mesh('Single luminous bore wall / '+bone,verts,faces,5,bone,True,uv)
        ob['inner_ring_glow']=True;ob['ring_bore_single_surface']=True;ob['preserve_aperture']=True;ob['bore_radius']=radius
        result.append({'bone':bone,'removed_faces':removed,'lining_faces':64,'radius':radius,'axial_span':[lo,hi]})
    return result
