-- Visual-only charge display. Native weapon owns firing and energy consumption.
local Entity = import('/lua/sim/Entity.lua').Entity
local OrbTrails = import('/lua/effecttemplates.lua').SDFExperimentalPhasonProjFXTrails01
local Mesh = '/mods/Project Roc Unicorns/effects/entities/DushNaiCharge/DushNaiCharge_mesh'
local Beams = {
    '/mods/Project Roc Unicorns/effects/emitters/itha_yen_charge_beam_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/itha_yen_charge_core_beam_emit.bp',
}

local function Clear(list)
    for _, effect in ipairs(list or {}) do effect:Destroy() end
end

function UpdateOrb(unit, progress, visible)
    if not visible then
        Clear(unit.VaelOrbFX)
        unit.VaelOrbFX = {}
        return
    end
    if not unit.VaelOrbFX or table.getn(unit.VaelOrbFX) == 0 then
        unit.VaelOrbFX = {}
        for _, path in ipairs(OrbTrails) do
            table.insert(unit.VaelOrbFX, CreateAttachedEmitter(unit.ChargeVisual, -1, unit.Army, path))
        end
    end
    for _, effect in ipairs(unit.VaelOrbFX) do
        effect:ScaleEmitter(.6 * math.max(.05, progress))
    end
end

local function FieldThread(unit)
    local tick = 0
    while not unit.Dead and not unit:BeenDestroyed() and not unit.VaelFXStopped do
        Clear(unit.VaelBeams)
        unit.VaelBeams = {}
        if unit.GunChargeVisible then
            for i = 1, 3 do
                local l = math.mod(tick + i, 3) + 1
                local r = math.mod(tick * 2 + i, 3) + 1
                for index, path in ipairs(Beams) do
                    local beam = AttachBeamEntityToEntity(unit.VaelEndpoints[1][l], -1,
                        unit.VaelEndpoints[2][r], -1, unit.Army, path)
                    if beam then
                        local progress = unit.GondolaOpen or 0
                        beam:SetBeamParam('THICKNESS', index == 2 and (.025 + .04 * progress) or (.10 + .14 * progress))
                        table.insert(unit.VaelBeams, beam)
                    end
                end
            end
        end
        tick = tick + 1
        WaitTicks(1)
    end
    Clear(unit.VaelBeams)
    unit.VaelBeams = {}
end

function Initialize(unit)
    unit.VaelFXStopped = false
    unit.VaelBeams = {}
    unit.VaelOrbFX = {}
    local visual = Entity({Owner = unit})
    visual:SetMesh(Mesh, false)
    visual:SetCollisionShape('None')
    visual:AttachBoneTo(-1, unit, 'Charge')
    visual:SetParentOffset(Vector(0, 0, 0))
    visual:SetVizToFocusPlayer('Always')
    visual:SetVizToAllies('Always')
    visual:SetVizToEnemies('Intel')
    visual:SetVizToNeutrals('Intel')
    visual:SetDrawScale(.000001)
    unit.ChargeVisual = visual
    unit.Trash:Add(visual)
    -- Lightweight anchors follow each sliding gondola; no extra mesh bones.
    unit.VaelEndpoints = {}
    for side, bone in ipairs({'GondolaL', 'GondolaR'}) do
        unit.VaelEndpoints[side] = {}
        for i, offset in ipairs({-.55, 0, .55}) do
            local endpoint = Entity({Owner = unit})
            endpoint:SetCollisionShape('None')
            endpoint:AttachBoneTo(-1, unit, bone)
            endpoint:SetParentOffset(Vector(0, 0, offset))
            unit.Trash:Add(endpoint)
            unit.VaelEndpoints[side][i] = endpoint
        end
    end
    unit:ForkThread(FieldThread)
end

function Stop(unit)
    unit.VaelFXStopped = true
    unit.GunChargeVisible = false
    Clear(unit.VaelBeams)
    Clear(unit.VaelOrbFX)
    unit.VaelBeams = {}
    unit.VaelOrbFX = {}
    local visual = unit.ChargeVisual
    if visual and not visual:BeenDestroyed() then visual:SetDrawScale(.000001) end
end
