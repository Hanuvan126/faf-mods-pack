-- M28AI v328 divides by Physics.MaxSpeed when estimating missile arrival.
-- Some non-missile projectiles fired by SILO structures use MaxSpeed = 0;
-- skip the missile dodge for those projectiles instead of waiting indefinitely.
do
    local OriginalKeepUnitsAway = KeepUnitsAwayFromNukeOrTMLTarget

    function KeepUnitsAwayFromNukeOrTMLTarget(projectile, launcher, team, enemyNuke)
        if projectile and not projectile:BeenDestroyed() then
            local blueprint = projectile.Blueprint
            local physics = blueprint and blueprint.Physics
            local speed = physics and physics.MaxSpeed
            if type(speed) == 'number' and speed <= 0 then
                return
            end
        end

        return OriginalKeepUnitsAway(projectile, launcher, team, enemyNuke)
    end
end
