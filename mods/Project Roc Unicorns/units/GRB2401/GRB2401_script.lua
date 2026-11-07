local CWalkingLandUnit = import('/lua/cybranunits.lua').CWalkingLandUnit
local CIFArtilleryWeapon = import('/lua/cybranweapons.lua').CIFArtilleryWeapon
local FirePath = import('/mods/Project Roc Unicorns/lua/grb2401_fire_path.lua')
GRB2401 = ClassUnit(CWalkingLandUnit) {
    -- Match the stock Megalith's directional walking animation behavior.
    OnMotionHorzEventChange = function(self, new, old)
        CWalkingLandUnit.OnMotionHorzEventChange(self, new, old)
        if old == 'Stopped' then
            local display = self:GetBlueprint().Display
            if display.AnimationWalk and self.Animator then
                self.Animator:SetDirectionalAnim(true)
                self.Animator:SetRate(display.AnimationWalkRate)
            end
        end
    end,
    OnKilled = function(self, instigator, damageType, overkillRatio)
        -- Stop live walking and firing controllers before the independent death animation.
        if self.Animator then
            self.Animator:Destroy()
            self.Animator = nil
        end
        if self.GunRotators then
            for _, side in { 'Left', 'Right' } do
                self.GunRotators[side]:Destroy()
                self.GunSlides[side]:Destroy()
            end
        end
        CWalkingLandUnit.OnKilled(self, instigator, damageType, overkillRatio)
    end,

    OnAnimCollision = function(self, bone, x, y, z)
        if not self.Dead then
            CWalkingLandUnit.OnAnimCollision(self, bone, x, y, z)
        end
    end,

    -- The native death weapon calls this once. Impact occurs as the hull
    -- reaches the ground, 2.4 seconds into the three-second collapse.
    DeathWeaponDamageThread = function(self, radius, damage, damageType, damageFriendly)
        WaitTicks(24)
        if not self:BeenDestroyed() then
            DamageArea(self, self:GetPosition(), radius, damage, damageType, damageFriendly)
            DamageArea(self, self:GetPosition(), radius, 1, 'TreeForce', false)
        end
    end,

    -- Preserve the native overkill / build-completion rules for creating
    -- a wreck, but give a created full-health wreck exactly 15,000 mass.
    CreateWreckageProp = function(self, overkillRatio)
        local wreck = CWalkingLandUnit.CreateWreckageProp(self, overkillRatio)
        if wreck and not wreck:BeenDestroyed() then
            wreck:SetMaxReclaimValues(wreck.TimeReclaim, 15000, 0)
        end
        return wreck
    end,

    EnsureGunManips = function(self)
        if self.GunSlides then return end
        self.GunSlides = {}
        self.GunRotators = {}
        self.GunRecoilEpoch = { Left = 0, Right = 0 }
        self.GunReloadEpoch = { Left = 0, Right = 0 }
        for _, side in { 'Left', 'Right' } do
            local slide = CreateSlider(self, 'Recoil_' .. side)
            slide:SetWorldUnits(false)
            slide:SetSpeed(-1)
            self.Trash:Add(slide)
            self.GunSlides[side] = slide
            local rotation = CreateRotator(self, 'Reload_' .. side, 'x')
            self.Trash:Add(rotation)
            self.GunRotators[side] = rotation
        end
    end,

    -- The callback runs after projectile creation and never blocks the salvo.
    AnimateGunRecoil = function(self, side, epoch)
        local slide = self.GunSlides[side]
        slide:SetSpeed(-1)
        slide:SetGoal(0, 0, -2.8)
        WaitTicks(1)
        if self.Dead or self:BeenDestroyed() or self.GunRecoilEpoch[side] ~= epoch then return end
        slide:SetSpeed(4)
        slide:SetGoal(0, 0, 0)
    end,

    AnimateGunReload = function(self, side, epoch, rate)
        -- Each barrel starts lowering immediately after its own projectile.
        local rotation = self.GunRotators[side]
        rotation:SetSpeed(24)
        rotation:SetGoal(12)
        WaitTicks(5)
        if self.Dead or self:BeenDestroyed() or self.GunReloadEpoch[side] ~= epoch then return end
        -- Allow time to return before this barrel's next nominal shot.
        local holdTicks = math.max(0, math.floor((1 / math.max(rate, 0.001) - 1.5) * 10))
        if holdTicks > 0 then WaitTicks(holdTicks) end
        if self.Dead or self:BeenDestroyed() or self.GunReloadEpoch[side] ~= epoch then return end
        rotation:SetSpeed(18)
        rotation:SetGoal(0)
    end,

    Weapons = {
        MainGun = ClassWeapon(CIFArtilleryWeapon) {
            -- Check the approximate ballistic corridor before starting a shot;
            -- aiming remains enabled while waiting for a clear route.
            CanWeaponFire = function(self)
                if not CIFArtilleryWeapon.CanWeaponFire(self) then return false end
                local tick = GetGameTick()
                if not self.PathCheckTick or tick >= self.PathCheckTick then
                    self.PathClear = FirePath.IsClear(self, 'Aim_Muzzle')
                    self.PathCheckTick = tick + 5
                end
                return self.PathClear
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                if FirePath.IsClear(self, muzzle) then
                    CIFArtilleryWeapon.PlayFxMuzzleSequence(self, muzzle)
                end
            end,
            CreateProjectileAtMuzzle = function(self, muzzle)
                -- Recheck because the shooter or obstacle may move between
                -- the two shots. A blocked shot creates no projectile.
                if not FirePath.IsClear(self, muzzle) then return nil end
                local projectile = CIFArtilleryWeapon.CreateProjectileAtMuzzle(self, muzzle)
                if projectile and not projectile:BeenDestroyed() then
                    local unit = self.unit
                    unit:EnsureGunManips()
                    local side = muzzle == 'Muzzle_Left' and 'Left' or 'Right'
                    unit.GunRecoilEpoch[side] = unit.GunRecoilEpoch[side] + 1
                    unit:ForkThread(unit.AnimateGunRecoil, side, unit.GunRecoilEpoch[side])
                    unit.GunReloadEpoch[side] = unit.GunReloadEpoch[side] + 1
                    unit:ForkThread(unit.AnimateGunReload, side, unit.GunReloadEpoch[side], self:GetWeaponRoF())
                end
                return projectile
            end,
            FxMuzzleFlash = {
                '/effects/emitters/cybran_artillery_muzzle_flash_01_emit.bp',
                '/effects/emitters/cybran_artillery_muzzle_flash_02_emit.bp',
                '/effects/emitters/cybran_artillery_muzzle_smoke_01_emit.bp',
            },
        },
    },
}
TypeClass = GRB2401

