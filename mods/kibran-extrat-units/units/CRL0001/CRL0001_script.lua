local Unit = import('/lua/sim/Unit.lua').Unit

CRL0001 = ClassUnit(Unit) {
    OnCreate = function(self)
        Unit.OnCreate(self)
        self:HideBone(0, true)
        self:SetUnSelectable(true)
        self:SetDoNotTarget(true)
        self:SetReclaimable(false)
        self:SetCapturable(false)
        self:SetCanTakeDamage(false)
        self:SetCollisionShape('None')
    end,
}
TypeClass = CRL0001
