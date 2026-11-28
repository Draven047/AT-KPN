# AT-KPN 0.700 — fonts by format and language

`TTF/` and `OTF/` each contain these eight language folders:

- English
- Kannada
- Hindi
- Marathi
- Malayalam
- Tamil
- Telugu
- Bengali

Each language folder has Light (300), Regular (400) and Bold (700): 24 TTF files and 24 OTF files in total.

The OTF files are genuine OpenType fonts with CFF cubic outlines. Their outlines, spacing and shaping are converted from the 0.700 TrueType fonts, with whole-unit CFF coordinates (within 0.5 units) and subroutinization. Each Indian-language font also contains English, punctuation and shared symbols for mixed text. Hindi and Marathi use the same Devanagari design, with separate family names.

Choose TTF or OTF for each language when installing; the two formats represent the same family and weights. Language names appear in font menus, for example **AT-KPN Kannada**. The existing multilingual fonts remain in `desktop/`.

SIL Open Font License 1.1 and author credits are included in each format folder. Editable sources remain in `sources/`; `tools/export_language_fonts.py` recreates these exports. Validation is recorded in `qa/language-exports.json` and `qa/language-coretext.json`; `LANGUAGE-FONTS.sha256` lists the exported file hashes.
