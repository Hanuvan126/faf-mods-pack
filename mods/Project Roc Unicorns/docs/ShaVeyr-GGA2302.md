# Sha’Veyr / Ishal-Thar: separate T3 defences

GGA2301: restored original Ishal-Thar beam turret from the pre-comet backup, including model,
materials, activate/idle animations and original icon. Beam statistics unchanged (range 60).
Inline Display.Mesh added for native build effects. Fixed an extra self argument in the archived
animation ForkThread callback; Unit:ForkThread already supplies the unit.

GGA2302: independent Sha’Veyr twin comet turret. Current approved live geometry/materials/icon,
range 80, shot every 0.6 s, projectile speed 45 and all other existing balance retained.
Independent GGP2302 projectile and sha_veyr particle assets/fire-path helper. Both units are T3
and available to T3 engineers/commanders through the existing build categories.
GGA2401 remains disabled; GGA2404 and DushNai not changed by this revision.

New wreck: 38 armour fragments / broken edges / scattered shards / severed ribs; 8243 vertices,
8729 triangles. Charred dedicated Unit-shader maps, zero emissive/team channels. Six bones match
live skeleton count for native wreck smoke effects. Bound geometry stays on root; prop nonblocking.
Images are Blender renders of the exported SCM with approximate charcoal materials, not game captures.
Editable live and wreck scenes: source-assets/GGA2302/ShaVeyr.blend and ShaVeyr_wreck.blend.

Installed runtime files in both the working repository and the local game Mods directory.
Local backups, hashes and preview renders are retained outside the repository in the ShaVeyr_GGA2302 output folder.
Validated Lua/BP syntax, resources, independent IDs/paths, T3 categories, mesh bounds and skeletons.
In-game match NOT run. Start a NEW match: check both build icons, build both, verify old beam/new
alternating comets, destroy ShaVeyr, reclaim wreck and rebuild at the same location.
