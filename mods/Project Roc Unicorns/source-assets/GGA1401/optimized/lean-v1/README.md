# Uya-Iava optimization — 2026-11-07

Local runtime update. No gameplay changes or publication.

LOD0: 7,662 vertices / 12,032 triangles (was 43,476 / 25,912).
LOD1: 2,302 vertices / 3,276 triangles.
Three 512x512 DXT5 maps with ten mip levels: 1,049,040 bytes total, down from 4,194,768 bytes. Independent-channel filtering preserves Albedo.A team color and normal G/A data.

Geometry is rebuilt from the existing procedural definitions with fewer angular/profile samples. All petals and all five orbiting/spinning shards are retained. Far LOD omits thin raised conduits and reduces petal cross-sections. UV seams, normal splits and bone assignments remain distinct; duplicate tangent-only vertices are welded with orthonormalized tangents.

The seven bone records are copied exactly from the original runtime mesh. The existing idle SCA, unit blueprint and script are byte-identical. Shield, ambient emitters, economy, tarmac and orbital animation are unchanged.

Rebuild in order: optimize_uya.py, texture_uya.py, validate_uya.py, render_uya_final.py using Python, numpy and Pillow. Helpers are the original reactor_geometry.py and supcom_binary.py in this unit's source folder. Outputs are under repository outputs/UyaIava_Optimization. Validate and inspect before copying SCM/DDS into runtime. The original full-resolution generator will overwrite optimized resources if run directly.

before.zip contains the original runtime files. Keep the backup compressed; do not extract old blueprints into the live mod. Original procedural sources are unchanged.

Verified: SCM indices/bounds/normals, exact skeleton, DDS dimensions/format/mip count, rendered exported SCM at front/game angles and four poses of the unchanged SCA. Not tested in a running FAF match; live shield and particle emitters are not represented by these renders.
