from pathlib import Path
import re
p=Path(__file__).parent;mod=p.parents[2];stage=p/'runtime';u=stage/'units/GGA2301'
bp=(mod/'units/GGA2301/GGA2301_unit.bp').read_text()
bp=re.sub(r"        Animation(?:Activate|Idle) = .*?\n",'',bp)
bp=bp.replace('UniformScale = 0.06','UniformScale = 0.40')
bp=bp.replace('    Economy = {', '''    Footprint = { SizeX = 1, SizeZ = 1 },
    Economy = {''')
bp=bp.replace('        UniformScale = 0.40,', '''        UniformScale = 0.40,
        MeshBlueprintWrecked = '/mods/Project Roc Unicorns/units/GGA2301/GGA2301_wreck_mesh',
        Tarmacs = { {
            Albedo = 'Tarmacs/Tar6x_seraphim_01_albedo',
            Normal = 'Tarmacs/Tar6x_seraphim_01_normals',
            Width = 6.4, Length = 6.4, Orientations = { 0, 90, 180, 270 },
            DeathLifetime = 300, FadeOut = 150, RemoveWhenDead = false,
        } },''')
bp=bp.replace("<LOC gga2301_help>T3 point defense with an upgraded ultrachromatic beam",'T3 twin comet point defense')
bp=bp.replace('SelectionThickness = 0.5','SelectionThickness = 0.25').replace('MeshExtentsY = 2.5','MeshExtentsY = 1.8').replace('SizeY = 2,','SizeY = 1.6,').replace('CollisionOffsetY = -0.25','CollisionOffsetY = 0')
bp=re.sub(r'            Audio = \{.*?            \},',"""            Audio = { Fire = Sound { Bank = 'XSL_Weapon', Cue = 'XSL0201_Cannon_Spectra', LodCutoff = 'Weapon_LodCutoff' } },""",bp,flags=re.S)
bp=re.sub(r'            Beam\w+ = .*?\n','',bp)
replaces={'CollideFriendly = false':'CollideFriendly = true','Damage = 175':'Damage = 130','DamageRadius = 0':'DamageRadius = 0.35',"DisplayName = 'Ultrachromatic Beam Generator'":"DisplayName = 'Twin Comet Cannon'",'FiringTolerance = 0':'FiringTolerance = 2','LeadTarget = false':'LeadTarget = true','RateOfFire = 10 / 40':'RateOfFire = 10 / 3',"'Turret_Muzzle'":"'MuzzleLeft'","'Turret_Barrel'":"'TurretPitch'","'Turret'":"'TurretYaw'",'RackRecoilDistance = -1':'RackRecoilDistance = -0.08',"RackBone = 'TurretPitch'":"RackBone = 'GunRecoil'",'TurretPitchRange = 30':'TurretPitchRange = 45',"Land = 'Land|Water|Seabed'":"Land = 'Land|Water'","Water = 'Land|Water|Seabed'":"Water = 'Land|Water'"}
for a,b in replaces.items():bp=bp.replace(a,b)
bp=bp.replace('            Damage = 130,',"""            Damage = 130,
            DamageFriendly = false,
            MuzzleVelocity = 85,
            ProjectileId = '/mods/Project Roc Unicorns/projectiles/GGP2301/GGP2301_proj.bp',""")
