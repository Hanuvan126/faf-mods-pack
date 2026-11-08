# Vael-Itha lightweight resources — 2026-11-07

Installed locally only. Source authoring blend remains unchanged.
Preserved 12 bone records (names, parents, bind matrices, translations, rotations) exactly from the working runtime SCM. Unit blueprint, script, weapons, balance, tarmac and wreck definition are unchanged.

Per-object simplification preserves the gondola apertures. The metal ring and luminous bore use matching uniform angular samples: 32 segments near, 16 far. Mirrored face winding and UVs are retained. Near engraving ribbons are projected back onto the reduced receiving skin. Far LOD omits the tiny engraved ribbons and retains the metal silhouette, luminous bore and electrical field.

Textures: three 512x256 DXT5 atlases with ten mip levels, independent RGBA channel filtering. Albedo.A remains the team mask; packed normals remain G/A. All textures total 524784 bytes (0.50 MiB).

Rebuild: Blender background optimize_vael.py; Python/Pillow texture_vael.py; Python/numpy/Pillow validate_vael.py then render_vael_final.py. Outputs go to repository outputs/VaelItha_Optimization. Render utility comes from this unit source folder. Copy only validated SCM/DDS files to runtime. Never run legacy full generators over this optimization unintentionally.

Rollback: before.zip holds the original runtime directory. Keep ZIP compressed: old blueprints must not be extracted elsewhere in the live mod.

Validation: binary indices, finite/unit normals, exact skeleton records, bounding extents, DDS dimensions/format/mips and exported-SCM renders. This is not an in-game verification. Compare charging, close/open movement, aiming and LOD transition in a new FAF match before publishing.
