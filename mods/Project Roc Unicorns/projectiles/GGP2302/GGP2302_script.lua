local Base = import('/lua/sim/projectiles/EmitterProjectile.lua').EmitterProjectile
local Impact = {
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_flash_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_ring_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_mist_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_sparks_emit.bp',
}
GGP2302 = ClassProjectile(Base) {
    -- No polytrail, point light, pulse animation, or repeatedly spawned head glow.
    FxTrails = {
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_stardust_mist_emit.bp',
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_stardust_stars_emit.bp',
    },
    FxImpactLand = Impact,
    FxImpactUnit = Impact,
    FxImpactProp = Impact,
    FxImpactWater = Impact,
    FxLandHitScale = 1.0, FxUnitHitScale = 1.0, FxPropHitScale = 1.0, FxWaterHitScale = 1.0,
    DestroyOnImpact = true,
}
TypeClass = GGP2302
