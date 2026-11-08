local PreviousModBlueprints = ModBlueprints
function ModBlueprints(all_blueprints)
    PreviousModBlueprints(all_blueprints)
    if all_blueprints.Unit then all_blueprints.Unit.gga0404 = nil end
end
