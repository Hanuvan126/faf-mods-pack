local Base = import('/lua/aeonunits.lua').AAirUnit
local EnemyTargets = (categories.LAND + categories.AIR + categories.STRUCTURE) - categories.UNTARGETABLE
local ExplosionEffects = import('/lua/effecttemplates.lua').CMobileBeetleExplosion

NEA0001 = ClassUnit(Base) {
    OnCreate = function(self)
        Base.OnCreate(self)
        self:SetUnSelectable(true)
        self.Trash:Add(CreateAttachedEmitter(self, 0, self.Army,
            '/effects/emitters/zapper_electricity_01_emit.bp'):ScaleEmitter(2))
    end,

    StartSwarm = function(self, carrier, slot)
        self.Carrier = carrier
        self.SwarmSlot = slot
        self:ForkThread(self.SwarmThread)
    end,

    FindSwarmTarget = function(self, carrier)
        local brain = self:GetAIBrain()
        local candidates = brain:GetUnitsAroundPoint(EnemyTargets, carrier:GetPosition(), 35, 'Enemy')
        local origin = self:GetPosition()
        local best, bestDist = nil, 1000000
        for _, target in candidates do
            if not target.Dead and not target:BeenDestroyed() then
                local blip = target:GetBlip(self.Army)
                if blip and (blip:IsSeenNow(self.Army) or blip:IsOnRadar(self.Army) or blip:IsOnOmni(self.Army)) then
                    local p = target:GetPosition()
                    local dx, dz = p[1] - origin[1], p[3] - origin[3]
                    local dist = dx * dx + dz * dz
                    if dist < bestDist then best, bestDist = target, dist end
                end
            end
        end
        return best
    end,

    SwarmThread = function(self)
        local carrier = self.Carrier
        local slot = self.SwarmSlot
        local radius = 3 + (slot - 1) * 9 / 19
        local phase = (slot - 1) * 2 * math.pi / 20
        local target = nil
        while not self.Dead and not self:BeenDestroyed() do
            if not carrier or carrier.Dead or carrier:BeenDestroyed() or carrier.Army ~= self.Army then
                self:Destroy()
                return
            end
            local center = carrier:GetPosition()
            if target and not target.Dead and not target:BeenDestroyed() then
                local p = target:GetPosition()
                local dx, dz = p[1] - center[1], p[3] - center[3]
                local blip = target:GetBlip(self.Army)
                if dx * dx + dz * dz > 45 * 45 or not blip or
                    not (blip:IsSeenNow(self.Army) or blip:IsOnRadar(self.Army) or blip:IsOnOmni(self.Army)) then
                    target = nil
                end
            else
                target = nil
            end
            if not target then target = self:FindSwarmTarget(carrier) end
            if target then
                local p = target:GetPosition()
                local me = self:GetPosition()
                local dx, dy, dz = p[1] - me[1], p[2] - me[2], p[3] - me[3]
                -- Large structures can prevent the drone from reaching their
                -- centre. Detonate near their collision footprint instead.
                local proximity = 3
                local height = 3
                if EntityCategoryContains(categories.STRUCTURE, target) then
                    local bp = target:GetBlueprint()
                    proximity = math.max(bp.SizeX or 0, bp.SizeZ or 0) * 0.5 + 3
                    height = (bp.SizeY or 0) * 0.5 + 3
                end
                if dx * dx + dz * dz <= proximity * proximity and math.abs(dy) <= height then
                    DamageArea(self, p, 3, 2000, 'Normal', false)
                    for _, effect in ExplosionEffects do
                        CreateEmitterAtBone(self, -2, self.Army, effect):ScaleEmitter(1.5)
                    end
                    CreateLightParticle(self, -1, self.Army, 8, 20, 'glow_03', 'ramp_antimatter_02')
                    self:Destroy()
                    return
                end
                self:SetElevation(math.max(1, p[2] - GetSurfaceHeight(p[1], p[3])))
                IssueClearCommands({ self })
                IssueMove({ self }, p)
                WaitTicks(5)
            else
                self:SetElevation(5)
                -- Give the navigator time to start moving and aim ahead on
                -- the orbit instead of repeatedly issuing nearly identical goals.
                phase = phase + 2.4 / radius
                local goalPhase = phase + math.pi / 3
                local x = center[1] + radius * math.cos(goalPhase)
                local z = center[3] + radius * math.sin(goalPhase)
                x = math.max(0, math.min(ScenarioInfo.size[1] - 1, x))
                z = math.max(0, math.min(ScenarioInfo.size[2] - 1, z))
                IssueClearCommands({ self })
                IssueMove({ self }, { x, GetSurfaceHeight(x, z), z })
                WaitTicks(10)
            end
        end
    end,
}
TypeClass = NEA0001

