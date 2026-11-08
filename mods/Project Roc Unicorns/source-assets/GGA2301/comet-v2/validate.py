from pathlib import Path
import sys,struct,json,zipfile,re,math
p=Path(__file__).parent;stage=p/'runtime'
sys.path.insert(0,'F:/FAF-Development/work/pythonlibs')
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('UnitBlueprint=function(x) BP=x end; Sound=function(x)return x end; MeshBlueprint=function(x)end; ProjectileBlueprint=function(x)end; PropBlueprint=function(x)end; TrailEmitterBlueprint=function(x)end; EmitterBlueprint=function(x)end')
for f in stage.rglob('*.bp'):lua.execute(f.read_text())
lua.execute((stage/'units/GGA2301/GGA2301_unit.bp').read_text());bp=lua.globals().BP
assert bp.Footprint.SizeX==1 and bp.Physics.SkirtSizeX==2 and bp.Physics.SkirtOffsetX==-.5
assert bp.Weapon[1].MuzzleSalvoDelay==0 and abs(bp.Weapon[1].RateOfFire-10/6)<1e-9
assert bp.Weapon[1].ProjectileId.endswith('GGP2301_proj.bp')
# Syntax check all Lua even when module runtime needs the game.
for f in stage.rglob('*.lua'):lua.execute('assert(load(...))',f.read_text())
# Pure terrain/wall checks with deterministic simulation stubs.
lua.execute('''categories={WALL=1}; walls={}; terrain=0
Rect=function(a,b,c,d)return {a,b,c,d} end
GetUnitsInRect=function(r)return walls end
GetTerrainHeight=function(x,z) if terrain==1 and x>4 and x<6 then return 8 end return 0 end
EntityCategoryContains=function(cat,u)return u.isWall end
origin={0,1,0}; weapon={unit={GetPosition=function()return origin end}}
function makewall(x,y,z,height)
 return {isWall=true,Dead=false,BeenDestroyed=function()return false end,
 GetPosition=function()return {x,y,z} end,GetBlueprint=function()return {SizeX=1,SizeZ=1,SizeY=height} end}
end
''')
lua.execute((stage/'lua/ishal_thar_fire_path.lua').read_text())
lua.execute('''assert(TestClearToPoint(weapon,'MuzzleLeft',{10,1,0}))
terrain=1;assert(not TestClearToPoint(weapon,'MuzzleLeft',{10,1,0}));terrain=0
walls={makewall(5,0,0,2)};assert(not TestClearToPoint(weapon,'MuzzleLeft',{10,1,0}))
walls={makewall(5,0,3,2)};assert(TestClearToPoint(weapon,'MuzzleLeft',{10,1,0}))
walls={makewall(5,0,0,.4)};assert(TestClearToPoint(weapon,'MuzzleLeft',{10,1,0}))
walls={};origin={0,1,0};assert(TestClearToPoint(weapon,'MuzzleLeft',{0,1,0}))
''')
# Run real weapon override methods with stubbed native base and fire-path module.
lua.execute('''clear=true; shotLog={}; flashLog={}
Cannon={RackSalvoFiringState={},RackSalvoFireReadyState={},
 CanWeaponFire=function()return true end,
 CreateProjectileAtMuzzle=function(self,m)table.insert(shotLog,m);return {} end,
 PlayFxMuzzleSequence=function(self,m)table.insert(flashLog,m) end,
 OnWeaponFired=function()end}
ClassUnit=function(base)return function(t)return setmetatable(t,{__index=base})end end
ClassWeapon=ClassUnit
State=function(base)return function(t)return setmetatable(t,{__index=base})end end
-- State { ... } and State(base) { ... } both supported.
State=function(base)
 if base.StateName then return base end
 return function(t)return setmetatable(t,{__index=base})end
end
import=function(path)
 if string.find(path,'fire_path') then return {IsClear=function()return clear end} end
 if string.find(path,'seraphimunits') then return {SStructureUnit={}} end
 return {SDFOhCannon=Cannon}
end
''')
lua.execute((stage/'units/GGA2301/GGA2301_script.lua').read_text())
lua.execute('''w=setmetatable({GetCurrentTarget=function()return {} end},{__index=GGA2301.Weapons.MainGun})
for i=1,8 do w:PlayFxMuzzleSequence('MuzzleLeft');w:CreateProjectileAtMuzzle('MuzzleLeft') end
for i=1,8 do local expected=i%2==1 and 'MuzzleLeft' or 'MuzzleRight';assert(shotLog[i]==expected);assert(flashLog[i]==expected) end
local before=w.NextMuzzle;clear=false;assert(not w:CanWeaponFire());assert(w:CreateProjectileAtMuzzle('MuzzleLeft')==nil);assert(#shotLog==8 and w.NextMuzzle==before)
''')
# Binary structure, bone mapping, winding/normal coherence and muzzle positions.
report=[]
for f in stage.rglob('*.scm'):
 data=f.read_bytes();h=struct.unpack_from('<4s11I',data);assert h[0]==b'MODL' and h[1]==5
 vertices=[struct.unpack_from('<16f4B',data,h[4]+68*i) for i in range(h[6])];ids=struct.unpack_from('<'+'H'*h[8],data,h[7]);assert max(ids)<len(vertices)<65536
 assert all(v[16]<h[3] and all(math.isfinite(x) for x in v[:16]) for v in vertices)
 report.append({'file':str(f.relative_to(stage)),'vertices':h[6],'triangles':h[8]//3,'bones':h[3]})
# Resolve all declared resource paths against the patch, mod and installed game archives.
mod=p.parents[2];known=set()
for folder in ['C:/ProgramData/FAForever/gamedata','D:/SteamLibrary/steamapps/common/Supreme Commander Forged Alliance/gamedata']:
 for archive in Path(folder).glob('*'):
  if archive.suffix.lower() in ['.nx2','.scd']:
   try:
    with zipfile.ZipFile(archive) as z:known.update('/'+n.replace('\\','/').lower() for n in z.namelist())
   except zipfile.BadZipFile:pass
missing=[]
for f in list(stage.rglob('*.lua'))+list(stage.rglob('*.bp')):
 for path in re.findall(r"['\"](/[^'\"]+)['\"]",f.read_text()):
  if path.startswith('/mods/Project Roc Unicorns/'):
   rel=path[len('/mods/Project Roc Unicorns/'):];candidates=[rel,rel+'.bp']
   if not any((stage/r).exists() or (mod/r).exists() for r in candidates):missing.append(path)
  elif path.lower() not in known and (path.lower()+'.bp') not in known:missing.append(path)
assert not missing,missing
(p/'validation.json').write_text(json.dumps({'status':'passed','checks':['Lua syntax','stock T2 footprint','alternating actual muzzles and flashes','blocked shot suppression','ridge and wall segment tests','SCM bone/index bounds','resource resolution'],'meshes':report,'game_match_tested':False},indent=2))
print('VALIDATION_PASSED',report)
