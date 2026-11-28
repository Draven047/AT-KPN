"""Outline quality report for the editable sources.

Counts, per component, the things that make an outline look untidy:
  kinks    nodes that turn 1.5-12 degrees where a curve is involved (meant to be smooth, but are not)
  short    segments under 3 units
  offaxis  smooth curve nodes 0.3-3 degrees away from horizontal/vertical (extrema that miss the axis)
Writes qa/outline-quality.json; fails when kinks per glyph exceed the limit.
"""
from pathlib import Path
import argparse, json
from ufoLib2 import Font as UFO
import outline_finish
from fit_concept import read, SCRIPTS, WEIGHTS

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 0.05         # kinks per glyph


def report(root):
    out = {}
    for script in SCRIPTS:
        for weight in WEIGHTS:
            path = root/'sources/editable'/f'AT-KPN{script}-{weight}.ufo'
            if not path.exists(): continue
            tot = {'glyphs': 0, 'nodes': 0, 'kinks': 0, 'gentle_corners': 0, 'short': 0, 'offaxis': 0, 'corners': 0}
            for g in UFO.open(path):
                cs = read(g)
                if not cs: continue
                tot['glyphs'] += 1
                for k, v in outline_finish.quality(cs).items(): tot[k] += v
            tot['nodes_per_glyph'] = round(tot['nodes']/tot['glyphs'], 1); tot['kinks_per_glyph'] = round(tot['kinks']/tot['glyphs'], 2)
            out[f'{script}-{weight}'] = tot
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); ap.add_argument('--root', default=str(ROOT)); ap.add_argument('--no-write', action='store_true')
    a = ap.parse_args(); r = report(Path(a.root))
    for k, v in r.items(): print(f"{k:20s} nodes/glyph {v['nodes_per_glyph']:6.1f}  kinks {v['kinks']:6d} ({v['kinks_per_glyph']}/glyph)  short {v['short']:5d}  offaxis {v['offaxis']:5d}")
    ok = all(v['kinks_per_glyph'] <= LIMIT for v in r.values())
    if not a.no_write: (ROOT/'qa/outline-quality.json').write_text(json.dumps({'pass': ok, 'limit_kinks_per_glyph': LIMIT, 'components': r}, indent=2)+'\n')
    print('pass' if ok else 'FAIL'); raise SystemExit(0 if ok else 1)
