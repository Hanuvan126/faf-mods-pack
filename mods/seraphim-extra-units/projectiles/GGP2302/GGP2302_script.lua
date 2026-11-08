local Base = import('/lua/sim/projectiles/EmitterProjectile.lua').EmitterProjectile
local EffectTemplate = import('/lua/effecttemplates.lua')
GGP2302 = ClassProjectile(Base) {
    -- No polytrail, point light, pulse animation, or repeatedly spawned head glow.
    FxTrails = {
        '/mods/seraphim-extra-units/effects/emitters/sha_veyr_stardust_mist_emit.bp',
        '/mods/seraphim-extra-units/effects/emitters/sha_veyr_stardust_stars_emit.bp',
    },
    FxImpactLand = EffectTemplate.OhCannonHit,
    FxImpactUnit = EffectTemplate.OhCannonHitUnit,
    FxImpactProp = EffectTemplate.OhCannonHit,
    FxImpactWater = EffectTemplate.OhCannonHit,
    FxLandHitScale = 0.30, FxUnitHitScale = 0.30, FxPropHitScale = 0.30, FxWaterHitScale = 0.30,
    DestroyOnImpact = true,
}
TypeClass = GGP2302
