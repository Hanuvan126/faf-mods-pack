local CWalkingLandUnit = import('/lua/cybranunits.lua').CWalkingLandUnit
local CIFArtilleryWeapon = import('/lua/cybranweapons.lua').CIFArtilleryWeapon
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
    EnsureGunManips = function(self)
        if self.GunSlides then return end
        self.GunSlides = {}
        self.GunRotators = {}
        self.GunRecoilEpoch = { Left = 0, Right = 0 }
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

    AnimateGunReload = function(self, epoch, rate)
        WaitTicks(3)
        if self.Dead or self:BeenDestroyed() or self.GunReloadEpoch ~= epoch then return end
        for _, side in { 'Left', 'Right' } do
            self.GunRotators[side]:SetSpeed(24)
            self.GunRotators[side]:SetGoal(18)
        end
        WaitTicks(9)
        if self.Dead or self:BeenDestroyed() or self.GunReloadEpoch ~= epoch then return end
        local holdTicks = math.max(0, math.floor((1 / math.max(rate, 0.001) - 2.9) * 10))
        if holdTicks > 0 then WaitTicks(holdTicks) end
        if self.Dead or self:BeenDestroyed() or self.GunReloadEpoch ~= epoch then return end
        for _, side in { 'Left', 'Right' } do
            self.GunRotators[side]:SetSpeed(18)
            self.GunRotators[side]:SetGoal(0)
        end
    end,

    Weapons = {
        MainGun = ClassWeapon(CIFArtilleryWeapon) {
            CreateProjectileAtMuzzle = function(self, muzzle)
                local projectile = CIFArtilleryWeapon.CreateProjectileAtMuzzle(self, muzzle)
                if projectile and not projectile:BeenDestroyed() then
                    local unit = self.unit
                    unit:EnsureGunManips()
                    local side = muzzle == 'Muzzle_Left' and 'Left' or 'Right'
                    unit.GunRecoilEpoch[side] = unit.GunRecoilEpoch[side] + 1
                    unit:ForkThread(unit.AnimateGunRecoil, side, unit.GunRecoilEpoch[side])
                    if side == 'Right' then
                        unit.GunReloadEpoch = (unit.GunReloadEpoch or 0) + 1
                        unit:ForkThread(unit.AnimateGunReload, unit.GunReloadEpoch, self:GetWeaponRoF())
                    end
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

