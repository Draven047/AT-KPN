# AT-KPN

A rounded, open-source display font family for **English, Kannada, Hindi, Marathi, Malayalam, Tamil, Telugu and Bengali**.

**[Try the font and download it](https://at-kpn-fonts.amar047.chatgpt.site/)** · [Releases](https://github.com/Draven047/AT-KPN/releases) · [Report a glyph issue](https://github.com/Draven047/AT-KPN/issues)

AT-KPN 0.600 includes **Light (300), Regular (400) and Bold (700)**. Desktop fonts are available as TTF and genuine CFF OTF; web fonts are available as WOFF2 and WOFF. The combined family covers all eight languages, and separate language families include English for mixed text.

## Downloads

The website offers individual weight/format downloads, a ZIP for each language, format bundles, and a complete collection ZIP. Every ZIP includes the font license and credits. GitHub Releases also provide the complete collection, TTF, OTF and web bundles.

| Folder | Contents |
| --- | --- |
| `TTF/<Language>/` | Three desktop TrueType weights per language |
| `OTF/<Language>/` | Three desktop CFF OpenType weights per language |
| `web/<Language>/` | WOFF2 and WOFF for the three weights |
| `desktop/` | Combined multilingual TTF and OTF |
| `web/All-languages/` | Combined multilingual web fonts |
| `sources/editable/` | 21 edited UFO sources |
| `sources/layout/` | Coordinated OpenType layout TTX sidecars |
| `sources/upstream/` | Baloo 2 source snapshots and provenance |
| `site/` | Interactive specimen and download site source |
| `tools/` | Font and website build scripts |
| `qa/` | Validation reports |

Choose TTF or OTF when installing a family; the two formats contain the same design. Hindi and Marathi share the Devanagari design. Malayalam includes an optional stacked form using the OpenType `ss01` feature.

## Run the website locally

The website is static HTML, CSS and JavaScript with no runtime dependencies. Python 3 builds the downloadable bundles from the committed font exports.

```sh
python3 tools/build_website.py
python3 tools/check_website.py
python3 -m http.server 8000 --directory dist
```

Open `http://localhost:8000`. The playground supports editable text, eight languages, three weights, adjustable size, preview colors and the Malayalam alternate. Downloads work without an account; default TTF and all ZIP links also work without JavaScript.

## Edit and rebuild the fonts

See [FONT-DEVELOPMENT.md](FONT-DEVELOPMENT.md) for the drawing and shaping workflow. Use Python 3.11 or later and the pinned dependencies in `tools/requirements.txt`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python tools/compile_edited.py
.venv/bin/python tools/validate_family.py
.venv/bin/python tools/export_language_fonts.py
.venv/bin/python tools/prepare_web_fonts.py
.venv/bin/python tools/build_website.py
.venv/bin/python tools/check_website.py
```

The supplied compiler keeps each UFO coordinated with its TTX layout sidecar. Do not use a generic UFO export for these complex-script sources. `build_family.py` regenerates the design from upstream and overwrites edited UFOs; use `compile_edited.py` to keep later outline edits.

## Design and provenance

AT-KPN is an adaptation of **Baloo 2 by Ek Type**, release 1.640. It includes six independently drawn Latin letter constructions, coordinated accents, refined native terminals, adjusted proportions, round Tamil dots and a revised Malayalam construction. It is not a wholly original drawing of every glyph. Cocon was a visual reference; its binaries and traced outlines are not included.

See [AUTHORS.md](AUTHORS.md), [PROVENANCE.md](PROVENANCE.md) and [FONTLOG.md](FONTLOG.md). Font integrity, source rebuild, shaping, conversion and macOS checks are recorded in `qa/`. Native-reader review of uncommon conjuncts and long-form text is still welcome.

## License

Font software and sources: **[SIL Open Font License 1.1](OFL.txt)**. Website code: **[MIT](LICENSE-CODE.txt)**. Preserve the original notices when redistributing fonts. No Cocon font software is distributed in this repository.
