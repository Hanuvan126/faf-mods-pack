from pathlib import Path
import math, struct, json
import numpy as np
from PIL import Image, ImageDraw
from geometry import Mesh, load_scm, load_dds_mip
from primitives import plate, ellipsoid, ring, tube
from supcom_binary import write_scm, save_dds_dxt5

SRC=Path(__file__).resolve().parent
MOD=SRC.parents[1]

def build(kind, detail):
    m=Mesh(detail)
    if kind=='NEA0401':
        # Broad, low, rounded hover tank with a circular production cradle.
        plate(m,[(0,31),(-11,24),(-20,8),(-20,-18),(-13,-28),(13,-28),(20,-18),(20,8),(11,24)],(0,0),7,4)
        for s in (-1,1):
            plate(m,[(s*10,22),(s*20,13),(s*23,-12),(s*17,-23),(s*12,-14)],(s*16,0),8,3,trim=False)
            ellipsoid(m,(s*17,3,-3),(3,2,18),0,'dark')
            tube(m,[(s*13,8.2,-17),(s*18,8.2,-4),(s*16,8.2,10),(s*8,8.2,23)],.25,0,'team',8)
        ellipsoid(m,(0,8,-3),(10,2.2,13),0,'steel')
        for r in (5.7,7.0): ring(m,0,10.2,-3,r,0,'edge',.35)
        ring(m,0,10.3,-3,4.4,0,'team',.22)
        ellipsoid(m,(0,10.5,-3),(3.1,1.2,3.1),0,'lens')
        for s in (-1,1): ellipsoid(m,(s*8,7,22),(2,.8,3),0,'lens')
    else:
        # A luminous core and raised, irregular arcs conforming to the sphere.
        ellipsoid(m,(0,0,0),(6,6,6),0,'crystal')
        for i in range(6 if detail >= 16 else 4):
            longitude = i * 2 * math.pi / (6 if detail >= 16 else 4)
            points=[]
            for j in range(9):
                lat = -.95 + j * 1.9 / 8
                lon = longitude + (.16 if j % 2 else -.16)
                r = 6.07
                points.append((r*math.cos(lat)*math.cos(lon), r*math.sin(lat), r*math.cos(lat)*math.sin(lon)))
            tube(m,points,.12,0,'lens',6)
        for z in (-2.8,2.8):
            r=math.sqrt(6.08**2-z*z)
            points=[(r*math.cos(a),r*math.sin(a),z) for a in np.linspace(0,2*math.pi,detail+1)]
            tube(m,points,.08,0,'team',6)
    m.smooth()
    return m

