Current installed version: parts-v2/README.md. Measurements below describe the preceding stage.

# Sha’Veyr optimization — 2026-11-07

LOD0: 4601 vertices, 6498 triangles, 6 bones (previous 25334 / 49860 / 6).
LOD1: 3399 vertices, 4497 triangles, 6 bones (previous 10270 / 19916 / 6).
Three shared 512x512 DXT5 textures with complete independent-channel mipmaps: 1,049,040 bytes total (~1 MiB), previously ~4 MiB. Shared by both LODs, count once. Seraphim shader: team mask remains in Albedo.A; packed normal channels preserved.

All six bones, bind transforms, local transforms, parents and names retained. Blueprint, scripts, attack behavior, build footprint, tarmac and wreck geometry unchanged. Existing wreck referencing these same material filenames receives the resized maps too.

LOD0 preserves source UVs with decimation; distant mesh also decimated retaining source UVs; the 600-triangle remesh was rejected for UV distortion. Fine rims/details are reduced in far LOD. No in-game animation/LOD test performed. Actual exported SCM renders and binary validation performed.

For reproduction, extract original-inputs.zip to work (work/original). Run Blender 4.5.3 optimize_shaveyr.py, Python texture_shaveyr.py, Python validate_shaveyr.py, Blender render_shaveyr_opt.py. Python requires numpy/Pillow. SHAVEYR_OPT_WORK overrides work. Results go to work/runtime; installation is separate. Blend stores geometry, not a full animation rig. The ZIP also preserves original gameplay files for rollback. Do not extract old .bp files anywhere inside a live mod.

A 2500-triangle direct decimation also caused unacceptable collapsed detail. Final distant mesh uses 4497 triangles. Further large reduction requires manual topology/ornament cleanup rather than automatic collapse.
