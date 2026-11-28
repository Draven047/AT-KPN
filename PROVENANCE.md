# Provenance

Source family: Baloo 2, Ek Type, SIL Open Font License 1.1.

- Repository: https://github.com/EkType/Baloo2
- Release: 1.640
- Commit: `3aa20453e9f86f3f21b17e9a585f9d89181b2c17`
- Original binary archive: https://github.com/EkType/Baloo2/releases/download/1.640/Baloo2_1.640.zip
- Archive hashes: `sources/upstream/provenance.json` and `sources/upstream/source-provenance.json`
- Individual selected binary hashes: `sources/upstream/selected-fonts.json`

Selected families: Baloo 2 (Latin and Devanagari), Baloo Tamma 2 (Kannada), Baloo Chettan 2 (Malayalam), Baloo Thambi 2 (Tamil), Baloo Tammudu 2 (Telugu) and Baloo Da 2 (Bengali). Three source instances per family are retained: Regular, SemiBold and ExtraBold. The selected source snapshot contains VFB outlines and layout text; redundant TTX snapshots and unrelated scripts are excluded.

AT-KPN's Light, Regular and Bold are optical adaptations of those instances. Naming, outline edits, proportions, widths, mark placement and shared metrics are encoded in the supplied tools. `sources/editable/` and `sources/layout/` are the reproducible edited sources.

No Noto or Cocon font binaries or outlines are included in release 0.700. Cocon-derived design information in this package is limited to scalar measurements and visual direction. The approved concept image was generated for this project and is included as a design reference, not evidence of font rendering.

The 0.600 refinement retains upstream shaping identifiers while revising selected contour profiles, advances and anchor placement. Malayalam adds one unencoded traditional alternate glyph per weight and the optional ss01 feature.

Release 0.700 adds a fit to the approved concept image: a per-script outline offset (Bold) and smooth per-glyph warps for the letters in the concept, recorded in `design/concept-fit.json` and applied by `tools/fit_concept.py`. Upstream shaping identifiers, glyph names and layout tables are unchanged.
