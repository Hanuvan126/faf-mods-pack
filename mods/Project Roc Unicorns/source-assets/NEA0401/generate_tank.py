"""Rebuild only Halo Nest; never overwrite Halo Drone assets."""
from pathlib import Path
import json,struct
import numpy as np
from PIL import Image
import geometry
import generate_swarm as g
from supcom_binary import write_scm,save_dds_dxt5

name='NEA0401';src=Path(__file__).resolve().parent;unit=g.MOD/'units'/name

def main():
    g.textures(unit,name)
    report=[]
    for lod,detail in enumerate((24,12)):
        mesh=g.build(name,detail)
        if lod==0:g.export_obj(mesh,name)
        target=unit/f'{name}_lod{lod}.scm'
        write_scm(mesh,target,[name,'Crystal'],[-1,0],[(0,0,0),(0,17,-1)])
        vertices,faces=geometry.load_scm(target)
        raw=target.read_bytes();h=struct.unpack_from('<4s11I',raw)
        assert h[:2]==(b'MODL',5) and h[3]==2 and len(vertices)<65536 and faces.max()<len(vertices)
        assert np.isfinite(vertices).all()
        assert np.allclose(np.linalg.norm(vertices[:,3:6],axis=1),1,atol=1e-5)
        area=np.linalg.norm(np.cross(vertices[faces[:,1],:3]-vertices[faces[:,0],:3],vertices[faces[:,2],:3]-vertices[faces[:,0],:3]),axis=1)
        assert area.min()>1e-8
        names=[]
        for i in range(h[3]):
            bone=struct.unpack_from('<16f3f4f4i',raw,h[2]+i*108)
            names.append(raw[bone[23]:].split(b'\0')[0].decode())
            assert bone[24] == [-1,0][i]
            assert np.allclose(bone[16:19],[(0,0,0),(0,17,-1)][i])
        assert names == ['NEA0401','Crystal']
        report.append({'lod':lod,'vertices':len(vertices),'triangles':len(faces),'bones':names,
                       'bounds_game':(np.array([vertices[:,:3].min(0),vertices[:,:3].max(0)])*.1).round(3).tolist()})
    for suffix in ('albedo','specteam','normalsTS'):
        for level in (0,1,4,7):
            arr=np.asarray(geometry.load_dds_mip(unit/f'{name}_{suffix}.dds',level))
            assert arr[:,:,:3].max()>0
            if suffix=='normalsTS':
                assert abs(arr[:,:,1].mean()-128)<5 and abs(arr[:,:,3].mean()-128)<5
    (src/'NEA0401_seven_spheres_checks.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)
    original=geometry.load_dds_mip
    def loader(path,level=0):
        im=original(path,level)
        if 'albedo' in Path(path).name:
            data=np.asarray(im).copy()
            spec=original(Path(path).with_name(Path(path).name.replace('albedo','specteam')),level)
            data[:,:,3]=np.asarray(spec)[:,:,3]
            return Image.fromarray(data)
        return im
    geometry.load_dds_mip=loader
    views=[]
    for label,az,el in [('perspective',35,40),('top',180,88),('front',0,12),('side',90,12)]:
        path=src/f'{name}_{label}.png'
        geometry.render_scm(unit/f'{name}_lod0.scm',src,path,azimuth=az,elevation=el,size=600,texture_mip=1)
        views.append(Image.open(path))
    sheet=Image.new('RGB',(1200,1200))
    for i,im in enumerate(views):sheet.paste(im,((i%2)*600,(i//2)*600))
    sheet.save(src/f'{name}_views.png')
    icon=geometry.render_scm(unit/f'{name}_lod0.scm',src,src/f'{name}_icon.png',azimuth=35,elevation=43,size=128,texture_mip=0,transparent=True).resize((64,64),Image.Resampling.LANCZOS)
    for folder in ('icons/units','textures/ui/common/icons/units'):
        save_dds_dxt5(icon,g.MOD/folder/f'{name}_icon.dds')

if __name__=='__main__':main()
