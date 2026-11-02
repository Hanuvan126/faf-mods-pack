"""2026-11-02 hand-drawn references translated into fitted geometric inlays."""
import math,json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
def apply_lower_petals(parts,mesh):
    report={'petals':[],'gondolas':[],'designs':[]}
    def tree(ob):return BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])
    def remove(ob):parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    # Support repeatable runs without duplicating newly authored strokes.
    for ob in list(parts):
        if ob.get('lower_petal_v10'):remove(ob)
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
    for idx,deg in [(4,-90),(5,30),(6,150)]:
        receiver=next(o for o in parts if o.get('foundation_petal') and o.name.endswith('petal '+str(idx)))
        assert receiver.get('secondary_petal')
        for ob in list(parts):
            if ob.name.startswith((f'Crop circle petal {idx}/',f'Orbital node petal {idx}/',f'Petal circle link {idx}/',f'Living energy vein {idx} /',f'Artist petal hatch {idx}/',f'Artist petal perimeter {idx}')):remove(ob)
        a=math.radians(deg);rad=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0))
        def xy(u,v):
            r=(1.94-1.72*u)*.94;t=float(np.interp(r/.94,prs[:,0],ts));_,z,w=prof(t)
            return rad*r+side*(v*.88)+Vector((0,0,z*.79+.2))
        paths=[]
        # u=0 pointed end; u=1 root. Outline follows unchanged petal skin.
        outline=[]
        for sign,seq in [(1,np.linspace(6.82,.24,130)),(-1,np.linspace(.24,6.82,130))]:
            for t in seq:r,z,w=prof(t);outline.append(((1.94-r)/1.72,sign*w*.88))
        outline.append(outline[0]);paths.append(outline)
        paths.append([(.065,0),(.96,0)])
        for sign in [-1,1]:
            # Matching circles and broken outer arcs, mirrored along petal axis.
            paths.append([(.55+.078*math.cos(t),sign*.238+.105*math.sin(t)) for t in np.linspace(0,2*math.pi,97)])
            for start,end in [(25,155),(205,335)]:
                paths.append([(.55+.117*math.cos(t),sign*.238+.151*math.sin(t)) for t in np.linspace(math.radians(start),math.radians(end),60)])
            for u,v,l in [(.71,.08,.22),(.69,.16,.17),(.65,.235,.10),(.24,.14,.17)]:paths.append([(u,sign*v),(u+l,sign*v)])
            for i in range(4):
                u=.15+i*.047;paths.append([(u,sign*.065),(u+.078,sign*.14)])
            for i in range(3):
                u=.255+i*.038;paths.append([(u,sign*.23),(u+.055,sign*.285)])
        for n,path in enumerate(paths):
            ob=ribbon(f'Lower petal new pattern {idx}/{n}',[xy(*p) for p in path],receiver,width=.005)
            ob['lower_petal_v10']=True
        report['petals'].append({'index':idx,'paths':len(paths)})
        if idx==4:report['designs']=paths
    return report
