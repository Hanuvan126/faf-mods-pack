# Local v6 — 2026-10-31

Local changes only; not published.

- Dush’Nai: 12,000 mass; TECH3 instead of EXPERIMENTAL, available to T3 engineers in their T3 construction tab. Existing HP, energy cost, build time, weapons and accepted animation remain unchanged.
- Massive movement: additional native 6x6 hover footprint with IgnoreStructures, matching the structure-ignore navigation flag used by large native units. This changes pathing, not stomping damage. Existing small hover profiles are untouched.
- Vothuun GGA2401 disabled: unit, both icons and source assets moved to F:/FAF-Development/disabled-units/GGA2401_Vothuun_2026-10-31. RESTORE.txt and SHA256 manifest preserve restoration instructions and all 135 original files.
- Vael-Itha: standard Seraphim tarmac, 6.4 x 6.4.
- Both units: separate damaged static wreck models, two LODs each, soot textures, native reclaimable Wreckage props. Existing reclaim multipliers and normal engine death/overkill rules retained.

Validation: Lua blueprint loading, native custom-wreck creation branch, SCM layout/indices/normals, DDS textures, archive hashes and unchanged accepted runtime files checked. No new FAF match has been run; test movement through buildings, T3 build menu, construction decal and destruction/reclaim in game.

Installation: extract Project Roc Unicorns from the runtime ZIP into the FAF Mods directory, replacing the old mod folder entirely (merging leaves the disabled Vothuun files behind). Keep any personal changes backed up first.
