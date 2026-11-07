from pathlib import Path
import math
import numpy as np
from PIL import Image
from model_tools import Mesh, export_obj, make_previews
from supcom_binary import write_scm, save_dds_dxt5

HERE=Path(__file__).resolve().parent
UNIT=HERE.parents[1]/'units'/'NSB2201'
NAMES=['NSB2201','Turret','Turret_Barrel','Turret_Muzzle']
PARENTS=[-1,0,1,2]
PIVOTS=[(0,0,0),(0,82,0),(0,0,0),(0,0,9.5)]

def build(detail):
    m=Mesh(detail)
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
    colors=[(173,180,157),(46,59,52),(205,205,171),(120,143,121),(112,164,137),(104,240,205),(166,250,218),(38,57,48)]
    for i,c in enumerate(colors):
        y=(i//4)*256; x=(i%4)*128
        a[y:y+256,x:x+128,:3]=c; a[y:y+256,x:x+128,3]=255
        s[y:y+256,x:x+128]=[110,105,0,0]
        if i==4: s[y:y+256,x:x+128]=[110,100,45,180]
        if i==5: s[y:y+256,x:x+128]=[95,75,185,0]
        if i==6: s[y:y+256,x:x+128]=[100,85,140,0]
    for suffix,data in [('albedo',a),('specteam',s),('normalsTS',n)]:
        im=Image.fromarray(data); im.save(HERE/f'NSB2201_{suffix}_source.png')
        save_dds_dxt5(im,UNIT/f'NSB2201_{suffix}.dds',independent_channels=True)

if __name__=='__main__':
    for lod,detail in [(0,32),(1,12)]:
        m=build(detail); write_scm(m,UNIT/f'NSB2201_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
        if lod==0: export_obj(m,HERE)
        print('LOD',lod,'vertices',len(m.vertices),'triangles',len(m.indices)//3)
    textures(); make_previews(UNIT,HERE)
