local Base = import('/lua/aeonunits.lua').AShieldHoverLandUnit

NEA0401 = ClassUnit(Base) {
    OnStopBeingBuilt = function(self, builder, layer)
        Base.OnStopBeingBuilt(self, builder, layer)
        self.Swarm = {}
        self:ForkThread(self.SwarmProductionThread)
    end,

    SwarmProductionThread = function(self)
        while not self.Dead and not self:BeenDestroyed() do
            for slot = 1, 20 do
                if self.Dead or self:BeenDestroyed() then return end
                local drone = self.Swarm[slot]
                if not drone or drone.Dead or drone:BeenDestroyed() then
                    local pos = self:GetPosition()
                    drone = CreateUnitHPR('NEA0001', self.Army, pos[1], pos[2] + 3, pos[3], 0, 0, 0)
                    if drone then
                        self.Swarm[slot] = drone
                        drone:SetCreator(self)
                        drone:StartSwarm(self, slot)
                    end
                    -- One completed drone every three seconds, with no extra resource cost.
                    WaitSeconds(3)
                end
            end
            WaitSeconds(1)
        end
    end,

    OnDestroy = function(self)
        if self.Swarm then
            for _, drone in self.Swarm do
                if drone and not drone.Dead and not drone:BeenDestroyed() then
                    drone:Destroy()
                end
            end
        end
        Base.OnDestroy(self)
    end,
}
TypeClass = NEA0401
