local Base = import('/lua/terranunits.lua').TAirUnit
local Laser = import('/lua/terranweapons.lua').TOrbitalDeathLaserBeamWeapon
local Targets = (categories.LAND + categories.NAVAL + categories.STRUCTURE) - categories.UNTARGETABLE
local Radius = 300

UEA0004 = ClassUnit(Base) {
    DestroyNoFallRandomChance = 1.1,
    Weapons = { OrbitalDeathLaserWeapon = ClassWeapon(Laser) {} },

    OnCreate = function(self)
        Base.OnCreate(self)
        self:SetUnSelectable(true)
    end,

    StartSatellite = function(self, carrier, slot)
        self.Carrier = carrier
        self.Slot = slot
        self:ForkThread(self.OpenSatellite)
        self:ForkThread(self.ControlSatellite)
    end,

    OpenSatellite = function(self)
        local anim = CreateAnimator(self)
        self.Trash:Add(anim)
        anim:PlayAnim('/units/XEA0002/xea0002_aopen01.sca')
        WaitFor(anim)
        for _, bone in { 'Shell01', 'Shell02', 'Shell03', 'Shell04' } do
            self:HideBone(bone, true)
        end
        anim:PlayAnim('/units/XEA0002/xea0002_aopen02.sca')
    end,

    ControlSatellite = function(self)
        local carrier = self.Carrier
        local currentTarget = false
        local returning = false
        while not self.Dead and not self:BeenDestroyed() do
            if not carrier or carrier.Dead or carrier:BeenDestroyed() or carrier.Army ~= self.Army then
                self:Destroy()
                return
            end
            local center = carrier:GetPosition()
            local pos = self:GetPosition()
            local dx, dz = pos[1] - center[1], pos[3] - center[3]
            local outside = dx * dx + dz * dz > (Radius - 10) * (Radius - 10)
            local best, bestDistance = false, 1e12
            if not outside then
                local candidates = self:GetAIBrain():GetUnitsAroundPoint(Targets, center, Radius - 25, 'Enemy')
                for _, target in candidates do
                    if not target.Dead and not target:BeenDestroyed() then
                        local blip = target:GetBlip(self.Army)
                        if blip and (blip:IsSeenNow(self.Army) or blip:IsOnRadar(self.Army) or blip:IsOnOmni(self.Army)) then
                            local p = target:GetPosition()
                            local x, z = p[1] - pos[1], p[3] - pos[3]
                            local distance = x * x + z * z
                            if distance < bestDistance then best, bestDistance = target, distance end
                        end
                    end
                end
            end
            if best then
                if best ~= currentTarget or returning then
                    IssueClearCommands({ self })
                    IssueAttack({ self }, best)
                    currentTarget, returning = best, false
                end
            else
                -- Follow the carrier when idle or when the boundary is approached.
                local angle = (self.Slot - 1) * math.pi / 2
                local x = math.max(0, math.min(ScenarioInfo.size[1] - 1, center[1] + 12 * math.cos(angle)))
                local z = math.max(0, math.min(ScenarioInfo.size[2] - 1, center[3] + 12 * math.sin(angle)))
                IssueClearCommands({ self })
                IssueMove({ self }, { x, GetSurfaceHeight(x, z), z })
                currentTarget, returning = false, true
            end
            WaitSeconds(1)
        end
    end,
}
TypeClass = UEA0004
