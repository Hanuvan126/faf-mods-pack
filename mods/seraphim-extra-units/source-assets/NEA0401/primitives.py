import math
import numpy as np
from geometry import normalized

def curve(points, subdivisions, closed=False):
    p = np.asarray(points,float)
    result = []
    for i in range(len(p) if closed else len(p)-1):
        a = p[(i-1)%len(p)] if closed else p[max(0,i-1)]
        b, c = p[i], p[(i+1)%len(p)]
        d = p[(i+2)%len(p)] if closed else p[min(len(p)-1,i+2)]
        for t in np.linspace(0,1,subdivisions,endpoint=False):
            result.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    if not closed: result.append(p[-1])
    return np.asarray(result)


def tube(m, points, radius, bone=0, material='team', sides=6):
    points = np.asarray(points,float)
    rings = []
    for i,p in enumerate(points):
        axis = normalized(points[min(i+1,len(points)-1)]-points[max(i-1,0)])
        u = normalized(np.cross(axis,(0,1,0) if abs(axis[1])<.95 else (1,0,0)))
        v = np.cross(axis,u)
        rings.append([p+radius*(math.cos(a)*u+math.sin(a)*v)
                      for a in np.linspace(0,2*math.pi,sides,endpoint=False)])
    m.loft(rings,points,bone,material)


def ring(m, x, y, z, radius, bone=0, material='team', width=.075, vertical=False):
    points = [(x+radius*math.cos(a), y+radius*math.sin(a) if vertical else y,
               z if vertical else z+radius*math.sin(a))
              for a in np.linspace(0,2*math.pi,m.detail+1)]
    tube(m,points,width,bone,material)


def ellipsoid(m, center, radii, bone=0, material='steel'):
    x,y,z = center
    rx,ry,rz = radii
    rings=[]; centers=[]
    for t in np.linspace(-.999,.999,9 if m.detail>=20 else 6):
        r=math.sqrt(1-t*t)
        rings.append([(x+rx*r*math.cos(a), y+ry*r*math.sin(a), z+rz*t)
                      for a in np.linspace(0,2*math.pi,m.detail,endpoint=False)])
        centers.append((x,y,z+rz*t))
    m.loft(rings,centers,bone,material)


def plate(m, outline, center, top, thickness, bone=0, trim=True):
    """Closed cambered shell with a rolled edge, not an extruded flat polygon."""
    contour=curve(outline,5 if m.detail>=20 else 3,True)
    center=np.asarray(center,float)
    mid=top-thickness/2
    profile=[(.035,top),(.38,top-.015),(.74,top-.12),(.89,top-.30),
             (.97,mid+.24),(1,mid+.04),(.995,mid-.20),(.94,top-thickness+.12),
             (.72,top-thickness),(.035,top-thickness)]
    rings=[]
    for scale,y in profile:
        points=center+(contour-center)*scale
        rings.append([(x,y,z) for x,z in points])
    for k in range(len(rings)-1):
        for j in range(len(contour)):
            jj=(j+1)%len(contour)
            points=[rings[k][j],rings[k][jj],rings[k+1][jj],rings[k+1][j]]
            mean=np.mean(points,axis=0)
            outward=(0,1,0) if k<4 else ((0,-1,0) if k>=7 else (mean[0]-center[0],0,mean[2]-center[1]))
            material='armor' if k<3 else ('edge' if k<6 else 'dark')
            m.face(points,bone,material,outward,
                   [((p[0]-center[0])/35+.5,(p[2]-center[1])/65+.5) for p in points])
    for index,normal in ((0,(0,1,0)),(-1,(0,-1,0))):
        for j in range(len(contour)):
            m.face([(center[0],profile[index][1],center[1]),rings[index][j],rings[index][(j+1)%len(contour)]],
                   bone,'armor' if index==0 else 'dark',normal)
    if trim:
        points=center+(contour-center)*.87
        tube(m,[(x,top-.23,z) for x,z in np.vstack((points,points[:1]))],.065,bone,'team')

