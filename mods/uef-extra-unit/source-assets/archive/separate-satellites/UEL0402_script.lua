local Base = import('/lua/terranunits.lua').TLandUnit
local HiddenBones = {
    'Turret_Right01', 'Turret_Right02', 'Turret_Left01', 'Turret_Left02',
    'Turret_Right_AA', 'Turret_Left_AA', 'Riot_Gun_Right', 'Riot_Gun_Left',
}

UEL0402 = ClassUnit(Base) {
    OnStopBeingBuilt = function(self, builder, layer)
        Base.OnStopBeingBuilt(self, builder, layer)
        for _, bone in HiddenBones do
            self:HideBone(bone, true)
        end
        self.Satellites = {}
        self:ForkThread(self.SatelliteThread)
    end,

    SatelliteThread = function(self)
        while not self.Dead and not self:BeenDestroyed() do
            for slot = 1, 4 do
                local satellite = self.Satellites[slot]
                if not satellite or satellite.Dead or satellite:BeenDestroyed() or satellite.Army ~= self.Army then
                    local p = self:GetPosition()
                    satellite = CreateUnitHPR('UEA0004', self.Army, p[1], p[2] + 5, p[3], 0, 0, 0)
                    if satellite then
                        self.Satellites[slot] = satellite
                        satellite:SetCreator(self)
                        satellite:StartSatellite(self, slot)
                    end
                end
            end
            WaitSeconds(5)
        end
    end,

    OnDestroy = function(self)
        if self.Satellites then
            for _, satellite in self.Satellites do
                if satellite and not satellite.Dead and not satellite:BeenDestroyed() then
                    satellite:Destroy()
                end
            end
        end
        Base.OnDestroy(self)
    end,
}
TypeClass = UEL0402
