local CWalkingLandUnit = import('/lua/cybranunits.lua').CWalkingLandUnit
local CIFArtilleryWeapon = import('/lua/cybranweapons.lua').CIFArtilleryWeapon
GRB2401 = ClassUnit(CWalkingLandUnit) {
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
