# Ishal-Thar — twin comet replacement, local build

Replaces GGA2301 in Project Roc Unicorns. Vael-Itha / GGA2404 is not changed.
Footprint 1x1, SkirtSize 2x2 and offsets -0.5 match stock XSB2301 T2 point defense.
T3 technology, 2000 mass / 17600 energy, 6500 HP and range 60 retained.
New weapon: one shot every 0.3 s, alternating muzzles, velocity 85,
130 damage per shot, 0.35 splash radius, no friendly damage. Initial balance for testing.
Dark metallic model, team-color geometric inlays, fixed white muzzle rings.
Native aiming/recoil; old prism animation references removed. Original files retained in backup.
Stock Seraphim tarmac (Tar6x, 6.4) and own nonblocking reclaimed wreck.
Straight terrain/wall clearance checks, visible/radar-known alternate-target selection,
physical projectile collisions including friendly units/walls. A shot above a low wall is allowed.

Installed by copying ONLY manifest files into the existing mod. Other units untouched.
Start a NEW match to reload blueprint and script changes. Enable Project Roc Unicorns.
Test: build next to stock T2 PD; alternate shots on a visible target; a ridge or tall wall
in the fire line; a second unobstructed enemy; hold fire; kill and reclaim then rebuild.
Lua, geometry, resources and simulated firing/clearance tests passed. Not tested in a running FAF match.
No GitHub publication performed.

Authoritative editable Lua/blueprints are under comet-v1/runtime; build_runtime.py was an initial
scaffold, followed by ready-state recovery and custom wreck corrections. Do not regenerate it blindly.
export_blender.py and pack_assets.py produce geometry/materials; source model is v09.
