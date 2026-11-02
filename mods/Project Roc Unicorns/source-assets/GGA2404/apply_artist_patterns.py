"""2026-11-02 hand-drawn references translated into fitted geometric inlays."""
import math,json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
def apply_artist_patterns(parts,mesh):
    report={'petals':[],'gondolas':[],'designs':[]}
    def tree(ob):return BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])
    def remove(ob):parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    # Support repeatable runs without duplicating newly authored strokes.
    for ob in list(parts):
        if ob.get('artist_pattern_20261102'):remove(ob)
    def ribbon(name,points,receiver,material=3,width=.006,projector=None):
        bv=tree(receiver);points=[Vector(p) for p in points];vs=[];uv=[]
        for i,p in enumerate(points):
            tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
            hit,normal,_,_=bv.find_nearest(p) if projector is None else projector(p,bv)
            assert hit is not None,name
            side=normal.cross(tangent).normalized()
            for sign in [-1,1]:
                q,n,_,_=bv.find_nearest(hit+side*width*sign) if projector is None else projector(hit+side*width*sign,bv)
                vs.append(q+n*.0022);uv.append((i/(len(points)-1),(sign+1)/2))
        faces=[(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(points)-1)]
        # Ensure triangle winding follows the receiving skin on mirrored parts.
        for j,f in enumerate(faces):
            a,b,c=[vs[k] for k in f[:3]];normal=bv.find_nearest((a+b+c)/3)[1]
            if (b-a).cross(c-a).dot(normal)<0:faces[j]=tuple(reversed(f))
        ob=mesh(name,vs,faces,material,receiver['rig_bone'],True,uv);ob['artist_pattern_20261102']=True;ob['decorative_pattern']=material==3;ob['engraved_inlay']=True
        return ob
    def centers(ob):
        v=np.array([tuple(p.co) for p in ob.data.vertices]);n=2 if ob.get('engraved_inlay') else 4
        return v[:len(v)//n*n].reshape(-1,n,3).mean(1)
    controls=np.array([(.22,.91,.14),(.42,1,.26),(.65,.83,.41),(.91,.56,.55),(1.18,.31,.56),(1.49,.135,.38),(1.76,.055,.18),(1.94,.025,.004)])
    def prof(t):
        t=min(6.999999,max(0,t));j=int(t);u=t-j;a,b,c,d=controls[max(0,j-1)],controls[j],controls[j+1],controls[min(7,j+2)]
        return .5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u**3)
    ts=np.linspace(0,7,1401);prs=np.array([prof(t) for t in ts])
    # Two petal types, three copies each. Hatching stays outside a symmetric
    # envelope around ALL existing motifs, including their empty inner circles.
    for idx,deg,secondary in [(1,-150,False),(2,-30,False),(3,90,False),(4,-90,True),(5,30,True),(6,150,True)]:
        receiver=next(o for o in parts if o.get('foundation_petal') and o.name.endswith('petal '+str(idx)))
        a=math.radians(deg);rad=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0));rs=.94 if secondary else 1;ws=.88 if secondary else 1
        existing=[o for o in parts if any(o.name.startswith(n) for n in [f'Crop circle petal {idx}/',f'Orbital node petal {idx}/',f'Petal circle link {idx}/',f'Living energy vein {idx} /'])]
        paths=[np.array([(Vector(p).dot(rad),Vector(p).dot(side)) for p in centers(o)]) for o in existing]
        def surface(r,s):
            t=float(np.interp(r/rs,prs[:,0],ts));_,z,w=prof(t)
            return rad*r+side*s+Vector((0,0,z*(.79 if secondary else 1)+.2))
        outline=[]
        for sign,seq in [(1,np.linspace(.24,6.82,100)),(-1,np.linspace(6.82,.24,100))]:
            for t in seq:r,z,w=prof(t);outline.append((r*rs,sign*w*ws*.88))
        outline.append(outline[0]);ribbon(f'Artist petal perimeter {idx}',[surface(*p) for p in outline],receiver,width=.006)
        hatches=[];min_clearance=10
        for r in np.arange(.34,1.83,.095)*rs:
            t=float(np.interp(r/rs,prs[:,0],ts));w=prof(t)[2]*ws*.86;gap=.035
            ys=[]
            for path in paths:
                for p,q in zip(path[:-1],path[1:]):
                    lo,hi=sorted([p[0],q[0]])
                    if lo-gap<=r<=hi+gap:
                        u=max(0,min(1,(r-p[0])/(q[0]-p[0]))) if abs(q[0]-p[0])>1e-8 else .5
                        ys.append(abs(p[1]+u*(q[1]-p[1])))
            stop=max(ys)+gap if ys else 0
            spans=[(-w,-stop),(stop,w)] if ys else [(-w,w)]
            for y0,y1 in spans:
                if y1-y0<.035:continue
                xy=[(float(r),float(y)) for y in np.linspace(y0,y1,max(3,int((y1-y0)/.018)))]
                ribbon(f'Artist petal hatch {idx}/{len(hatches)}',[surface(*p) for p in xy],receiver,width=.0045);hatches.append(xy)
        report['petals'].append({'index':idx,'hatch_segments':len(hatches),'keepout_gap':.035})
        if idx in [1,4]:report['designs'].append({'type':'petal','secondary':secondary,'perimeter':outline,'hatches':hatches,'existing':[[list(p) for p in q] for q in paths]})
    # Remove the old exterior motifs, retaining ring and crown ornamentation.
    for ob in list(parts):
        if ob.name.startswith(('Hull nested orbital seal','Hull satellite','Team long hull circuit')):remove(ob)
    for bone in ['GondolaL','GondolaR']:
        sign=-1 if bone=='GondolaL' else 1
        hull=next(o for o in parts if o.get('main_gondola') and o['rig_bone']==bone)
        ring=next(o for o in parts if o.get('through_ring') and o['rig_bone']==bone)
        cx,cy,cz=ring['axis_center']
        # Recess ONLY the hull under the existing ornamental ring face. The
        # functional .385 luminous bore and the ring itself remain untouched.
        bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.55,depth=4,location=(cx,cy,cz),rotation=(0,math.pi/2,0));cutter=bpy.context.object
        for m in hull.data.materials:cutter.data.materials.append(m)
        for p in cutter.data.polygons:p.material_index=1
        bpy.context.view_layer.objects.active=hull;mod=hull.modifiers.new('Expose complete ring engraving','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
        # Trim old panels/lips beneath the ring too; preserve all ring parts.
        for ob in [o for o in list(parts) if o['rig_bone']==bone and o.name.startswith('Gondola ')]:
            bm=bmesh.new();bm.from_mesh(ob.data);erase=[f for f in bm.faces if any((v.co.y-cy)**2+(v.co.z-cz)**2<.548**2 for v in f.verts)]
            bmesh.ops.delete(bm,geom=erase,context='FACES');loose=[v for v in bm.verts if not v.link_faces]
            if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
            bm.to_mesh(ob.data);bm.free();ob.data.update()
            if not ob.data.polygons:remove(ob)
        composite_objects=[o for o in parts if o['rig_bone']==bone and (o.get('main_gondola') or o.name.startswith('Gondola '))]
        cv=[];cf=[]
        for obj in composite_objects:
            offset=len(cv);cv.extend(v.co.copy() for v in obj.data.vertices);cf.extend([[i+offset for i in f.vertices] for f in obj.data.polygons])
        composite=BVHTree.FromPolygons(cv,cf)
        def project(p,bv,outside=True):
            start=Vector((sign*3 if outside else -sign*3,p.y,p.z));direction=Vector((-sign if outside else sign,0,0))
            hit,n,ix,dist=(composite if outside else bv).ray_cast(start,direction)
            if n is not None and n.dot(direction)>0:n=-n
            assert hit is not None,('Missing gondola surface',bone,tuple(p),outside)
            return hit,n,ix,dist
        outside_paths=[];inside_paths=[]
        for direction in [-1,1]:
            tip=cy+direction*1.382;neck=cy+direction*.52
            def width(y):t=max(0,min(1,(y+1.56)/2.8));return (.003+.345*math.sin(math.pi*t)**.72)*.86*min(1,abs(y-tip)/.08)**.5
            ztop=width(neck);r=(.52**2+ztop**2)**.5;angle=math.atan2(ztop,.52)
            outline=[(float(y),cz+width(y)) for y in np.linspace(tip,neck,50)]
            outline += [(cy+direction*r*math.cos(a),cz+r*math.sin(a)) for a in np.linspace(angle,-angle,30)]
            outline += [(float(y),cz-width(y)) for y in np.linspace(neck,tip,50)];outline.append(outline[0])
            outside_paths.append(outline);inside_paths.append(outline)
            big=cy+direction*.88;node=cy+direction*.70
            for yy,zz,rr in [(big,cz,.080),(node,cz+.16,.035),(node,cz-.16,.035)]:
                outside_paths.append([(yy+rr*math.cos(a),zz+rr*math.sin(a)) for a in np.linspace(0,2*math.pi,65)])
            for dz in [-1,1]:outside_paths.append([(big-direction*.035,cz+dz*.072),(node+direction*.02,cz+dz*.13)])
            outside_paths.append([(node,cz-.125),(node,cz+.125)])
            for near,far,zz in [(1.25,1.01,.105),(1.16,1.02,.052)]:outside_paths.append([(cy+direction*far,cz-zz),(cy+direction*near,cz),(cy+direction*far,cz+zz)])
        for i,path in enumerate(outside_paths):ribbon(f'Artist gondola exterior {bone}/{i}',[(sign*2,y,z) for y,z in path],hull,width=.006,projector=lambda p,bv:project(p,bv,True))
        for i,path in enumerate(inside_paths):ribbon(f'Artist gondola inner luminous contour {bone}/{i}',[(-sign*2,y,z) for y,z in path],hull,5,.006,projector=lambda p,bv:project(p,bv,False))
        # Visibility check: sample the ring's retained face inscriptions from the
        # outside. Hull/panels must not sit in front of their source coordinates.
        obstacles=[o for o in parts if o['rig_bone']==bone and (o.get('main_gondola') or o.name.startswith('Gondola '))];obstacles=[tree(o) for o in obstacles if o.data.polygons]
        tested=0
        for ob in [o for o in parts if o['rig_bone']==bone and o.name.startswith(('Ring orbital seal','Ring paired orbit'))]:
            for v in list(ob.data.vertices)[::8]:
                p=v.co;start=Vector((sign*3,p.y,p.z));direction=Vector((-sign,0,0));target=abs(start.x-p.x)
                for bv in obstacles:
                    hit,n,ix,dist=bv.ray_cast(start,direction,target-.001)
                    assert hit is None,('Ring engraving occluded',bone,ob.name,tuple(p))
                tested+=1
        report['gondolas'].append({'bone':bone,'exterior_paths':len(outside_paths),'inner_contours':len(inside_paths),'visible_ring_samples':tested})
        if sign<0:report['designs'].append({'type':'gondola','center':[cy,cz],'outside':outside_paths,'inside':inside_paths})
    return report
