# Sha'Veyr burst revision — 2026-11-08

Runtime tuning, no mesh density increase. Live model scale 0.4 -> 0.8, footprint 1 -> 2, construction skirt 2 -> 4 with offsets -1.5. Selection, collision, health bar, tarmac and wreck bounds follow the enlarged tower. Native wreck creation applies the unit UniformScale.

One native rack, MuzzleSalvoSize 5, MuzzleSalvoDelay 0.2: shot times 0, .2, .4, .6, .8. Native firing state waits after the fifth shot too, then three seconds of rack reload. Next burst starts at 4.0 seconds. Alternate muzzle only in OnWeaponFired (once per salvo). RoF .25 matches this four-second cycle. Native rack recoil is zero because FAF rejects nonzero recoil with delayed muzzle salvos; a short independent slider pulse supplies per-shot recoil. Each projectile release retains terrain/wall checks and aborts the rest of a blocked burst.

Head visual scale x4, near-white albedo with gentle variation, stable emission, no pulsing point light. Purple stationary stardust trail unchanged. Initial/max/muzzle speed 45 -> 22.5; fallback lifetime 8 seconds. Collision dimensions .22 -> .88. Damage 130 per projectile, range 80 unchanged; radius 2 and randomness .6 (empirically about radius 4 at range 80). No extra scripted damage. Five hits total 650 damage before splash; nominal sustained direct DPS 162.5, previously about 216.7.

Four short impact emitters: white flash, expanding purple ground ring, purple mist and sparks. Existing stock/mod textures referenced, no new high-resolution assets. Lifetime bounded; particles use world-space velocity. Visual tuning requires FAF testing.

Validation uses actual installed FAF native firing/reload Main functions in Lua with mocked engine APIs. Ten-shot alternation/timing and obstruction abort pass. All changed Lua/blueprints compile; effect texture and custom asset paths resolve. Does not prove live-engine appearance, targeting, slider direction or particle timing. Test in a fresh match.

before.zip is the pre-edit runtime backup, kept compressed. Source scripts are one-shot migration tools; do not re-run against already patched files. Restore the backed-up files first to rebuild, run from this directory, then revise_shaveyr_burst.py, shade_shaveyr_burst.py and verify_shaveyr_burst.py. Scripts use local F: repository and Python library locations.
