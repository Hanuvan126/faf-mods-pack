local AStructureUnit = import('/lua/aeonunits.lua').AStructureUnit
local ADFPhasonLaser = import('/lua/aeonweapons.lua').ADFPhasonLaser

NSB2201 = Class(AStructureUnit) {
    Weapons = {
        MainGun = Class(ADFPhasonLaser) {},
    },
}
TypeClass = NSB2201
