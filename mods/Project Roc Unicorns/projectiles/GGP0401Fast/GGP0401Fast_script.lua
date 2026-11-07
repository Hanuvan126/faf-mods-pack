local Phason = import('/mods/Project Roc Unicorns/projectiles/GGP0401/GGP0401_script.lua').GGP0401
local Trails = import('/lua/effecttemplates.lua').SDFAireauWeaponPolytrails01

GGP0401Fast = ClassProjectile(Phason) {
    OnCreate = function(self, inWater)
        Phason.OnCreate(self, inWater)
        for _, trail in Trails do
            CreateTrail(self, -1, self.Army, trail)
        end
    end,
}
TypeClass = GGP0401Fast
