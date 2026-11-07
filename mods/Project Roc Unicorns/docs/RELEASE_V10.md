# Dush’Nai / Vael-Itha v10 — 2026-11-02

Cumulative changes since v5:
- Dush’Nai costs 12000 mass, appears in TECH3 construction, and uses an isolated 6x6 hover IgnoreStructures footprint.
- Vothuun GGA2401 is disabled. Its archived files were later removed from the workspace.
- Vael-Itha receives a Seraphim tarmac, thin selection outline, single-surface luminous ring bores, exposed ring ornament and revised team-color patterns.
- Both units have custom reclaimable damaged wrecks. Their attachment bone counts match the live units so native wreck smoke cannot abort death cleanup.
- v10 replaces only the three lower foundation petal patterns with the latest artist sketch. Upper petals and gondola ornament remain as in v9.

Validation: exported SCM layout/index bounds, unchanged rig, 768 bore rays and native Lua death cleanup regression passed. Runtime ZIP verified against working files. This build has not been verified in a new FAF match.

Installation: replace the complete old Project Roc Unicorns mod folder with the folder from the runtime ZIP. Do not merge old files: that retains disabled GGA2401. Restart the match to load updated assets.

The six-legged Sha’Thuum study is not included as a playable unit.