def textures(unit, name):
    # Aeon shader: specular alpha is team mask; normals use G/A.
    palettes=[(190,194,178),(55,64,58),(220,220,201),(154,165,148),(135,158,135),(115,183,155),(95,205,174),(48,59,51)]
    a=np.zeros((256,512,4),dtype=np.uint8); s=np.zeros_like(a); n=np.full_like(a,128)
    for i,c in enumerate(palettes):
        y=(i//4)*128;x=(i%4)*128
        a[y:y+128,x:x+128,:3]=c; a[y:y+128,x:x+128,3]=255
        s[y:y+128,x:x+128,:]=[110,110,0,0]
        if i in (4,5,6): s[y:y+128,x:x+128,:]=[105,100,40 if i!=6 else 100,255]
    if name == 'NEA0001':
        # Blue-white self-lit Aeon material; alpha remains the team mask.
        for i in range(8):
            y=(i//4)*128; x=(i%4)*128
            a[y:y+128,x:x+128,:3] = (105,165,215) if i == 5 else (195,226,250)
            s[y:y+128,x:x+128,:] = [100,115,150,0]
            if i == 4: s[y:y+128,x:x+128,:] = [100,115,100,170]
            if i == 6: s[y:y+128,x:x+128,:] = [100,100,230,0]
    for suffix,data in [('albedo',a),('specteam',s),('normalsTS',n)]:
        im=Image.fromarray(data);im.save(SRC/f'{name}_{suffix}_source.png')
        save_dds_dxt5(im,unit/f'{name}_{suffix}.dds',independent_channels=True)

def export_obj(mesh, name):
    lines = [f"# {name}, Y up; game scale {0.075 if name == 'NEA0001' else 0.1}", f'mtllib {name}_source.mtl']
    for v in mesh.vertices: lines.append('v %.6f %.6f %.6f' % v[:3])
    for v in mesh.vertices: lines.append('vt %.7f %.7f' % (v[12], 1-v[13]))
    for v in mesh.vertices: lines.append('vn %.6f %.6f %.6f' % v[3:6])
    lines += [f'g {name}', 'usemtl aeon_atlas']
    for i in range(0,len(mesh.indices),3):
        lines.append('f ' + ' '.join(f'{j+1}/{j+1}/{j+1}' for j in mesh.indices[i:i+3]))
    (SRC/f'{name}_source.obj').write_text('\n'.join(lines)+'\n')
    (SRC/f'{name}_source.mtl').write_text(f'newmtl aeon_atlas\nKd 1 1 1\nmap_Kd {name}_albedo_source.png\n')

def main():
    report={}
    for name in ('NEA0401','NEA0001'):
        unit=MOD/'units'/name; textures(unit,name); report[name]=[]
        for lod,detail in enumerate((16,8)):
            m=build(name,detail)
            if lod == 0: export_obj(m, name)
            target=unit/f'{name}_lod{lod}.scm'
            write_scm(m,target,[name],[-1],[(0,0,0)])
            v,f=load_scm(target)
            assert len(v)<65536 and f.max()<len(v) and np.isfinite(v).all()
            report[name].append({'vertices':len(v),'triangles':len(f)})
        for suffix in ('albedo','specteam','normalsTS'):
            for mip in (0,1,4):
                ar=np.asarray(load_dds_mip(unit/f'{name}_{suffix}.dds',mip))
                assert ar[:,:,:3].max()>0
    (SRC/'export_checks.json').write_text(json.dumps(report,indent=2))
    print(report,flush=True)
    # Adapt the established SCM/DDS renderer's texture naming and team channel.
    import geometry
    original=geometry.load_dds_mip
    for name in ('NEA0401','NEA0001'):
        def loader(path,level=0, name=name):
            path=Path(str(path).replace('NEA0401_',name+'_'))
            image=original(path,level)
            if 'albedo' in path.name:
                a=np.asarray(image).copy(); mask=np.asarray(original(path.with_name(path.name.replace('albedo','specteam')),level))[:,:,3]; a[:,:,3]=mask; return Image.fromarray(a)
            return image
        geometry.load_dds_mip=loader
        views=[]
        for label,az,el in [('perspective',35,40),('top',180,88),('front',0,12),('side',90,12)]:
            p=SRC/f'{name}_{label}.png'
            geometry.render_scm(MOD/'units'/name/f'{name}_lod0.scm',SRC,p,azimuth=az,elevation=el,size=480,texture_mip=1)
            views.append(Image.open(p))
        sheet=Image.new('RGB',(960,960))
        for i,img in enumerate(views):sheet.paste(img,((i%2)*480,(i//2)*480))
        sheet.save(SRC/f'{name}_views.png')
        if name=='NEA0401':
            im=geometry.render_scm(MOD/'units'/name/f'{name}_lod0.scm',SRC,SRC/f'{name}_icon.png',azimuth=35,elevation=43,size=128,texture_mip=0,transparent=True).resize((64,64),Image.Resampling.LANCZOS)
            for folder in ('icons/units','textures/ui/common/icons/units'): save_dds_dxt5(im,MOD/folder/f'{name}_icon.dds')
    geometry.load_dds_mip=original

if __name__=='__main__': main()
