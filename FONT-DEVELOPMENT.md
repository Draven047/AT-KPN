# AT-KPN 0.600

AT-KPN is a compact, rounded display family for English, Kannada, Hindi, Marathi, Malayalam, Tamil, Telugu and Bengali. This release implements the Study 02 visual-audit refinements: rounded English feet and exits, corrected headline cuts, fuller native hooks, circular Tamil dots, and balanced below-base forms.

## Use the fonts

- Install the three TTF files in `desktop/`. Each file contains all eight languages. The family is **AT-KPN**, with **Light 300**, **Regular 400** and **Bold 700**.
- On macOS, open each TTF with Font Book and choose Install. If you installed an earlier AT-KPN version, replace or disable it to avoid duplicate family names. Applications may need to restart to refresh their font cache.
- For websites, copy `web/` into your project and load `AT-KPN.css`. Use `font-family: 'AT-KPN', sans-serif` and weight 300, 400 or 700.
- Open `specimen/index.html` to try the actual web fonts and edit the eight sample lines. PNG proofs are in the same directory.
- Malayalam uses the reference-style inline `സ്ക` construction by default. Enable OpenType stylistic set **ss01** for the retained stacked construction; the specimen provides an Inline / Stacked control. Normal Unicode text works with either form.
- Native scripts require an application with OpenType shaping. Avoid letter spacing in joining scripts. Use generous line spacing for deeply stacked conjuncts.

## License and provenance

The font software, editable sources and build scripts are distributed under the **SIL Open Font License 1.1** in `OFL.txt`. Upstream attribution is retained. No publication to an external repository has been performed.

AT-KPN is an adaptation of **Baloo 2 by Ek Type**, release 1.640, not a wholly original drawing of every glyph. It includes independently drawn Latin H, I, e, i, l and o; regenerated accents over those forms; new Latin mark positioning; and outline, spacing and stroke-end changes across all scripts. Hindi and Marathi share the Devanagari component.

Cocon supplied by the user was the visual reference. No Cocon font binaries or traced Cocon outlines are included. Scalar reference dimensions are recorded in `design/reference-profile.json`; the builder does not need or read Cocon files. `design/approved-concept.png` records the approved visual concept. It is artwork, not a specimen of the released font, and it is not a literal template for native-script spelling or conjuncts.

Upstream: https://github.com/EkType/Baloo2 at commit `3aa20453e9f86f3f21b17e9a585f9d89181b2c17` (release 1.640). Original copyrights, contributors and license are included in `sources/upstream/`. Download provenance and hashes accompany the sources.

## Edit and rebuild

Use Python 3.11 or later. Dependencies used in this build are recorded in `tools/requirements.lock.txt`. The smaller `tools/requirements.txt` lists the packages directly required by this project.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python tools/compile_edited.py
.venv/bin/python tools/validate_family.py
.venv/bin/python tools/make_proofs.py
.venv/bin/python tools/make_overview.py
.venv/bin/python tools/make_specimen.py
```

`compile_edited.py` compiles the **21 editable UFOs** in `sources/editable/` and retains the complex OpenType layout from corresponding `sources/layout/*.ttx` files. The UFOs contain outlines, Unicode mappings and advances. Layout is deliberately kept in the TTX sidecars, not in UFO feature text; use the supplied compiler rather than a generic UFO export. Glyph names and order must remain coordinated with the layout sidecar. Original upstream VFB and layout sources are also included.

`build_family.py` recreates the design from the upstream TTFs and `design/config.json`. **It overwrites the edited UFOs**, so use it only to regenerate the starting design. Use `compile_edited.py` to retain subsequent hand edits.

The proof rendering helpers use macOS Helvetica for their explanatory labels; the font build itself is independent of that label font. On macOS, `swift tools/check_coretext.swift .` reruns the additional platform check.

All weights are drawn instances, not synthetic application bolding. The source instances Regular, SemiBold and ExtraBold were mapped optically to AT-KPN Light, Regular and Bold, with separate custom Latin stem widths. Native width factors are 94% for Kannada, Devanagari and Malayalam; 98% for Tamil and Telugu; and 100.5% for Bengali. Local corrections independently restore circular dots, rebalance below-base forms and reshape terminals. Advances and anchors are coordinated with the relevant geometry changes. The family is static; this package does not contain variable or italic fonts.

## Validation

`qa/validation.json` records source-to-edited native glyph-sequence checks, component-to-merged shaping comparisons, missing-glyph checks, Unicode coverage, metadata, outline bounds, TTF/WOFF2 layout equivalence and OpenType Sanitizer results. `qa/coretext.json` records macOS CoreText tests, including mixed-language strings. `qa/source-roundtrip.json` records the editable-source rebuild comparison. The final build passes 29,430 component-to-merged shaping cases, 29,391 upstream native sequence checks, 81 CoreText cases and all six TTF/WOFF2 sanitizer checks. Additional checks cover circular Tamil dots, the Bengali headline and both Malayalam constructions. All 21 edited source components reproduce their outlines and layout tables. The browser specimen loads all three weights and exposes the Malayalam alternate along with editing, weight and size controls.

The automated checks establish font integrity and preservation of tested shaping. They do not certify every possible native-language word, typographic refinement or a pixel-identical match to Cocon. Native-reader review of long-form text and uncommon conjuncts remains recommended before a broad production rollout.

Earlier AT-KPN releases are preserved separately. `specimen/AT-KPN-refinement-comparison.png` compares the approved artwork, 0.500 and 0.600; it is rendered from the actual font files. Word-width figures in `qa/visual-comparison.json` describe silhouettes at equal visible height, not a percentage similarity score. Native-reader review of the revised forms is still pending.
