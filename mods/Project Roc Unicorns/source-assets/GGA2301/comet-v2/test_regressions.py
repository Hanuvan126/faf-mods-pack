from pathlib import Path
import sys,struct,json,zipfile
import numpy as np
from PIL import Image
sys.path.insert(0,'F:/FAF-Development/work/pythonlibs')
from lupa import LuaRuntime
p=Path('F:/FAF-Development/work/faf-upload/mods/Project Roc Unicorns/source-assets/GGA2301/comet-v2');stage=p/'runtime'
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('UnitBlueprint=function(t) BP=t end; Sound=function(t)return t end; EmitterBlueprint=function(t) FX=t end')
lua.execute((stage/'units/GGA2301/GGA2301_unit.bp').read_text());bp=lua.globals().BP
assert bp.Weapon[1].MaxRadius==80 and abs(1/bp.Weapon[1].RateOfFire-.6)<1e-9
assert bp.Weapon[1].MuzzleVelocity==45
assert bp.Display.Mesh.LODs[1].LODCutoff==120 and bp.Display.Mesh.LODs[2].LODCutoff==215
assert bp.Wreckage.UseCustomMesh

# Execute the actual FAF effect function that threw the exception in game_28081241.log.
source=None
for f in Path('C:/ProgramData/FAForever/gamedata').glob('*.nx2'):
    with zipfile.ZipFile(f) as z:
        for name in z.namelist():
            if name.lower()=='lua/defaultexplosions.lua':source=z.read(name).decode()
assert source
effect=source[source.index('function CreateWreckageEffects(unit, prop)'):].split('\nend',1)[0]+'\nend'
unit_h=struct.unpack_from('<4s11I',(stage/'units/GGA2301/GGA2301_lod0.scm').read_bytes())
wreck_h=struct.unpack_from('<4s11I',(stage/'units/GGA2301/GGA2301_wreck.scm').read_bytes())
assert unit_h[3]==wreck_h[3]==6
lua.globals().wreckBones=wreck_h[3]
lua.execute('''MathFloor=math.floor; DefaultWreckageEffectsCount=1; DefaultWreckageEffects={'test'}
IEffectScaleEmitter=function()end;IEffectSetEmitterParam=function()end;ApplyWindDirection=function()end
unit={Blueprint=BP, Army=1,GetBoneCount=function()return 6 end}
prop={Trash={Add=function()end}}
CreateEmitterAtBone=function(p,b) assert(b>=0 and b<wreckBones,'invalid wreck bone');return {} end
''')
lua.execute(effect)
for i in range(1,6):
    lua.globals().chosen=i
    lua.execute('Random=function(a,b) if not a then return .5 end; if b==1 then return 1 end;return chosen end;CreateWreckageEffects(unit,prop)')
# The old one-bone wreck must fail this same path, proving the regression reproducer.
lua.execute('wreckBones=1;chosen=5')
try:lua.execute('CreateWreckageEffects(unit,prop)')
except Exception as e:assert 'invalid wreck bone' in str(e)
else:raise AssertionError('Regression reproducer did not fail for old wreck')
lua.execute('wreckBones=6')

lua.execute('ModBlueprints=function(t)t.baseHookCalled=true end')
lua.execute((stage/'hook/lua/system/Blueprints.lua').read_text())
lua.execute('b={Unit={gga2401={},xsb1104={},gga2301={},gga2404={},gga0401={}}};ModBlueprints(b);assert(b.baseHookCalled and b.Unit.gga2401==nil and b.Unit.gga2301 and b.Unit.gga2404 and b.Unit.gga0401)')
lua.execute((stage/'effects/emitters/ishal_comet_smoke_emit.bp').read_text());fx=lua.globals().FX
assert fx.LocalVelocity==False and fx.LocalAcceleration==False
assert fx.VelocityCurve.Keys[1].y==0
assert all(fx[k+'AccelCurve'].Keys[1].y==0 for k in 'XYZ')
assert fx.LifetimeCurve.Keys[1].y==.32 and fx.EmitRateCurve.Keys[1].y==150

# Check sampled fill decisions, symmetry, and material channel semantics from the final DDS.
tex=np.array(Image.open(stage/'units/GGA2301/GGA2301_albedo.dds').convert('RGBA'))
def at(u,v):return tex[int(v*1024),int(u*1024),3]
def roof(x,y):return at(.02+.46*(x+2.5)/5,.15+.8*(y+2.5)/5)
def support(u,z):return at(.52+.46*(u+1.5)/3,.15+.8*z/2.5)
assert roof(.5,0)>240 and roof(0,.34)<10 and roof(0,-.39)<10
assert support(0,1.12)>240 and support(.4,1.12)<10
assert support(.3,1.8)>240 and support(.1,1.8)<10 and support(.55,1.8)<10 and support(.8,1.8)>240
for x in [.1,.3,.5,.8]:assert abs(int(support(x,1.8))-int(support(-x,1.8)))<10
proj=(stage/'projectiles/GGP2301/GGP2301_lod0.scm').read_bytes();h=struct.unpack_from('<4s11I',proj)
radius=max(np.linalg.norm(struct.unpack_from('<3f',proj,h[4]+i*68)) for i in range(h[6]))
assert abs(radius-.11)<1e-5

report={'status':'passed','checks':['regression reproduces old wreck bone failure; corrected wreck passes every reachable bone','disabled artillery blueprint removed; unrelated units preserved','inline mesh LODs available for tarmac and build effects','80 range / 0.6 s / 45 velocity / 0.22 projectile diameter','zero world smoke velocity and acceleration / 0.32 s fade','symmetric fill masks and unfilled circular cutouts'],'game_match_tested':False}
(p/'regression_checks.json').write_text(json.dumps(report,indent=2));print('REGRESSION_CHECKS_PASSED')
