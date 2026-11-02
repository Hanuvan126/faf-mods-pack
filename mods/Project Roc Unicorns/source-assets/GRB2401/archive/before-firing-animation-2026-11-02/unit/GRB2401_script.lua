local CWalkingLandUnit = import('/lua/cybranunits.lua').CWalkingLandUnit
local CIFArtilleryWeapon = import('/lua/cybranweapons.lua').CIFArtilleryWeapon
GRB2401 = ClassUnit(CWalkingLandUnit) {
    -- Match the stock Megalith's directional walking animation behavior.
    OnMotionHorzEventChange = function(self, new, old)
        CWalkingLandUnit.OnMotionHorzEventChange(self, new, old)
        if old == 'Stopped' then
            local display = self:GetBlueprint().Display
            if display.AnimationWalk and self.Animator then
                self.Animator:SetDirectionalAnim(true)
                self.Animator:SetRate(display.AnimationWalkRate)
            end
        end
    end,
    Weapons = {
        MainGun = ClassWeapon(CIFArtilleryWeapon) {
            FxMuzzleFlash = {
                '/effects/emitters/cybran_artillery_muzzle_flash_01_emit.bp',
                '/effects/emitters/cybran_artillery_muzzle_flash_02_emit.bp',
                '/effects/emitters/cybran_artillery_muzzle_smoke_01_emit.bp',
            },
        },
    },
}
TypeClass = GRB2401
