# Contributing to AT-KPN

For a rendering issue, include the language, exact Unicode text, font weight, application/operating system and a screenshot when possible. Native-reader feedback on letterforms, spacing and conjuncts is especially useful.

Edit coordinated sources in `sources/editable/` and `sources/layout/`, then compile with `tools/compile_edited.py`. Run the appropriate font checks before submitting a change. Preserve the upstream copyright and SIL OFL notices.

For website changes, edit `site/`, run `python3 tools/build_website.py` and `python3 tools/check_website.py`, then check the live tester and downloads in a browser. Do not commit `dist/`, credentials, generated server logs or environment files.
