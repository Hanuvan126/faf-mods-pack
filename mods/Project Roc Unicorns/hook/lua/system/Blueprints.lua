local FAFModBlueprints = ModBlueprints

function ModBlueprints(all_blueprints)
    FAFModBlueprints(all_blueprints)

    if all_blueprints.Unit then
        all_blueprints.Unit.xsb1104 = nil
        -- Keep Vothuun disabled even if an old blueprint remains in a source
        -- archive or an installation updated by merging folders.
        all_blueprints.Unit.gga2401 = nil
    end
end
