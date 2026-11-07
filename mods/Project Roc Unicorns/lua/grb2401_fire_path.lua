-- An approximation of the ballistic path from the current aim direction and
-- target position. Engine projectile physics and target leading are not exposed.
local function ClipAxis(origin, delta, minimum, maximum, t0, t1)
    if math.abs(delta) < 0.0001 then
        if origin < minimum or origin > maximum then return nil end
        return t0, t1
    end
    local a = (minimum - origin) / delta
    local b = (maximum - origin) / delta
    if a > b then a, b = b, a end
    t0 = math.max(t0, a)
    t1 = math.min(t1, b)
    if t0 > t1 then return nil end
    return t0, t1
end

local function SampleClear(weapon, muzzle)
    if not weapon:WeaponHasTarget() then return true end
    local target = weapon:GetCurrentTargetPos()
    if not target then return true end
    local unit = weapon.unit
    local ox, oy, oz = unit:GetPositionXYZ(muzzle)
    local dx, dy, dz = target[1] - ox, target[2] - oy, target[3] - oz
    local distance = math.sqrt(dx * dx + dz * dz)
    if distance < 4 then return true end
    local vx, vy, vz = unit:GetBoneDirection('Aim_Muzzle')
    if not vx or not vy or not vz then return true end
    local horizontal = math.sqrt(vx * vx + vz * vz)
    if horizontal < 0.01 then return true end
    -- Before the aim manipulator converges, do not interpret the wrong direction
    -- as an actual blocked ballistic solution.
    if (dx * vx + dz * vz) / (distance * horizontal) < 0.9 then return true end
    local slope = vy / horizontal
    local bend = dy - distance * slope
    if bend >= 0 then return true end
    local function Height(t)
        return oy + distance * slope * t + bend * t * t
    end
    -- Half-unit terrain samples, excluding muzzle and the target endpoint.
    local steps = math.ceil(distance * 2)
    for i = 2, steps - 4 do
        local t = i / steps
        local x, z = ox + dx * t, oz + dz * t
        if GetTerrainHeight(x, z) > Height(t) + .05 then return false end
    end

    -- Only presently visible hostile units: allied units do not collide with
    -- this weapon, and unseen units must not leak hidden information.
    local units = GetUnitsInRect(math.min(ox, target[1]) - 12, math.min(oz, target[3]) - 12,
                                 math.max(ox, target[1]) + 12, math.max(oz, target[3]) + 12) or {}
    local current = weapon:GetCurrentTarget()
    if current and current.GetSource then current = current:GetSource() end
    for _, other in units do
        if other ~= unit and other ~= current and not other.Dead and not other:BeenDestroyed()
            and not IsAlly(unit.Army, other.Army)
            and EntityCategoryContains(categories.ALLUNITS - categories.AIR - categories.UNTARGETABLE, other) then
            local blip = other:GetBlip(unit.Army)
            if blip and blip:IsSeenNow(unit.Army) then
                local box = other:GetCollisionExtents()
                if box and box.Min and box.Max then
                    local a, b = box.Min, box.Max
                    local lo, hi = ClipAxis(ox, dx, a[1], b[1], 1 / distance, 1 - 2 / distance)
                    if lo then lo, hi = ClipAxis(oz, dz, a[3], b[3], lo, hi) end
                    if lo then
                        local y0, y1 = Height(lo), Height(hi)
                        local ymin, ymax = math.min(y0, y1), math.max(y0, y1)
                        local apex = -distance * slope / (2 * bend)
                        if apex > lo and apex < hi then ymax = math.max(ymax, Height(apex)) end
                        if ymax >= a[2] and ymin <= b[2] then return false end
                    end
                end
            end
        end
    end
    return true
end

function IsClear(weapon, muzzle)
    return SampleClear(weapon, muzzle)
end
