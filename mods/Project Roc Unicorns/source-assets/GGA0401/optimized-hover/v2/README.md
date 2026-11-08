# Dush’Nai optimization v2 — 2026-11-07

LOD0: 3852 exported vertices, 4698 triangles, 16 bones.
LOD1: 427 exported vertices, 458 triangles, 16 bones.
Textures: LOD0 3 x 1024x512, LOD1 3 x 256x128, DXT5 with full independent-channel mip chains. Total DDS size 2,229,216 bytes = 2.126 MiB (under 3 MiB).

Original input archive: ../optimization-inputs.zip. Extract to work/ so that work/original exists; run Blender optimize_dush_v2.py, Python texture_dush_v2.py, Python validate_dush_v2.py, Blender render_dush_v2.py. Override work with DUSH_OPT_WORK if needed. Scripts write runtime candidates, not the installed unit. Blender 4.5.3; Python numpy/Pillow. Blend is intermediate geometry, not a rigged animation-authoring scene.

before-v2.zip restores previous unit directory. Original pre-optimization backup remains ../before-optimization.zip. Mesh blueprint still uses 240/700 cutoffs, two LODs. Gameplay and charge effect Lua unchanged. Existing unused old assets retained; wreck still references original normal map. Consequently whole folder size is not live-model resource size.

Validated SCM indices/normals/bones/symmetry, geometry budgets, DDS mip chains and <3 MiB total texture size. Rendered actual exported SCM. In-game animation and LOD transition test pending; not uploaded.

Hull rebuilt as a continuous surface before decimation to eliminate intersecting layers; small edge details are softened. Gondolas receive more geometry than hull per source triangle. Smooth normals recalculated from final topology.
