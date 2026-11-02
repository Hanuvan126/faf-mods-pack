"""Run installed FAF wreck smoke + DestroyUnit path with bone-validating API doubles."""
from pathlib import Path
import struct,sys,json,zipfile,re
sys.path.insert(0,'F:/FAF-Development/work/pythonlibs')
from lupa import LuaRuntime
SRC=Path(__file__).resolve().parent;MOD=SRC.parents[1];OUT=Path('F:/FAF-Development/outputs/VaelItha_Wreck_Death_Fix_v8')
def bones(p):return struct.unpack_from('<4s11I',p.read_bytes())[3]
with zipfile.ZipFile('C:/ProgramData/FAForever/gamedata/lua.nx2') as z:
 exp=z.read('lua/defaultexplosions.lua').decode();unit=z.read('lua/sim/Unit.lua').decode()
fx=exp[exp.index('function CreateWreckageEffects(unit, prop)'):exp.index('\n--------------------------------',exp.index('function CreateWreckageEffects(unit, prop)'))]
start=unit.index('    DestroyUnit = function(self, overkillRatio)');end=unit.index('\n    end,',start)+len('\n    end')
destroy='DestroyUnit = '+unit[start:end].split('=',1)[1]
results=[]
for uid in ['GGA2404','GGA0401']:
 live=bones(MOD/f'units/{uid}/{uid}_lod0.scm')
 for lod in [0,1]:
  dead=bones(MOD/f'props/{uid}_wreck/{uid}_wreck_lod{lod}.scm')
  for pick in ['min','max','middle']:
   l=LuaRuntime();l.globals().LiveCount=live;l.globals().WreckCount=dead;l.globals().Pick=pick
   l.execute('''
MathFloor=math.floor; DefaultWreckageEffectsCount=1; DefaultWreckageEffects={'native-smoke'}
function Random(a,b) if a==nil then return .5 end if Pick=='min' then return a elseif Pick=='max' then return b else return math.floor((a+b)/2) end end
function CreateEmitterAtBone(prop,bone,army,effect)
 assert(bone>=0 and bone<WreckCount,'Invalid wreck bone '..bone..' (wreck has '..WreckCount..', live unit '..LiveCount..')')
 prop.SmokeCount=prop.SmokeCount+1;return {}
end
function IEffectScaleEmitter(...)end;function IEffectSetEmitterParam(...)end;function ApplyWindDirection(...)end
function WaitSeconds(...)end
prop={SmokeCount=0,Trash={Add=function()end}}
unit={Army=1,DeathThreadDestructionWaitTime=.1,Blueprint={SizeX=3.4,SizeY=4.4,SizeZ=3.4,Display={}},Destroyed=false,FootprintReserved=true}
function unit:GetBoneCount()return LiveCount end
function unit:PlayUnitSound(...)end
function unit:Destroy()self.Destroyed=true;self.FootprintReserved=false end
''')
   l.execute(fx);l.execute(destroy)
   l.execute('function unit:CreateWreckage(overkill) self.Wreck=prop;CreateWreckageEffects(self,prop);return prop end')
   # An invalid native smoke bone previously raised here after spawning the prop,
   # so DestroyUnit never reached Destroy and the original building survived.
   l.execute('DestroyUnit(unit,.2);assert(unit.Destroyed);assert(not unit.FootprintReserved);assert(unit.Wreck==prop);assert(prop.SmokeCount>0)')
  assert dead>=live
  results.append({'unit':uid,'lod':lod,'live_bones':live,'wreck_bones':dead,'native_DestroyUnit_reached_Destroy':True})
report={'native_smoke_and_destroy_path':results,'random_choices_tested':['min','max','middle'],'limits':'Native Lua functions with strict bone API doubles; engine pathing and actual in-game placement not run.'}
(OUT/'death_cleanup_validation.json').write_text(json.dumps(report,indent=2));print('DEATH_CLEANUP_CHECKS_PASS',json.dumps(report))
