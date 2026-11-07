local AStructureUnit = import('/lua/aeonunits.lua').AStructureUnit
local ACruiseMissileWeapon = import('/lua/aeonweapons.lua').ACruiseMissileWeapon
AEM2301 = Class(AStructureUnit) {
    Weapons = { MainGun = Class(ACruiseMissileWeapon) {} },
}
TypeClass = AEM2301