(u/'GGA2301_unit.bp').write_text(bp)
script='''local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local Cannon = import('/lua/seraphimweapons.lua').SDFOhCannon
local FirePath = import('/mods/Project Roc Unicorns/lua/ishal_thar_fire_path.lua')

GGA2301 = ClassUnit(SStructureUnit) {
    Weapons = {
        MainGun = ClassWeapon(Cannon) {
            FxMuzzleFlashScale = 0.35,
            NextMuzzle = 'MuzzleLeft',
            CanWeaponFire = function(self)
                return Cannon.CanWeaponFire(self) and FirePath.IsClear(self, self.NextMuzzle)
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                if FirePath.IsClear(self, self.NextMuzzle) then
                    Cannon.PlayFxMuzzleSequence(self, self.NextMuzzle)
                end
            end,
            CreateProjectileAtMuzzle = function(self, muzzle)
                local actual = self.NextMuzzle
                if not FirePath.IsClear(self, actual) then
                    self.RejectedTarget = self:GetCurrentTarget()
                    self.BlockedOnRelease = true
                    return nil
                end
                local projectile = Cannon.CreateProjectileAtMuzzle(self, actual)
                if projectile then
                    self.NextMuzzle = actual == 'MuzzleLeft' and 'MuzzleRight' or 'MuzzleLeft'
                end
                return projectile
            end,
            OnWeaponFired = function(self)
                Cannon.OnWeaponFired(self)
                if self.BlockedOnRelease then
                    self.BlockedOnRelease = false
                    ChangeState(self, self.BlockedState)
                end
            end,
            BlockedState = State {
                StateName = 'BlockedState',
                WeaponWantEnabled = false,
                WeaponAimWantEnabled = false,
                Main = function(self)
                    self.unit:SetBusy(false)
                    self.unit:SetWorkProgress(1)
                    local rejected = self.RejectedTarget
                    self.RejectedTarget = nil
                    self:ResetTarget()
                    local target = FirePath.FindClearTarget(self, self.NextMuzzle, rejected)
                    if target then
                        self.ClearTarget = target
                        ChangeState(self, self.ClearTargetState)
                        return
                    end
                    WaitTicks(5)
                    if not self:BeenDestroyed() and not self.unit.Dead then
                        self:ResetTarget()
                        ChangeState(self, self.IdleState)
                    end
                end,
            },
            ClearTargetState = State {
                StateName = 'ClearTargetState',
                WeaponWantEnabled = true,
                WeaponAimWantEnabled = true,
                Main = function(self)
                    local target = self.ClearTarget
                    self.ClearTarget = nil
                    if target and not target.Dead and not target:BeenDestroyed() then
                        self:SetTargetEntity(target)
                    end
                    ChangeState(self, self.RackSalvoFireReadyState)
                end,
            },
            RackSalvoFiringState = State(Cannon.RackSalvoFiringState) {
                Main = function(self)
                    if not self:WeaponHasTarget() then
                        WaitTicks(1)
                        if not self:WeaponHasTarget() then ChangeState(self, self.IdleState); return end
                    end
                    if not FirePath.IsClear(self, self.NextMuzzle) then
                        self.RejectedTarget = self:GetCurrentTarget()
                        ChangeState(self, self.BlockedState)
                        return
                    end
                    Cannon.RackSalvoFiringState.Main(self)
                end,
            },
        },
    },
}
TypeClass = GGA2301
'''
(u/'GGA2301_script.lua').write_text(script)
# Reuse the previously implemented target-priority/visibility logic, scoped to this gun.
f=(mod/'lua/dush_nai_fire_path.lua').read_text()
f=f.replace('    return true\nend', '''    -- Physical walls of any army block a shot only if its segment crosses their volume.
    local walls = GetUnitsInRect(Rect(math.min(origin[1],target[1])-2,
        math.min(origin[3],target[3])-2, math.max(origin[1],target[1])+2,
        math.max(origin[3],target[3])+2))
    for _, wall in ipairs(walls or {}) do
        if wall ~= weapon.unit and not wall.Dead and not wall:BeenDestroyed()
            and EntityCategoryContains(categories.WALL, wall) then
            local pos = wall:GetPosition()
            local bp = wall:GetBlueprint()
            local wx = pos[1] + (bp.CollisionOffsetX or 0)
            local wz = pos[3] + (bp.CollisionOffsetZ or 0)
            local radius = math.max(bp.SizeX or 1, bp.SizeZ or 1) * .5 + .055
            local len2 = dx*dx + dz*dz
            local t = len2 > 0 and ((wx-origin[1])*dx+(wz-origin[3])*dz)/len2 or 0
            if t > .001 and t < .999 then
                local ex, ez = origin[1]+dx*t-wx, origin[3]+dz*t-wz
                local y = origin[2]+dy*t
                local bottom = pos[2] + (bp.CollisionOffsetY or 0)
                if ex*ex+ez*ez <= radius*radius and y >= bottom-.055
                    and y <= bottom+(bp.SizeY or 1)+.055 then return false end
            end
        end
    end
    return true
end''',1)
# Expose pure segment check for repeatable regression checks.
f += '\nTestClearToPoint = ClearToPoint\n'
(stage/'lua').mkdir(exist_ok=True);(stage/'lua/ishal_thar_fire_path.lua').write_text(f)
pr=stage/'projectiles/GGP2301'
(pr/'GGP2301_proj.bp').write_text('''ProjectileBlueprint {
    Categories = { 'DIRECTFIRE', 'PROJECTILE', 'SERAPHIM' },
    General = { Category = 'Direct Fire', Faction = 'Seraphim', Weapon = 'Comet Cannon' },
    Display = { UniformScale = 1, Mesh = { LODs = { {
        MeshName = '/mods/Project Roc Unicorns/projectiles/GGP2301/GGP2301_lod0.scm',
        AlbedoName = '/mods/Project Roc Unicorns/projectiles/GGP2301/GGP2301_albedo.dds',
        SpecularName = '/mods/Project Roc Unicorns/projectiles/GGP2301/GGP2301_specteam.dds',
        NormalsName = '/mods/Project Roc Unicorns/projectiles/GGP2301/GGP2301_normalsTS.dds',
        ShaderName = 'Seraphim', LookupName = '/textures/environment/Falloff_seraphim_lookup.dds', LODCutoff = 180,
    } } } },
    Physics = { DestroyOnWater = true, InitialSpeed = 85, InitialSpeedRange = 0,
        MaxSpeed = 85, Acceleration = 0, UseGravity = false, TrackTarget = false,
        TurnRate = 0, VelocityAlign = true, Lifetime = 2 },
    SizeX = 0.11, SizeY = 0.11, SizeZ = 0.11,
    Audio = { Impact = Sound { Bank = 'Impacts', Cue = 'X_Impact_Land_Gen_Seraphim', LodCutoff = 'Weapon_LodCutoff' } },
}
''')
(pr/'GGP2301_script.lua').write_text('''local Base = import('/lua/sim/projectiles/SinglePolyTrailProjectile.lua').SinglePolyTrailProjectile
local EffectTemplate = import('/lua/effecttemplates.lua')
GGP2301 = ClassProjectile(Base) {
    PolyTrail = '/mods/Project Roc Unicorns/effects/emitters/ishal_comet_trail_emit.bp',
    FxTrails = {},
    FxImpactLand = EffectTemplate.OhCannonHit,
    FxImpactUnit = EffectTemplate.OhCannonHitUnit,
    FxImpactProp = EffectTemplate.OhCannonHit,
    FxImpactWater = EffectTemplate.OhCannonHit,
    FxLandHitScale = 0.45, FxUnitHitScale = 0.45, FxPropHitScale = 0.45, FxWaterHitScale = 0.45,
    DestroyOnImpact = true,
}
TypeClass = GGP2301
''')
e=stage/'effects/emitters';e.mkdir(parents=True,exist_ok=True)
(e/'ishal_comet_trail_emit.bp').write_text('''TrailEmitterBlueprint {
    BlendMode = 3, LODCutoff = 180, Lifetime = -1,
    RampTexture = '/mods/Project Roc Unicorns/textures/particles/ishal_comet_ramp.dds',
    RepeatTexture = '/textures/particles/trail_white_01.dds',
    Size = 0.075, SortOrder = 0, TextureRepeatRate = 0.2, TrailLength = 1.7,
}
''')
print('SCRIPT_BLUEPRINT_READY')
