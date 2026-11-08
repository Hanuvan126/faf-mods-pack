from pathlib import Path
from types import SimpleNamespace
from io import BytesIO
import sys,json,struct,math,shutil
import numpy as np
from PIL import Image

mod=Path('F:/FAF-Development/work/faf-upload/mods/Project Roc Unicorns')
p=mod/'source-assets/GGA2301/comet-v2';stage=p/'runtime';unit=stage/'units/GGA2301'
sys.path.insert(0,str(p.parent))
from supcom_binary import write_scm

inputs=p/'inputs';inputs.mkdir(exist_ok=True)
for rel in ['units/GGA2301/GGA2301_unit.bp','projectiles/GGP2301/GGP2301_lod0.scm','units/GGA0401/GGA0401_approved_albedo.dds','units/GGA0401/GGA0401_approved_specteam.dds']:
    dst=inputs/rel
    if not dst.exists():
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(mod/rel,dst)

def dds(im,path,independent=True):
    path.parent.mkdir(parents=True,exist_ok=True)
    cur=im.convert('RGBA');levels=[]
    while True:
        stream=BytesIO();cur.save(stream,format='DDS',pixel_format='DXT5');levels.append(stream.getvalue()[128:])
        if cur.size==(1,1):break
        size=(max(1,cur.width//2),max(1,cur.height//2))
        if independent:cur=Image.merge('RGBA',[c.resize(size,Image.Resampling.BOX) for c in cur.split()])
        else:cur=cur.resize(size,Image.Resampling.LANCZOS)
    w,h=im.size
    header=[124,0xA1007,h,w,((w+3)//4)*((h+3)//4)*16,0,len(levels)]
    header += [0]*11+[32,4,0x35545844,0,0,0,0,0]+[0x401008,0,0,0,0]
    path.write_bytes(b'DDS '+struct.pack('<31I',*header)+b''.join(levels))

for lod in [0,1]:
    d=json.loads((p/f'lod{lod}.json').read_text())
    write_scm(SimpleNamespace(vertices=d['vertices'],indices=d['indices']),unit/f'GGA2301_lod{lod}.scm',d['names'],d['parents'],d['pivots'])

# Atlas: top palette strip, planar roof at left, one repeated cylindrical support sector at right.
size=1024;yy,xx=np.mgrid[:size,:size];u=(xx+.5)/size;v=(yy+.5)/size
a=np.empty((size,size,4),dtype=np.uint8);a[:]=(44,49,56,0)
sp=np.empty_like(a);sp[:]=(180,165,0,0)
n=np.empty_like(a);n[:]=(128,128,255,128)
colors=[(44,49,56,0),(90,96,105,0),(19,23,28,0),(110,110,110,255),(235,240,255,0)]
specs=[(180,165,0,0),(220,195,0,0),(110,120,0,0),(200,190,28,0),(130,160,255,0)]
for i,(c,s) in enumerate(zip(colors,specs)):
    q=(u>=i/8)&(u<(i+1)/8)&(v<.11);a[q]=c;sp[q]=s
x=(u-.02)/.46*5-2.5;y=(v-.15)/.8*5-2.5
roof=(u>=.02)&(u<=.48)&(v>=.15)&(v<=.95)
mask=roof&(x*x+y*y<.76**2)&(x*x+(y-.34)**2>.38**2)&(x*x+(y+.39)**2>.27**2)
bu=(u-.52)/.46*3-1.5;bz=(v-.15)/.8*2.5
r2=bu*bu+(bz-1.12)**2
support=(u>=.52)&(u<=.98)&(bz>=.40)&(bz<=1.98)&(abs(bu)<1.40)
mask |= support&((r2<.33**2)|((r2>.47**2)&((abs(bu)>.66)|((abs(bu)>.22)&(abs(bu)<.44)))))
a[mask]=colors[3];sp[mask]=specs[3]
for suffix,arr in [('albedo',a),('specteam',sp),('normalsTS',n)]:
    im=Image.fromarray(arr);im.save(p/f'{suffix}_source.png');dds(im,unit/f'GGA2301_{suffix}.dds')
Image.fromarray(a[:,:,3]).save(p/'team_mask.png')

# Native death effects use live-unit bone indices on the wreck. Preserve ALL six bones.
d=json.loads((p/'lod1.json').read_text());vertices=[]
for vtx in d['vertices']:
    w=list(vtx);w[1]=max(.05,w[1]*.37);w[0]+=.12*math.sin(w[2]*2)*w[1]
    w[16]=0;w[12]=w[14]=2.5/8;w[13]=w[15]=.05;vertices.append(w)
write_scm(SimpleNamespace(vertices=vertices,indices=d['indices']),unit/'GGA2301_wreck.scm',d['names'],d['parents'],d['pivots'])

bp=unit/'GGA2301_unit.bp';s=(inputs/'units/GGA2301/GGA2301_unit.bp').read_text()
s=s.replace('MuzzleVelocity = 85','MuzzleVelocity = 45').replace('MaxRadius = 60','MaxRadius = 80').replace('RateOfFire = 10 / 3','RateOfFire = 10 / 6')
mesh=(unit/'GGA2301_mesh.bp').read_text().strip().removeprefix('MeshBlueprint').strip()
# The engine and Lua effects BOTH need the mesh LODs; external MeshBlueprint alone is insufficient.
s=s.replace('    Display = {','    Display = {\n        Mesh = '+mesh+',',1)
bp.write_text(s)

pr=stage/'projectiles/GGP2301';f=pr/'GGP2301_lod0.scm';raw=bytearray((inputs/'projectiles/GGP2301/GGP2301_lod0.scm').read_bytes());h=struct.unpack_from('<4s11I',raw)
for i in range(h[6]):
    off=h[4]+i*68;pos=struct.unpack_from('<3f',raw,off);struct.pack_into('<3f',raw,off,*[c*2 for c in pos])
f.write_bytes(raw)
f=pr/'GGP2301_proj.bp';s=f.read_text().replace('Speed = 85','Speed = 45').replace('Lifetime = 2','Lifetime = 3').replace('= 0.11','= 0.22');f.write_text(s)
f=pr/'GGP2301_script.lua';s=f.read_text().replace('SinglePolyTrailProjectile','EmitterProjectile')
s=s.replace("    PolyTrail = '/mods/Project Roc Unicorns/effects/emitters/ishal_comet_trail_emit.bp',\n    FxTrails = {},", "    -- Emitted smoke has zero world velocity; old particles stay behind and fade.\n    FxTrails = {\n        '/mods/Project Roc Unicorns/effects/emitters/ishal_comet_smoke_emit.bp',\n        '/mods/Project Roc Unicorns/effects/emitters/ishal_comet_glow_emit.bp',\n    },")
f.write_text(s)
effects=stage/'effects/emitters';tex=stage/'textures/particles';tex.mkdir(parents=True,exist_ok=True)

def emitter(name,texture,rate,life,start,end,blend,ramp):
    s="EmitterBlueprint {\n"
    fields={'Lifetime':-1,'Repeattime':1,'TextureFramecount':1,'Blendmode':blend,'LocalVelocity':False,'LocalAcceleration':False,'Gravity':False,'AlignRotation':False,'AlignToBone':False,'Flat':False,'LODCutoff':215,'EmitIfVisible':True,'CatchupEmit':True,'CreateIfVisible':False,'InterpolateEmission':True,'TextureStripcount':1,'SortOrder':0,'Texture':texture,'RampTexture':ramp}
    for k,val in fields.items():
        val=str(val).lower() if isinstance(val,bool) else repr(val)
        s+=f'    {k} = {val},\n'
    curves={'EmitRate':rate,'Lifetime':life,'Velocity':0,'Size':0,'StartSize':start,'EndSize':end,'InitialRotation':0,'RotationRate':0,'FrameRate':0,'TextureSelection':0,'RampSelection':0}
    curves.update({axis+kind:0 for axis in 'XYZ' for kind in ['Direction','Accel','Pos']})
    for k,val in curves.items():s+=f'    {k}Curve = {{ XRange = 1, Keys = {{ {{ x=0, y={val}, z=0 }} }} }},\n'
    (effects/name).write_text(s+'}\n')

# Original procedural soft smoke sprite: asymmetrical cloud density, no hard billboard edges.
sy,sx=np.mgrid[-1:1:128j,-1:1:128j];rr=np.sqrt(sx*sx+sy*sy)
density=(.74+.14*np.sin(13*sx+4*np.sin(5*sy))+.12*np.cos(17*sy-3*sx))
alpha=np.clip(1-rr,0,1)**1.4*density
cloud=np.empty((128,128,4),dtype=np.uint8);cloud[:,:,:3]=255;cloud[:,:,3]=(np.nan_to_num(alpha)*220).astype('uint8')
dds(Image.fromarray(cloud),tex/'ishal_comet_smoke.dds',False)
glow=np.empty_like(cloud);glow[:,:,:3]=255;glow[:,:,3]=(np.exp(-rr*rr*7)*np.clip((1-rr)*4,0,1)*255).astype('uint8')
dds(Image.fromarray(glow),tex/'ishal_comet_glow.dds',False)
for name,rgba0,rgba1 in [('smoke',(185,145,245,160),(95,65,150,0)),('glow',(255,235,255,255),(130,80,255,0))]:
    t=np.linspace(0,1,256)[None,:,None];ar=np.array(rgba0)*(1-t)+np.array(rgba1)*t
    ar=np.repeat(ar,4,axis=0).astype('uint8');dds(Image.fromarray(ar),tex/f'ishal_comet_{name}_ramp.dds',False)
root='/mods/Project Roc Unicorns/textures/particles/'
emitter('ishal_comet_smoke_emit.bp',root+'ishal_comet_smoke.dds',150,.32,.14,.45,0,root+'ishal_comet_smoke_ramp.dds')
emitter('ishal_comet_glow_emit.bp',root+'ishal_comet_glow.dds',100,.035,.22,.12,3,root+'ishal_comet_glow_ramp.dds')

# Dush'Nai: Unit shader expects its team mask in specular alpha. Preserve that mask and energy tiles.
tank=stage/'units/GGA0401';tank.mkdir(parents=True,exist_ok=True)
ta=np.array(Image.open(inputs/'units/GGA0401/GGA0401_approved_albedo.dds').convert('RGBA'))
ts=np.array(Image.open(inputs/'units/GGA0401/GGA0401_approved_specteam.dds').convert('RGBA'))
metal=(ts[:,:,3]<8)&(ts[:,:,2]<25)
before=ta[metal,:3].mean(axis=0)
ta[metal,:3]=np.clip(ta[metal,:3].astype(float)*1.8+5,0,255).astype('uint8')
dds(Image.fromarray(ta),tank/'GGA0401_approved_albedo.dds')
assert np.array_equal(ts,np.array(Image.open(mod/'units/GGA0401/GGA0401_approved_specteam.dds').convert('RGBA')))
(p/'material_report.json').write_text(json.dumps({'tank_metal_before':before.tolist(),'tank_metal_after':ta[metal,:3].mean(axis=0).tolist(),'team_and_energy_preserved':True,'turret_line_width_multiplier':2,'turret_team_specular':[200,190,28,0]},indent=2))
print('BUILT',p,flush=True)
