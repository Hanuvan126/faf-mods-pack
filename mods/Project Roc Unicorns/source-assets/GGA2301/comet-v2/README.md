# Ishal-Thar / DushNai — local revision 2026-11-07

Installed in the existing local mod and repository; no GitHub publication.
Ishal-Thar GGA2301: range 80, one alternating shot every 0.6 seconds, projectile velocity 45,
ball diameter 0.22 (previously 0.11), stationary world-space smoke particles with 0.32 s lifetime.
Damage and costs unchanged. Expected raw DPS is halved by the requested interval change.
Team pattern line widths doubled; symmetric filled regions follow the two annotated drawings.
Seraphim shader retained with metallic team surfaces and reduced emissive washout.
DushNai base metal lightened selectively; team masks and fixed purple energy unaffected.

Death fix: wreck now retains the six-bone skeleton used by native FAF wreck-smoke effects.
Old one-bone wreck caused an invalid bone exception before Unit:Destroy and left a blocking unit.
Display.Mesh LODs are also supplied inline for native Seraphim build effects and tarmac cutoff logic.
Removed GGA2401 is excluded by the blueprints hook.

IMPORTANT: FAF recursively loads *.bp in mod directories, including source-assets archives!
All archived/source blueprints were renamed *.bp.source, reversibly, in BOTH installations.
The exact rename manifest and pre-change ZIP backups are beside this file.
Do not restore archived *.bp under an active mod directory. The working export/validation folder
is source/ HERE, outside the mod. The patch ZIP contains runtime files only. On another computer,
old archived blueprints also need disabling; copying the ZIP alone does not remove existing archives.

Build source: source/IshalThar_v10.blend; export_blender.py -> build_assets.py -> update_blend.py.
Export starts from approved v09, doubles lines; build generates filled masks and game assets.
validate.py and test_regressions.py cover Lua syntax, alternation, walls/terrain, native wreck-effect
regression, disabled build icon blueprint, resources, mesh bounds, settings and texture masks.
Tested with real files and mocked engine calls; NOT verified in a running FAF match.
Start a NEW match. Test build, alternating fire, smoke, death, reclaim and rebuilding on the same spot.
Existing units from an already-running match cannot be repaired by replacing files.

Active authoring workspace: F:/FAF-Development/outputs/IshalThar_Game_Comet_v2/source
