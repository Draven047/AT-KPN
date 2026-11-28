# AT-KPN 0.700

AT-KPN is a compact, rounded display family for English, Kannada, Hindi, Marathi, Malayalam, Tamil, Telugu and Bengali. Version 0.700 fits the Bold letterforms to the Study 02 concept image (see FONTLOG.md) on top of the 0.600 Study 02 visual-audit refinements: rounded English feet and exits, corrected headline cuts, fuller native hooks, circular Tamil dots, and balanced below-base forms.

## Use the fonts

- Install the three TTF files in `desktop/`. Each file contains all eight languages. The family is **AT-KPN**, with **Light 300**, **Regular 400** and **Bold 700**.
- On macOS, open each TTF with Font Book and choose Install. If you installed an earlier AT-KPN version, replace or disable it to avoid duplicate family names. Applications may need to restart to refresh their font cache.
- For websites, copy `web/` into your project and load `AT-KPN.css`. Use `font-family: 'AT-KPN', sans-serif` and weight 300, 400 or 700.
- Open `specimen/index.html` to try the actual web fonts and edit the eight sample lines. PNG proofs are in the same directory.
- Malayalam uses the reference-style inline `സ്ക` construction by default. Enable OpenType stylistic set **ss01** for the retained stacked construction; the specimen provides an Inline / Stacked control. Normal Unicode text works with either form.
- Native scripts require an application with OpenType shaping. Avoid letter spacing in joining scripts. Use generous line spacing for deeply stacked conjuncts.

## License and provenance

The font software, editable sources and build scripts are distributed under the **SIL Open Font License 1.1** in `OFL.txt`. Upstream attribution is retained. No publication to an external repository has been performed.

AT-KPN is an adaptation of **Baloo 2 by Ek Type**, release 1.640, not a wholly original drawing of every glyph. It includes independently drawn Latin H, I, K, M, N, W, e, i, l, o and w; adjusted stems in f and r and x-height bowls in b, d, h and k; English corner sizes measured from the reference; regenerated accents over those forms; new Latin mark positioning; and outline, spacing and stroke-end changes across all scripts. Hindi and Marathi share the Devanagari component.

Cocon supplied by the user was the visual reference. No Cocon font binaries or traced Cocon outlines are included. Scalar reference dimensions are recorded in `design/reference-profile.json` and corner positions and setbacks in `design/reference-corners.json`; the builder does not need or read Cocon files. `design/approved-concept.png` records the approved visual concept. It is artwork, not a specimen of the released font, and it is not a literal template for native-script spelling or conjuncts.

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

`fit_concept.py` fits the Bold to `design/approved-concept.png` and stores the result in `design/concept-fit.json`:

- **Letters:** each letter in the concept gets a smooth separable warp (stems stay vertical, curves stay smooth, and the baseline and headline are pinned).
- **Marks and subscripts:** the listed marks and subscripts (`FLEX`: Hindi े, Kannada and Telugu subscript ka) get a free 2D deformation instead.
- **Dots and detached marks:** dots get their own size and position, and detached marks such as the Malayalam chandrakkala get their own 2D shape.
- **Whole script:** each script gets a Bold weight change set from measured stroke thickness (`BOLD_WEIGHT`) and, for Devanagari, a thicker headline (`HEADLINE_EXTRA`).
- **Finishing:** `tools/outline_finish.py` finishes every glyph analytically, on the drawn nodes: winding, one shape for square stem ends (flat cut, one crisp corner, one large soft corner sized from the stem width), the headline and weight changes, and exactly smooth nodes with extrema on the axes. No boolean or stroke operation re-traces an outline; only a glyph built from overlapping pieces is merged first. The earlier blanket corner softening (and the `corner_radius` value in `design/concept-fit.json`) is no longer applied. `tools/check_outlines.py` writes `qa/outline-quality.json` and fails if smooth nodes are left kinked.

Letter changes also apply to glyphs that reuse the same contours and to Light and Regular. English is the exception: its letters follow the scalar reference proportions (box, advance, cap height and descender depth per letter, from `design/reference-profile.json`) and skip the concept letter warps, keeping only the corner finishing; `fit_concept.py --apply` then redraws their corners to the sizes in `design/reference-corners.json` (`tools/corner_match.py`, which also has `--measure` to remeasure from extracted sheet path data). The committed sources already include the fit. After regenerating with `build_family.py`, run `fit_concept.py --apply` and then `compile_edited.py`. To regenerate only some components (for example English Light and Regular after editing `english_refine.py`), call `build_family.build_component('Latin', weight)` for each weight, then run `fit_concept.py --apply --scripts Latin --weights Light Regular`; the fit is applied only to the components you name. `compare_reference.py` writes the concept sheet, the overlays and `qa/visual-comparison.json`, which records overlap and stroke-weight ratio per word. Run `fit_concept.py --fit` only to refit from unfitted 0.600 sources.

The proof rendering helpers use macOS Helvetica for their explanatory labels; the font build itself is independent of that label font. On macOS, `swift tools/check_coretext.swift .` reruns the additional platform check.

All weights are drawn instances, not synthetic application bolding. The source instances Regular, SemiBold and ExtraBold were mapped optically to AT-KPN Light, Regular and Bold, with separate custom Latin stem widths. Native width factors are 94% for Kannada, Devanagari and Malayalam; 98% for Tamil and Telugu; and 100.5% for Bengali. Local corrections independently restore circular dots, rebalance below-base forms and reshape terminals. Advances and anchors are coordinated with the relevant geometry changes. The family is static; this package does not contain variable or italic fonts.

## Validation

`qa/validation.json` records source-to-edited native glyph-sequence checks, component-to-merged shaping comparisons, missing-glyph checks, Unicode coverage, metadata, outline bounds, TTF/WOFF2 layout equivalence and OpenType Sanitizer results. `qa/coretext.json` records macOS CoreText tests, including mixed-language strings. `qa/source-roundtrip.json` records the editable-source rebuild comparison. The final build passes 29,430 component-to-merged shaping cases, 29,391 upstream native sequence checks, 81 CoreText cases and all six TTF/WOFF2 sanitizer checks. Additional checks cover circular Tamil dots, the Bengali headline and both Malayalam constructions. All 21 edited source components reproduce their outlines and layout tables. The browser specimen loads all three weights and exposes the Malayalam alternate along with editing, weight and size controls.

The automated checks establish font integrity and preservation of tested shaping. They do not certify every possible native-language word, typographic refinement or a pixel-identical match to Cocon. Native-reader review of long-form text and uncommon conjuncts remains recommended before a broad production rollout.

Earlier AT-KPN releases are preserved in the Git history. `specimen/AT-KPN-concept-sheet.png` sets the approved concept sheet in the actual 0.700 Bold beside the original artwork, and `specimen/AT-KPN-concept-overlay.png` overlays each word. Both are rendered from the font files by `tools/compare_reference.py`. `qa/visual-comparison.json` records the overlap (IoU) per word. It measures silhouettes, not legibility, so native-reader review of the revised forms is still recommended.
