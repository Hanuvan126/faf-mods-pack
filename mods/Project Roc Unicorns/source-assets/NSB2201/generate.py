from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from model_tools import Mesh, export_obj, make_previews
from supcom_binary import write_scm, save_dds_dxt5

HERE=Path(__file__).resolve().parent
UNIT=HERE.parents[1]/'units'/'NSB2201'
NAMES=['NSB2201','Turret','Turret_Barrel','Turret_Muzzle']
PARENTS=[-1,0,1,2]
# SkirtSize 6 spans 3 world units: fit the circular base to that square.
XZ_SCALE=(1.5/.045)/31
TOP=82+9.2*math.sin(7*math.pi/16)
SHOULDER=72
SHAFT_SCALE=(SHOULDER+TOP)/SHOULDER
PIVOTS=[(0,0,0),(0,82+TOP,0),(0,0,0),(0,0,9.5*XZ_SCALE)]

def build(detail):
    m=Mesh(detail)
    # Stretch the shaft, but translate the crown rigidly so the crystal stays round.
    original_face=m.face
    def scaled_face(points, *args, **kwargs):
        def transform(p):
            x,y,z=p
            y=y*SHAFT_SCALE if y<SHOULDER else y+TOP
            return (x*XZ_SCALE,y,z*XZ_SCALE)
        return original_face([transform(p) for p in points], *args, **kwargs)
    m.face=scaled_face
    m.column([(29,.2),(31,1),(31,2.2),(29,3.4),(24,4.6),(18,5.3)],material='dark')
    m.annulus(25,30,2.5,3.1,material='edge')
    m.annulus(19,24,4.4,5.0,material='team')
    m.column([(18,5),(18,8),(14,11),(11,16),(8,25),(6,40),(5,58),(6,70),(8,74)],material='armor')
    m.annulus(12,17,8,9,material='edge')
    m.annulus(5.4,7.2,66,67,material='team')
    # Four rounded, tapered ribs curve inward, then open around the crystal.
    for i in range(4):
        a=2*math.pi*i/4+math.pi/4
        sections=[(5,23,3.8),(9,21,3.5),(15,17,2.8),(24,13,2.2),(36,10,1.8),(50,8.5,1.6),(64,9,1.7),(74,11,1.6),(82,12,1.2),(89,10,.55)]
        if detail<24: sections=sections[::2]+[sections[-1]]
        m.blade(sections,a,0,'armor',False,1.6)
        trim=[(y,r+1.7,max(.18,w*.13)) for y,r,w in sections[:-1]]
        m.blade(trim,a,0,'team',False,.18)
    # Fixed spherical crystal seated in a collar, not a floating object.
    m.column([(6,72),(9,74),(10,76),(9,78)],material='edge')
    profile=[]
    for j in range(1,16):
        phi=-math.pi/2+math.pi*j/16
        profile.append((9.2*math.cos(phi),82+9.2*math.sin(phi)))
    m.column(profile,material='crystal',sides=detail)
    m.annulus(8.6,9.6,80.8,81.4,material='lens')
    m.smooth()
    return m

def textures():
    a=np.zeros((512,512,4),dtype=np.uint8); s=np.zeros_like(a); n=np.zeros_like(a)
    n[:]=(128,128,128,128)
    # Aeon PBR remaps SpecTeam.R to metalness. Values around 110 make
    # albedo almost white via pow(albedo, 1 - metalness * .95).
    colors=[(69,76,82),(26,30,34),(115,122,129),(73,80,86),(60,68,73),(87,99,108),(125,135,145),(25,30,35)]
    for i,c in enumerate(colors):
        y=(i//4)*256; x=(i%4)*128
        a[y:y+256,x:x+128,:3]=c; a[y:y+256,x:x+128,3]=255
        s[y:y+256,x:x+128]=[58,85,0,0]
        if i==2: s[y:y+256,x:x+128]=[64,75,0,0]
        if i==4: s[y:y+256,x:x+128]=[58,85,20,180]
        if i==5: s[y:y+256,x:x+128]=[60,92,12,0]
        if i==6: s[y:y+256,x:x+128]=[60,85,20,0]
    # The shaft and ribs share this UV tile. Fine longitudinal seams and
    # transverse joints repeat on their existing faces without changing SCM.
    art=Image.fromarray(a)
    draw=ImageDraw.Draw(art)
    for x in (18, 20, 62, 64, 106, 108):
        draw.line((x, 0, x, 255), fill=(38,44,49,255), width=1)
    for y in (48, 49, 126, 127, 204, 205):
        draw.line((0, y, 127, y), fill=(49,55,61,255), width=1)
    a=np.asarray(art)
    for suffix,data in [('albedo',a),('specteam',s),('normalsTS',n)]:
        im=Image.fromarray(data); im.save(HERE/f'NSB2201_{suffix}_source.png')
        save_dds_dxt5(im,UNIT/f'NSB2201_{suffix}.dds',independent_channels=True)

if __name__=='__main__':
    for lod,detail in [(0,32),(1,12)]:
        m=build(detail); write_scm(m,UNIT/f'NSB2201_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
        if lod==0: export_obj(m,HERE)
        print('LOD',lod,'vertices',len(m.vertices),'triangles',len(m.indices)//3)
    textures(); make_previews(UNIT,HERE)
