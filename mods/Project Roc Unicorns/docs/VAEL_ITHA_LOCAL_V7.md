Local v7: Vael-Itha selection/ring repair. No GitHub publication.
SelectionThickness 1.9 -> 0.25; selection dimensions unchanged.
Removed duplicated bore walls from both hulls and ring shells. Single continuous army-colored cylindrical wall per ring, original 0.385 radius; protected from LOD decimation. Both native meshes retain exact skeleton/bind data. All other runtime files are unchanged from the prior local v6 snapshot.
Actual native SCM ray checks: 768 rays total, each intersects one bore surface; baseline sample intersects multiple layers. Blueprint loads with Lua. No new FAF match has been run. Restart the game and verify selection and rings at different zoom levels.
Pattern sheets are actual geometric projections for markup, plus a 360-degree cylindrical wall sheet. They are not a unique baked UV map: the model uses shared material tiles and geometric inlays. PNG and editable SVG included. Existing patterns remain unchanged.
Install: replace the entire Project Roc Unicorns folder in FAF Mods with the folder from Project_Roc_Unicorns_LOCAL_v7.zip. Keep a backup of any personal changes. Disabled Vothuun remains disabled, previous T3 tank changes retained.
