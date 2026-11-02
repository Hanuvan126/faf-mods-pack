LOCAL v8 — wreck death cleanup repair

Confirmed in active game_28052177.log: Invalid bone index in CreateEmitterAtBone -> CreateWreckageEffects -> CreateWreckage -> DestroyUnit. Wreckage spawned, then the invalid smoke attachment aborted before destruction of the original building. This left both meshes and the building footprint.

Repair: keep the accepted static WreckRoot geometry and add valid native FX attachment slots. Vael-Itha wrecks now have 12 bones, Dush Nai wrecks 33, matching their live models. All visible vertex and triangle index bytes, materials, reclaim properties and gameplay are unchanged. The shared generator is updated too.

Validation: reproduced pre-fix native smoke error; executed actual installed FAF CreateWreckageEffects and DestroyUnit against strict bone API doubles after repair, both units and both LODs with minimum/maximum/middle random choices. DestroyUnit reaches Destroy after spawning the wreck. This is not a post-fix in-game placement test.

Installation: after finishing the current match, replace the complete Project Roc Unicorns folder in FAF Mods using Project_Roc_Unicorns_LOCAL_v8.zip, restart the game and test in a NEW match. Existing broken entities in the running match are not repaired by changing files. Back up any personal changes first. Current match and installed mod folder were not modified. No GitHub publication.

Game check: destroy Vael-Itha, wait for destruction effects, verify only its damaged wreck remains; reclaim it and build a structure on the same ground. Check Dush Nai destruction too.
