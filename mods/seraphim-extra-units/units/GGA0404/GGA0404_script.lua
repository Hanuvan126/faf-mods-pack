local SWalkingLandUnit = import('/lua/seraphimunits.lua').SWalkingLandUnit
local ADFPhasonLaser = import('/lua/aeonweapons.lua').ADFPhasonLaser
local SAALightningWeapon = import('/lua/seraphimweapons.lua').SAALightningWeapon
local LightningSmallSurfaceCollisionBeam = import('/lua/sim/collisionbeams/lightningsmallsurfacecollisionbeam.lua').LightningSmallSurfaceCollisionBeam

GGA0404 = ClassUnit(SWalkingLandUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        SWalkingLandUnit.OnStopBeingBuilt(self, builder, layer)
        self.ArmAimSlavers = {}
        self.ArmAimMode = {}
        self:SetArmAimMode('Left', false)
        self:SetArmAimMode('Right', false)
        self:ForkThread(self.ArmAimThread)
    end,

    -- One physical arm cannot follow two independent aim controllers at once.
    -- Prefer the anti-air controller while it has a target; suppress the ground
    -- gun on that side until the air target is lost, then restore it.
    SetArmAimMode = function(self, side, useAir)
        if self.ArmAimMode[side] == useAir then return end
        local previous = self.ArmAimSlavers[side]
        if previous then previous:Destroy() end
        self:SetWeaponEnabledByLabel(side .. 'Ground', not useAir)
        local master = side .. (useAir and 'AirAim' or 'Aim')
        local manipulator = CreateSlaver(self, side .. 'ArmVisual', master)
        self.Trash:Add(manipulator)
        self.ArmAimSlavers[side] = manipulator
        self.ArmAimMode[side] = useAir
    end,

    ArmAimThread = function(self)
        while not self.Dead and not self:BeenDestroyed() do
            for _, side in { 'Left', 'Right' } do
                local air = self:GetWeaponByLabel(side .. 'Air')
                self:SetArmAimMode(side, air and air:WeaponHasTarget() or false)
            end
            WaitTicks(2)
        end
    end,

    Weapons = {
        MainBeam = ClassWeapon(ADFPhasonLaser) {},
        LeftGround = ClassWeapon(SAALightningWeapon) { BeamType = LightningSmallSurfaceCollisionBeam, FxBeamEndPointScale = 0.01 },
        RightGround = ClassWeapon(SAALightningWeapon) { BeamType = LightningSmallSurfaceCollisionBeam, FxBeamEndPointScale = 0.01 },
        LeftAir = ClassWeapon(SAALightningWeapon) {},
        RightAir = ClassWeapon(SAALightningWeapon) {},
    },
}
TypeClass = GGA0404
