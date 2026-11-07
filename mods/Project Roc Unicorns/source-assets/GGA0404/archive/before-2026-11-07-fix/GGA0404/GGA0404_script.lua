local SWalkingLandUnit = import('/lua/seraphimunits.lua').SWalkingLandUnit
local ADFPhasonLaser = import('/lua/aeonweapons.lua').ADFPhasonLaser
local SAALightningWeapon = import('/lua/seraphimweapons.lua').SAALightningWeapon
local LightningSmallSurfaceCollisionBeam = import('/lua/sim/collisionbeams/lightningsmallsurfacecollisionbeam.lua').LightningSmallSurfaceCollisionBeam

GGA0404 = ClassUnit(SWalkingLandUnit) {
    Weapons = {
        MainBeam = ClassWeapon(ADFPhasonLaser) {},
        LeftGround = ClassWeapon(SAALightningWeapon) { BeamType = LightningSmallSurfaceCollisionBeam, FxBeamEndPointScale = 0.01 },
        RightGround = ClassWeapon(SAALightningWeapon) { BeamType = LightningSmallSurfaceCollisionBeam, FxBeamEndPointScale = 0.01 },
        LeftAir = ClassWeapon(SAALightningWeapon) {},
        RightAir = ClassWeapon(SAALightningWeapon) {},
    },
}
TypeClass = GGA0404
