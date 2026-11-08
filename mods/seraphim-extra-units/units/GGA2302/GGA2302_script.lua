local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local Cannon = import('/lua/seraphimweapons.lua').SDFOhCannon
local FirePath = import('/mods/seraphim-extra-units/lua/sha_veyr_fire_path.lua')

GGA2302 = ClassUnit(SStructureUnit) {
    Weapons = {
        MainGun = ClassWeapon(Cannon) {
            FxMuzzleFlashScale = 0.70,
            NextMuzzle = 'MuzzleLeft',
            CanWeaponFire = function(self)
                return Cannon.CanWeaponFire(self) and FirePath.IsClear(self, self.NextMuzzle)
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                if FirePath.IsClear(self, self.NextMuzzle) then
                    Cannon.PlayFxMuzzleSequence(self, self.NextMuzzle)
                end
            end,
            CreateProjectileAtMuzzle = function(self, muzzle)
                local actual = self.NextMuzzle
                if not FirePath.IsClear(self, actual) then
                    self.RejectedTarget = self:GetCurrentTarget()
                    self.BlockedOnRelease = true
                    self.HaltFireOrdered = true
                    return nil
                end
                local projectile = Cannon.CreateProjectileAtMuzzle(self, actual)
                if projectile then
                    self.BurstHasFired = true
                    self:ForkThread(self.PulseRecoil)
                end
                return projectile
            end,
            -- Native muzzle salvo holds one barrel for all five shots.
            -- OnWeaponFired runs once per salvo, not once per projectile.
            OnWeaponFired = function(self)
                Cannon.OnWeaponFired(self)
                if self.BurstHasFired then
                    self.NextMuzzle = self.NextMuzzle == 'MuzzleLeft' and 'MuzzleRight' or 'MuzzleLeft'
                    self.BurstHasFired = false
                end
                -- Let native reload finish; ready-state obstruction recovery follows it.
                self.BlockedOnRelease = false
            end,
            PulseRecoil = function(self)
                if self:BeenDestroyed() or self.unit.Dead then return end
                if not self.BurstRecoil then
                    self.BurstRecoil = CreateSlider(self.unit, 'GunRecoil')
                    self.Trash:Add(self.BurstRecoil)
                end
                self.BurstRecoil:SetSpeed(12)
                self.BurstRecoil:SetGoal(0, 0, -0.20)
                WaitTicks(1)
                if self:BeenDestroyed() or self.unit.Dead then return end
                self.BurstRecoil:SetGoal(0, 0, 0)
                self.BurstRecoil:SetSpeed(4)
            end,
            BlockedState = State {
                StateName = 'BlockedState',
                WeaponWantEnabled = false,
                WeaponAimWantEnabled = false,
                Main = function(self)
                    self.unit:SetBusy(false)
                    self.unit:SetWorkProgress(1)
                    local rejected = self.RejectedTarget
                    self.RejectedTarget = nil
                    self:ResetTarget()
                    local target = FirePath.FindClearTarget(self, self.NextMuzzle, rejected)
                    if target then
                        self.ClearTarget = target
                        ChangeState(self, self.ClearTargetState)
                        return
                    end
                    WaitTicks(5)
                    if not self:BeenDestroyed() and not self.unit.Dead then
                        self:ResetTarget()
                        ChangeState(self, self.IdleState)
                    end
                end,
            },
            ClearTargetState = State {
                StateName = 'ClearTargetState',
                WeaponWantEnabled = true,
                WeaponAimWantEnabled = true,
                Main = function(self)
                    local target = self.ClearTarget
                    self.ClearTarget = nil
                    if target and not target.Dead and not target:BeenDestroyed() then
                        self:SetTargetEntity(target)
                    end
                    ChangeState(self, self.RackSalvoFireReadyState)
                end,
            },
            -- Native CanWeaponFire can suppress OnFire entirely. Check while ready
            -- as well, so an obstructed first target cannot monopolize the gun.
            RackSalvoFireReadyState = State(Cannon.RackSalvoFireReadyState) {
                Main = function(self)
                    self.unit:SetBusy(false)
                    self.WeaponCanFire = true
                    while not self:BeenDestroyed() and not self.unit.Dead do
                        WaitTicks(3)
                        if self:WeaponHasTarget() and not FirePath.IsClear(self, self.NextMuzzle) then
                            self.RejectedTarget = self:GetCurrentTarget()
                            ChangeState(self, self.BlockedState)
                            return
                        end
                    end
                end,
            },
            RackSalvoFiringState = State(Cannon.RackSalvoFiringState) {
                Main = function(self)
                    if not self:WeaponHasTarget() then
                        WaitTicks(1)
                        if not self:WeaponHasTarget() then ChangeState(self, self.IdleState); return end
                    end
                    if not FirePath.IsClear(self, self.NextMuzzle) then
                        self.RejectedTarget = self:GetCurrentTarget()
                        ChangeState(self, self.BlockedState)
                        return
                    end
                    Cannon.RackSalvoFiringState.Main(self)
                end,
            },
        },
    },
}
TypeClass = GGA2302
