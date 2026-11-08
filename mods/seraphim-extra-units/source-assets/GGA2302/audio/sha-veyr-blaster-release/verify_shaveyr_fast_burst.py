from pathlib import Path
import sys,re,json,zipfile
sys.path.insert(0,'F:/FAF-Development/work/pythonlibs')
from lupa import LuaRuntime
ROOT=Path('F:/FAF-Development/work/faf-upload');MOD=ROOT/'mods/Project Roc Unicorns';OUT=ROOT/'outputs/ShaVeyr_Burst_20261108'
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
table.getn=function(t) return #t end
function UnitBlueprint(t) BP=t end
function ProjectileBlueprint(t) PROJ=t end
function PropBlueprint(t) PROP=t end
function Sound(t) return t end
function EmitterBlueprint(t) return t end
function ClassUnit(base) return function(t) return setmetatable(t,{__index=base}) end end
ClassWeapon=ClassUnit
function State(t) return setmetatable(t,{__call=function(parent,child) return setmetatable(child,{__index=parent}) end}) end
clock=0; shots={}; blocked=false; blockAfter=nil
function WaitSeconds(t) clock=clock+t end
function WaitTicks(t) clock=clock+t/10 end
function ChangeState(self,state) self.state=state end
function nop() end
Cannon={CanWeaponFire=function() return true end,PlayFxMuzzleSequence=nop,OnWeaponFired=nop,
 CreateProjectileAtMuzzle=function(self,bone) table.insert(shots,{time=clock,barrel=bone});return {BeenDestroyed=function() return false end} end,
 RackSalvoFireReadyState={},RackSalvoFiringState={},RackSalvoReloadState={}}
FirePath={IsClear=function() return not blockAfter or #shots<blockAfter end}
function import(path)
 if string.find(path,'seraphimunits') then return {SStructureUnit={}} end
 if string.find(path,'seraphimweapons') then return {SDFOhCannon=Cannon} end
 return FirePath
end
''')
lua.execute((MOD/'units/GGA2302/GGA2302_unit.bp').read_text())
lua.execute((MOD/'projectiles/GGP2302/GGP2302_proj.bp').read_text())
lua.execute((MOD/'units/GGA2302/GGA2302_script.lua').read_text())
native=Path('faf_inspect/DefaultProjectileWeapon.lua').read_text()
section=native.split('    RackSalvoFiringState = State {',1)[1]
body=section.split('        Main = function(self)',1)[1].split('        ---@param self DefaultProjectileWeapon_RackSalvoFiringState',1)[0].strip()
assert body.endswith('end,');lua.execute('NativeFire = function(self)'+body[:-1])
section=native.split('    RackSalvoReloadState = State {',1)[1]
body=section.split('        Main = function(self)',1)[1].split('        ---@param self DefaultProjectileWeapon_RackSalvoReloadState',1)[0].strip()
assert body.endswith('end,');lua.execute('NativeReload = function(self)'+body[:-1])
lua.execute('''
function weapon()
 local w=setmetatable({NextMuzzle='MuzzleLeft',Blueprint=BP.Weapon[1],NumRackBones=1,CurrentRackSalvoNumber=1,
 unit={Dead=false,SetBusy=nop},RackSalvoReloadState={},RackSalvoFireReadyState={},IdleState={}}, {__index=GGA2302.Weapons.MainGun})
 w.GetWeaponRoF=function(self) return self.Blueprint.RateOfFire end
 w.BeenDestroyed=function() return false end
 w.WeaponHasTarget=function() return true end
 w.GetCurrentTarget=function() return {} end
 w.DestroyRecoilManips=nop;w.PlayFxRackReloadSequence=nop;w.DoOnFireBuffs=nop;w.StartEconomyDrain=nop;w.ForkThread=nop
 w.PlayFxRackSalvoReloadSequence=nop;w.WaitForAndDestroyManips=nop
 return w
end
w=weapon(); NativeFire(w);NativeReload(w);NativeFire(w);NativeReload(w)
assert(#shots==10)
for i=1,10 do
 local expected=i<=5 and 'MuzzleLeft' or 'MuzzleRight'
 assert(shots[i].barrel==expected)
 local t=i<=5 and (i-1)*.1 or 3.5+(i-6)*.1
 assert(math.abs(shots[i].time-t)<.0001)
end
timeline=shots
clock=0;shots={};blockAfter=2;w=weapon();NativeFire(w);assert(#shots==2);blockAfter=nil
assert(BP.Weapon[1].RackRecoilDistance==0 and BP.Weapon[1].MuzzleSalvoDelay>0)
assert(BP.Weapon[1].MaxRadius==80 and BP.Weapon[1].DamageRadius==2)
assert(BP.Weapon[1].MuzzleVelocity==22.5 and PROJ.Physics.MaxSpeed==22.5)
assert(BP.Display.UniformScale==.8 and BP.Physics.SkirtSizeX==4 and BP.Footprint.SizeX==2)
''')

print("PASS: native firing/reload timeline 0,.1,.2,.3,.4 / 3.5,3.6,3.7,3.8,3.9; barrel alternation and blocked-fire checks")
