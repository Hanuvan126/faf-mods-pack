from pathlib import Path
import re,zipfile,json
ROOT=Path('F:/FAF-Development/work/faf-upload')
MOD=ROOT/'mods/Project Roc Unicorns'
OUT=ROOT/'outputs/ShaVeyr_Burst_20261108';OUT.mkdir(exist_ok=True)
files=[*list((MOD/'units/GGA2302').glob('*')),*list((MOD/'projectiles/GGP2302').glob('*')),*list((MOD/'effects/emitters').glob('sha_veyr*')),*list((MOD/'props/GGA2302_wreck').glob('*'))]
if not (OUT/'before.zip').exists():
 with zipfile.ZipFile(OUT/'before.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:
   if p.is_file():z.write(p,p.relative_to(MOD))
def replace(path,changes):
 text=path.read_text()
 for a,b in changes:
  assert a in text,(path,a)
  text=text.replace(a,b)
 path.write_text(text)
replace(MOD/'units/GGA2302/GGA2302_unit.bp',[
 ('UniformScale = 0.40','UniformScale = 0.80'),
 ('Width = 6.4, Length = 6.4','Width = 12.8, Length = 12.8'),
 ('Footprint = { SizeX = 1, SizeZ = 1 }','Footprint = { SizeX = 2, SizeZ = 2 }'),
 ('LifeBarHeight = 0.075','LifeBarHeight = 0.15'),('LifeBarOffset = 0.75','LifeBarOffset = 1.5'),('LifeBarSize = 1.25','LifeBarSize = 2.5'),
 ('MeshExtentsX = 1.75','MeshExtentsX = 3.5'),('MeshExtentsY = 1.8','MeshExtentsY = 3.6'),('MeshExtentsZ = 2,','MeshExtentsZ = 4,'),
 ('SkirtOffsetX = -0.5','SkirtOffsetX = -1.5'),('SkirtOffsetZ = -0.5','SkirtOffsetZ = -1.5'),('SkirtSizeX = 2','SkirtSizeX = 4'),('SkirtSizeZ = 2','SkirtSizeZ = 4'),
 ('SelectionSizeX = 0.75','SelectionSizeX = 1.5'),('SelectionSizeZ = 0.75','SelectionSizeZ = 1.5'),
 ('    SizeX = 1,','    SizeX = 2,'),('    SizeY = 1.6,','    SizeY = 3.2,'),('    SizeZ = 1,','    SizeZ = 2,'),
 ('MuzzleVelocity = 45','MuzzleVelocity = 22.5'),('DamageRadius = 0.35','DamageRadius = 2'),('FiringRandomness = 0,','FiringRandomness = 0.6,'),
 ('MuzzleSalvoDelay = 0,','MuzzleSalvoDelay = 0.2,'),('MuzzleSalvoSize = 1,','MuzzleSalvoSize = 5,'),
 ('RackRecoilDistance = -0.08','RackRecoilDistance = 0'),('RackSalvoReloadTime = 0,','RackSalvoReloadTime = 3,'),('RateOfFire = 10 / 6','RateOfFire = 0.25')])
replace(MOD/'projectiles/GGP2302/GGP2302_proj.bp',[
 ('UniformScale = 1,','UniformScale = 4,'),('InitialSpeed = 45','InitialSpeed = 22.5'),('MaxSpeed = 45','MaxSpeed = 22.5'),('Lifetime = 3','Lifetime = 8'),
 ('SizeX = 0.22, SizeY = 0.22, SizeZ = 0.22','SizeX = 0.88, SizeY = 0.88, SizeZ = 0.88')])
replace(MOD/'props/GGA2302_wreck/GGA2302_wreck_prop.bp',[
 ('SizeX = 1.8, SizeY = 0.6, SizeZ = 1.8','SizeX = 3.6, SizeY = 1.2, SizeZ = 3.6')])
path=MOD/'units/GGA2302/GGA2302_script.lua'
replace(path,[('FxMuzzleFlashScale = 0.35','FxMuzzleFlashScale = 0.70'),
 ("self.BlockedOnRelease = true\n                    return nil","self.BlockedOnRelease = true\n                    self.HaltFireOrdered = true\n                    return nil"),
 ("self.NextMuzzle = actual == 'MuzzleLeft' and 'MuzzleRight' or 'MuzzleLeft'", "self.BurstHasFired = true\n                    self:ForkThread(self.PulseRecoil)"),
 ("            OnWeaponFired = function(self)\n                Cannon.OnWeaponFired(self)\n                if self.BlockedOnRelease then\n                    self.BlockedOnRelease = false\n                    ChangeState(self, self.BlockedState)\n                end\n            end,", """            -- Native muzzle salvo holds one barrel for all five shots.
            -- OnWeaponFired runs once per salvo, not once per projectile.
            OnWeaponFired = function(self)
                Cannon.OnWeaponFired(self)
                if self.BurstHasFired then
                    self.NextMuzzle = self.NextMuzzle == 'MuzzleLeft' and 'MuzzleRight' or 'MuzzleLeft'
                    self.BurstHasFired = false
                end
                -- Let native reload finish; ready-state obstruction recovery follows it.
                self.BlockedOnRelease = false
            end,
            PulseRecoil = function(self)
                if self:BeenDestroyed() or self.unit.Dead then return end
                if not self.BurstRecoil then
                    self.BurstRecoil = CreateSlider(self.unit, 'GunRecoil')
                    self.Trash:Add(self.BurstRecoil)
                end
                self.BurstRecoil:SetSpeed(12)
                self.BurstRecoil:SetGoal(0, 0, -0.20)
                WaitTicks(1)
                if self:BeenDestroyed() or self.unit.Dead then return end
                self.BurstRecoil:SetGoal(0, 0, 0)
                self.BurstRecoil:SetSpeed(4)
            end,""")])
# Stock-compatible emitter fields, local copies referencing existing game textures.
def emitter(name,texture,ramp,flat,life,rate,particlelife,start,end,speed=0,spread=0,blend=0):
 text=(MOD/'effects/emitters/sha_veyr_stardust_mist_emit.bp').read_text()
 text=text.replace('Lifetime = -1,',f'Lifetime = {life},').replace('Blendmode = 0,',f'Blendmode = {blend},').replace('Flat = false,',f'Flat = {str(flat).lower()},')
 text=re.sub(r"Texture = '[^']+'",f"Texture = '{texture}'",text)
 text=re.sub(r"RampTexture = '[^']+'",f"RampTexture = '{ramp}'",text)
 vals={'EmitRateCurve':(rate,0),'LifetimeCurve':(particlelife,0),'StartSizeCurve':(start,0),'EndSizeCurve':(end,0),'VelocityCurve':(speed,0),
       'XDirectionCurve':(0,spread),'YDirectionCurve':(.25 if speed else 0,spread*.3),'ZDirectionCurve':(0,spread)}
 for key,(value,variation) in vals.items():
  text=re.sub(key+r' = \{ XRange = 1, Keys = \{ \{[^}]+\} \} \}',f'{key} = {{ XRange = 1, Keys = {{ {{ x=0, y={value}, z={variation} }} }} }}',text)
 text=text.replace('YPosCurve = { XRange = 1, Keys = { { x=0, y=0, z=0.045 } } }','YPosCurve = { XRange = 1, Keys = { { x=0, y=0.08, z=0 } } }')
 (MOD/f'effects/emitters/sha_veyr_impact_{name}_emit.bp').write_text(text)
purple='/mods/Project Roc Unicorns/textures/particles/sha_veyr_stardust_mist_ramp.dds'
emitter('ring','/textures/particles/quantum_plasma_ring01.dds',purple,True,.1,10,.45,.25,2,blend=1)
emitter('flash','/textures/particles/flare_lens_add_01.dds','/textures/particles/ramp_white_premod_01.dds',False,.1,10,.16,.55,.1,blend=1)
emitter('mist','/mods/Project Roc Unicorns/textures/particles/sha_veyr_stardust_mist.dds',purple,False,.15,40,.65,.25,.8,.8,1)
emitter('sparks','/mods/Project Roc Unicorns/textures/particles/sha_veyr_stardust_stars.dds','/mods/Project Roc Unicorns/textures/particles/sha_veyr_stardust_stars_ramp.dds',False,.1,100,.38,.10,.015,3,1,1)
p=MOD/'projectiles/GGP2302/GGP2302_script.lua';text=p.read_text()
text=text.replace("local EffectTemplate = import('/lua/effecttemplates.lua')", """local Impact = {
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_flash_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_ring_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_mist_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_sparks_emit.bp',
}""")
text=text.replace('EffectTemplate.OhCannonHitUnit','Impact').replace('EffectTemplate.OhCannonHit','Impact').replace('Scale = 0.30','Scale = 1.0')
p.write_text(text)
(OUT/'parameters.json').write_text(json.dumps({'shots_per_burst':5,'shot_interval_seconds':.2,'native_salvo_duration_seconds':1,'reload_seconds':3,'barrel_sequence':'LLLLL RRRRR','projectile_scale':4,'projectile_speed':22.5,'splash_radius':2,'randomness':.6,'range':80,'damage_per_projectile':130,'tower_scale':.8,'construction_skirt':[4,4]},indent=2))
print('Blueprint, burst logic and impact emitters written; texture pass follows.')
