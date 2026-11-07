# NSB2201 materials

On 7 November 2026 the existing Crystal Spire received a darker Aeon material:
charcoal steel, lighter trim, fine seams and the existing player-colour inlays.
The mesh, UVs and gameplay were not changed. The previous DDS and source maps
are in `archive/before-aeon-material-2026-11-07/`.

`generate.py` contains the reproducible atlas. To rebuild only the material
maps and previews, import it and call `textures()` and `make_previews(UNIT, HERE)`;
running the file directly also rebuilds the mesh. The writer downsamples data
channels independently. Exported DDS mip levels 0, 1, 4 and 7 were inspected.

The local FAF `effects/mesh.fx` Aeon shader uses SpecTeam.A for player colour;
its high-fidelity PBR path maps SpecTeam.R to metallic and raises albedo to a
metal-dependent power. The old R=110 and light albedo could cause a nearly white
surface. The new lower R values and darker colours address that likely cause.
The multi-angle preview reads the exported SCM and DDS but uses approximate
lighting, not the game's Aeon shader. The result has not been checked in a match.
