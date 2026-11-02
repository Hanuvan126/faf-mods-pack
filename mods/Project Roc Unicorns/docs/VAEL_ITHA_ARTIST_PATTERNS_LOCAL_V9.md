LOCAL v9 — Vael-Itha artist patterns, 2026-11-02

Applied user petal/gondola sketches. All six petals (three primary and three secondary) retain their original motifs, with a perimeter inlay and 31 transverse hatch segments per petal. Hatches keep at least 0.035 model-unit centerline clearance from existing motifs. Outer gondola patterns replaced by clean circles, node connections and nested arrows; the two gondolas are mirrored. Inner lighting/panels remain and gain luminous perimeter contours. All new strokes use existing army-color material tiles; metal maps unchanged.

Ring/crown ornament geometry is preserved (63 checked objects). Hull material underneath ring-face engraving is recessed so the whole face is exposed; functional ring radius 0.385 and the single luminous bore are retained. Both SCM LODs preserve the complete skeleton. Only two live turret SCM files changed in the runtime; all gameplay, DDS textures, icons, tank, selection correction and v8 death-cleanup skeletons are unchanged.

Validation: both native LODs pass 436 ring-face visibility probes each and 192 inner-bore rays per ring. Exterior gondola pattern visibility sampled 356 times per LOD without obstruction. Hatching clearance checked in authoring projection. Native death cleanup regression passed for turret and tank. No post-change FAF match run. Native SCM previews approximate game shading and do not include particles.

Install by replacing Project Roc Unicorns in FAF Mods with the complete folder from Project_Roc_Unicorns_LOCAL_v9.zip, then restart the game for a new test. Keep personal changes backed up. Everything is local; no upload to GitHub.

Source: apply_artist_patterns.py (also called by generate_turret.py); build_artist_revision.py; refine_inner_contour.py; check_artist_revision.py; preview_artist_revision.py. Artist originals stored as petal_artist_reference_2026-11-02.png and gondola_artist_reference_2026-11-02.png. Crown means the central upper part of the foundation under the floating gun.
