-- One additional hover footprint, keeping the stock small-hover profiles intact.
-- Native large amphibious/vehicle footprints use the same IgnoreStructures flag.
SpecFootprints {
    { Name = 'DushNaiWaterLand6x6', SizeX = 6, SizeZ = 6,
      Caps = LAND + WATER, MaxWaterDepth = 5, MinWaterDepth = 0,
      MaxSlope = 0.75, Flags = IgnoreStructures },
}
