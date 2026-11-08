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
        # Forward is +Z. Seven separate pods: one at the nose and three
        # matched pairs along the central gondola, as in the supplied sketch.
        plate(m,[(0,25),(-5,22),(-7,13),(-7,-16),(-5,-23),(0,-26),
                 (5,-23),(7,-16),(7,13),(5,22)],(0,0),12.8,7,trim=False)
        plate(m,[(0,21),(-4,17),(-5,9),(-5,-14),(0,-21),
                 (5,-14),(5,9),(4,17)],(0,0),14.1,2.5,trim=False)
        # Narrow fairings join each sphere to the gondola without obscuring it.
        for side in (-1,1):
            for z in (14,0,-14):
                ellipsoid(m,(side*7.2,5.3,z),(3.5,2,2.2),0,'dark')
        ellipsoid(m,(0,5.3,22),(2.3,2,5),0,'dark')
        pods=[(0,27)] + [(side*12.8,z) for side in (-1,1) for z in (14,0,-14)]
        for x,z in pods:
            # Rounded, slightly flattened hovering spheres with a dark lower
            # hemisphere and a thin colored equatorial strip.
            ellipsoid(m,(x,5.5,z),(6.1,5.2,6.1),0,'dark')
            ellipsoid(m,(x,6.2,z),(5.9,4.7,5.9),0,'armor')
            ring(m,x,6.5,z,5.90,0,'team',.12)
            ring(m,x,9.9,z,3.55,0,'edge',.09)
            ellipsoid(m,(x,10.55,z),(1.15,.35,1.15),0,'lens')
        # Raised crystalline core is a faceted solid, with its own effect bone.
        ring(m,0,14.15,-1,4.5,0,'edge',.24)
        ring(m,0,14.23,-1,3.4,0,'team',.13)
        sides=8 if detail >= 20 else 6
        equator=[(3.3*math.cos(a),17.0,-1+3.3*math.sin(a))
                 for a in np.linspace(0,2*math.pi,sides,endpoint=False)]
        top=(0,23.0,-1); bottom=(0,14.4,-1)
        for i in range(sides):
            a=equator[i]; b=equator[(i+1)%sides]
            outward=(a[0]+b[0],1,a[2]+b[2]+2)
            m.face([top,a,b],1,'crystal',outward)
            m.face([bottom,b,a],1,'lens',(outward[0],-1,outward[2]))
        for side in (-1,1):
            tube(m,[(side*.25,14.3,18),(side*2,14.3,12),
                    (side*2.8,14.3,5),(side*3.4,14.3,-2)],.08,0,'team',6)
        # Real zigzag filaments on the surface augment the live spark emitter.
        for i in range(4):
            a=i*math.pi/2+.3
            points=[]
            for j in range(5):
                y=15+j*1.7
                rr=3.35*(1-abs(y-17)/6.2)
                aa=a+(.12 if j%2 else -.12)
                points.append((rr*math.cos(aa),y,-1+rr*math.sin(aa)))
            tube(m,points,.08,1,'lens',6)
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
    if kind == 'NEA0401':
        # Keep the authored normals/UV seams while sharing identical vertices.
        lookup, vertices, indices = {}, [], []
        for index in m.indices:
            vertex = m.vertices[index]
            key = tuple(round(float(value), 6) for value in vertex)
            if key not in lookup:
                lookup[key] = len(vertices)
                vertices.append(vertex)
            indices.append(lookup[key])
        m.vertices, m.indices = vertices, indices
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
    if name == 'NEA0401':
        # Aeon uses SpecTeam.B for emission, A for the player-color mask.
        s[128:256,128:256,2] = 200
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
    lines.append('usemtl aeon_atlas')
    last = None
    for i in range(0,len(mesh.indices),3):
        bone = int(mesh.vertices[mesh.indices[i]][16])
        if bone != last:
            lines.append('g ' + ('Crystal' if bone == 1 else name))
            last = bone
        lines.append('f ' + ' '.join(f'{j+1}/{j+1}/{j+1}' for j in mesh.indices[i:i+3]))
    (SRC/f'{name}_source.obj').write_text('\n'.join(lines)+'\n')
    (SRC/f'{name}_source.mtl').write_text(f'newmtl aeon_atlas\nKd 1 1 1\nmap_Kd {name}_albedo_source.png\n')

def main():
    report={}
    for name in ('NEA0401','NEA0001'):
        unit=MOD/'units'/name; textures(unit,name); report[name]=[]
        for lod,detail in enumerate((24,12)):
            m=build(name,detail)
            if lod == 0: export_obj(m, name)
            target=unit/f'{name}_lod{lod}.scm'
            write_scm(m,target,[name, 'Crystal'] if name == 'NEA0401' else [name],
                      [-1, 0] if name == 'NEA0401' else [-1],
                      [(0,0,0), (0,17,-1)] if name == 'NEA0401' else [(0,0,0)])
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
