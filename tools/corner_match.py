"""Corner sizes for the English letters.

A corner here is the meeting of two straight sides: a stem end, a bar end, the foot of a stem, or the inside
angle where an arm leaves a stem. Each corner is described by three scalars: the point where the two sides
would meet, and how far back along each side the rounding starts (0 and 0 for a crisp corner).

`--measure` reads those scalars from the reference sheet's path data (extracted outside this repository) and
writes design/reference-corners.json. Only the corner positions and setbacks are kept, rounded to whole units;
no outline data is stored. `apply()` then redraws the matching corners of AT-KPN's own outlines: the straight
sides are trimmed to the measured setbacks and joined by one cubic with the family's own handle tension,
so the rest of every letter stays as AT-KPN draws it.
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'design/reference-corners.json'
CHARS = ['ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz', '0123456789']
WEIGHTS = ['Bold', 'Regular', 'Light']
TENSION = 0.65          # handle length as a share of the setback (the reference sheet's median is 0.63-0.66)
MIN_RUN = 22            # shortest straight side, in font units
MAX_SET = 330           # largest setback treated as a corner (beyond this it is a bowl, not a corner)


def _sub(a, b): return (a[0]-b[0], a[1]-b[1])
def _add(a, b): return (a[0]+b[0], a[1]+b[1])
def _mul(a, k): return (a[0]*k, a[1]*k)
def _len(a): return math.hypot(a[0], a[1])
def _dot(a, b): return a[0]*b[0]+a[1]*b[1]
def _cross(a, b): return a[0]*b[1]-a[1]*b[0]
def _unit(a):
    l = _len(a); return (a[0]/l, a[1]/l) if l > 1e-9 else (0.0, 0.0)
def _angle(a, b): return math.degrees(math.atan2(_cross(a, b), _dot(a, b)))


def _point(s, t):
    if len(s) == 2: return (s[0][0]+(s[1][0]-s[0][0])*t, s[0][1]+(s[1][1]-s[0][1])*t)
    m = 1-t; return tuple(m**3*s[0][i]+3*m*m*t*s[1][i]+3*m*t*t*s[2][i]+t**3*s[3][i] for i in (0, 1))


def _straight(s, tol=0.8):
    if len(s) == 2: return True
    d = _sub(s[3], s[0]); l = _len(d)
    if l < 1: return False
    u = _mul(d, 1/l)
    return all(abs(_cross(_sub(c, s[0]), u)) < tol and -tol < _dot(_sub(c, s[0]), u) < l+tol for c in (s[1], s[2]))


def collapse(segs):
    """Straight cubics become lines and collinear neighbouring lines become one line."""
    segs = [(s[0], s[3]) if len(s) == 4 and _straight(s) else s for s in segs]
    segs = [s for s in segs if _len(_sub(s[-1], s[0])) > 0.05 or len(s) == 4]
    changed = True
    while changed and len(segs) > 2:
        changed = False
        for i in range(len(segs)):
            a, b = segs[i-1], segs[i]
            if len(a) == 2 and len(b) == 2 and abs(_angle(_unit(_sub(a[1], a[0])), _unit(_sub(b[1], b[0])))) < 0.6:
                segs[i-1] = (a[0], b[1]); del segs[i]; changed = True; break
    return segs


def _is_line(s): return len(s) == 2 and _len(_sub(s[1], s[0])) >= MIN_RUN


def _tan(s, end=False):
    pts = s[::-1] if end else s
    for q in pts[1:]:
        v = _sub(q, pts[0])
        if _len(v) > 1e-6: return _unit(_mul(v, -1) if end else v)
    return (0.0, 0.0)


def _meet(P, d, Q, e):
    """Intersection of the line through P along d with the line through Q along e (None if parallel)."""
    den = _cross(d, e)
    if abs(den) < 1e-6: return None
    return _add(P, _mul(d, _cross(_sub(Q, P), e)/den))


def _monotone(segs, d0, d_end, t):
    prev = d0
    for s in segs:
        for q in range(1, 9):
            d = _sub(_point(s, q/8), _point(s, (q-1)/8))
            if _len(d) < 1e-3: continue
            d = _unit(d)
            if _angle(prev, d)*t < -3: return False
            prev = d
    return _angle(prev, d_end)*t >= -3


def _axis(d): return min(abs(d[0]), abs(d[1])) < 0.035     # within 2 degrees of level or upright


def corners(segs):
    """Corners of one contour, as dicts:
      side1, side2  segment indices of the straight or curved sides, or None for a curve's extreme point
      gap           the segments between them (the rounding), V where the sides' tangents meet,
      d1, d2        the directions at the corner, a and b how far back from V the rounding starts
                    (0 and 0 when crisp), E1/E2 the extreme points, turn in degrees and a key.
    Kinds: straight to straight (any short run of curves between), straight to curve (one cubic, or a crisp
    node), and straight to the extreme point of a curve (the arch of n or the bowl of u: one to three cubics)."""
    n = len(segs); out = []
    def add(side1, side2, gap, V, d1, d2, a, b, t, E1=None, E2=None):
        kind = lambda k: 'point' if k is None else 'line' if len(segs[k]) == 2 else 'curve'
        out.append({'side1': side1, 'side2': side2, 'gap': gap, 'V': V, 'd1': d1, 'd2': d2, 'a': max(a, 0.0), 'b': max(b, 0.0),
                    'turn': t, 'E1': E1, 'E2': E2, 'key': (side1, side2, tuple(gap)), 'k1': kind(side1), 'k2': kind(side2)})
    runs = [i for i, s in enumerate(segs) if _is_line(s)]
    for k, i in enumerate(runs):                                  # straight to straight
        j = runs[(k+1) % len(runs)]
        if j == i: continue
        gap = [(i+1+m) % n for m in range((j-i-1) % n)]
        s1, s2 = segs[i], segs[j]; d1 = _tan(s1, True); d2 = _tan(s2)
        t = _angle(d1, d2)
        if not 50 <= abs(t) <= 130: continue
        V = _meet(s1[1], d1, s2[0], d2)
        a = _dot(_sub(V, s1[1]), d1); b = _dot(_sub(s2[0], V), d2)
        if a < -1.5 or b < -1.5 or max(a, b) > MAX_SET or not gap and max(a, b) > 1.5: continue
        reach = 1.35*max(a, b)+3
        if any(_len(_sub(_point(segs[g], q/8), V)) > reach for g in gap for q in range(1, 9)): continue
        if not _monotone([segs[g] for g in gap], d1, d2, t): continue
        add(i, j, gap, V, d1, d2, a, b, t)
    taken = {g for c in out for g in c['gap']}
    for k in range(n):                                            # straight to curved, or curved to straight
        s0, s1 = segs[k-1], segs[k]
        if (_is_line(s0) and len(s1) == 4) or (len(s0) == 4 and _is_line(s1)):     # crisp node
            d1 = _tan(s0, True); d2 = _tan(s1); t = _angle(d1, d2)
            if 50 <= abs(t) <= 130: add((k-1) % n, k, [], s1[0], d1, d2, 0.0, 0.0, t)
        s2 = segs[(k+1) % n]
        if len(s1) == 4 and ((_is_line(s0) and len(s2) == 4) or (len(s0) == 4 and _is_line(s2))):   # one cubic
            d1 = _tan(s0, True); d2 = _tan(s2); t = _angle(d1, d2)
            if not 50 <= abs(t) <= 130: continue
            if abs(_angle(d1, _tan(s1))) > 12 or abs(_angle(_tan(s1, True), d2)) > 12: continue
            V = _meet(s1[0], d1, s1[3], d2)
            if V is None: continue
            a = _dot(_sub(V, s1[0]), d1); b = _dot(_sub(s1[3], V), d2)
            if min(a, b) < 1 or max(a, b) > MAX_SET or not _monotone([s1], d1, d2, t): continue
            add((k-1) % n, (k+1) % n, [k], V, d1, d2, a, b, t)
    simple = {g for c in out for g in c['gap']} | {c['side1'] for c in out} | {c['side2'] for c in out}
    for i in runs:                                                # straight to a curve's extreme point
        if not _axis(_tan(segs[i])): continue                     # upright and level sides only
        for sgn in (1, -1):
            d1 = _tan(segs[i], True) if sgn > 0 else _mul(_tan(segs[i]), -1)
            P = segs[i][1] if sgn > 0 else segs[i][0]; gap = []
            for m in range(1, 7):
                g = (i+sgn*m) % n; s = segs[g]
                if len(s) != 4 or g in taken: break
                gap.append(g)
                e = _tan(s, True) if sgn > 0 else _mul(_tan(s), -1)
                E = s[3] if sgn > 0 else s[0]
                t = _angle(d1, e)
                if abs(t) > 130: break
                if 70 <= abs(t) <= 110 and _axis(e):
                    nxt = segs[(g+sgn) % n]
                    if len(nxt) != 4 or abs(_angle(e, _tan(nxt) if sgn > 0 else _mul(_tan(nxt, True), -1))) > 3: break
                    V = _meet(P, d1, E, e)
                    if V is None: break
                    a = _dot(_sub(V, P), d1); b = _dot(_sub(E, V), e)
                    if min(a, b) < 1 or max(a, b) > MAX_SET or not _monotone([segs[q] for q in (gap if sgn > 0 else gap[::-1])] if sgn > 0 else [tuple(segs[q][::-1]) for q in gap], d1, e, t): break
                    if len(gap) == 1 and (g in simple): break
                    if sgn > 0: add(i, None, gap, V, d1, e, a, b, t, E2=E)
                    else: add(None, i, gap[::-1], V, _mul(e, -1), _mul(d1, -1), b, a, -t, E1=E)
                    break
    return out


def _split(s, t):
    p0, p1, p2, p3 = s
    l = lambda a, b: _add(a, _mul(_sub(b, a), t))
    a, b, c = l(p0, p1), l(p1, p2), l(p2, p3); d, e = l(a, b), l(b, c); f = l(d, e)
    return (p0, a, d, f), (f, e, c, p3)


def _trim_start(s, V, d, dist):
    """Cubic s starts on the corner's side; move its start to `dist` from V (along d, or into the curve)."""
    b0 = _dot(_sub(s[0], V), d)
    if dist <= b0+0.5:
        B = _add(V, _mul(d, dist)); return (B, s[1] if _len(_sub(s[1], s[0])) > 1e-6 else B, s[2], s[3])
    lo, hi = 0.0, 1.0
    if _len(_sub(s[3], V)) <= dist: hi = lo = 0.85
    for _ in range(40):
        m = (lo+hi)/2
        if _len(_sub(_point(s, m), V)) < dist: lo = m
        else: hi = m
    return _split(s, (lo+hi)/2)[1]


def _trim_end(s, V, d, dist):
    r = _trim_start(s[::-1], V, _mul(d, -1), dist); return r[::-1]


def rebuild(segs, targets):
    """targets: {corner key: (a, b)} for corners found by corners(segs). Returns the new contour."""
    cs = [c for c in corners(segs) if c['key'] in targets]
    if not cs: return segs
    n = len(segs); new = list(segs); block = {}; drop = set()
    for c in cs: drop.update(c['gap'])
    # curved sides first: they set where the corner meets them and the tangent there
    for c in cs:
        a, b = targets[c['key']]
        if c['side2'] is not None and len(new[c['side2']]) == 4: new[c['side2']] = _trim_start(new[c['side2']], c['V'], c['d2'], b)
        if c['side1'] is not None and len(new[c['side1']]) == 4: new[c['side1']] = _trim_end(new[c['side1']], c['V'], _mul(c['d1'], -1), a)
    ends = {}; starts = {}; info = []
    for c in cs:
        a, b = targets[c['key']]
        s1 = new[c['side1']] if c['side1'] is not None else None; s2 = new[c['side2']] if c['side2'] is not None else None
        d1 = _tan(s1, True) if s1 and len(s1) == 4 else c['d1']; d2 = _tan(s2) if s2 and len(s2) == 4 else c['d2']
        P1 = s1[-1] if s1 and len(s1) == 4 else c['V']; P2 = s2[0] if s2 and len(s2) == 4 else c['V']
        V = _meet(P1, d1, P2, d2) or c['V']
        if s1 is None: a = min(a, _len(_sub(V, c['E1'])))           # an extreme point: the flat can only shrink
        if s2 is None: b = min(b, _len(_sub(c['E2'], V)))
        A = s1[-1] if s1 and len(s1) == 4 else _sub(V, _mul(d1, a))
        B = s2[0] if s2 and len(s2) == 4 else _add(V, _mul(d2, b))
        if s1 is not None and len(s1) == 2: ends[c['side1']] = A
        if s2 is not None and len(s2) == 2: starts[c['side2']] = B
        info.append((c, A, B, d1, d2))
    # a straight side keeps some length between its two corners
    for r in set(ends) | set(starts):
        s = new[r]; u = _unit(_sub(s[1], s[0])); P0 = starts.get(r, s[0]); P1 = ends.get(r, s[1])
        pa, pb = _dot(_sub(P0, s[0]), u), _dot(_sub(P1, s[0]), u)
        if pb-pa < 3:                                             # the corners meet: no straight part left
            L = _len(_sub(s[1], s[0]))
            m = (pa+pb)/2 if r in starts and r in ends else L if r in starts else 0.0
            m = min(max(m, 0.0), L)
            if r in starts: starts[r] = _add(s[0], _mul(u, m))
            if r in ends: ends[r] = _add(s[0], _mul(u, m))
    for c, A, B, d1, d2 in info:
        if c['side1'] is not None and c['side1'] in ends: A = ends[c['side1']]
        if c['side2'] is not None and c['side2'] in starts: B = starts[c['side2']]
        segs_c = []
        if c['E1'] is not None and _len(_sub(A, c['E1'])) < 3: A = c['E1']
        if c['E2'] is not None and _len(_sub(c['E2'], B)) < 3: B = c['E2']
        if c['E1'] is not None and _len(_sub(A, c['E1'])) > 1: segs_c.append((c['E1'], A))
        if _len(_sub(B, A)) >= 1.0:
            X = _meet(A, d1, B, d2)
            ha = _len(_sub(X, A))*TENSION if X else _len(_sub(B, A))/3
            hb = _len(_sub(B, X))*TENSION if X else _len(_sub(B, A))/3
            segs_c.append((A, _add(A, _mul(d1, ha)), _sub(B, _mul(d2, hb)), B))
        if c['E2'] is not None and _len(_sub(c['E2'], B)) > 1: segs_c.append((B, c['E2']))
        block[c['gap'][0] if c['gap'] else ('after', c['side1'])] = segs_c
    out = []
    for k in range(n):
        if k in block: out += block[k]
        if k in drop: continue
        s = new[k]
        if len(s) == 2: s = (starts.get(k, s[0]), ends.get(k, s[1]))
        out.append(s)
        if ('after', k) in block: out += block[('after', k)]
    # join any ends that no longer meet exactly (a crisp corner whose curved side moved to V)
    fixed = []
    for i, s in enumerate(out):
        prev = out[i-1][-1]
        if _len(_sub(prev, s[0])) > 1e-3:
            if _len(_sub(prev, s[0])) > 3: return None               # the sides no longer meet: not this corner
            s = (prev,)+tuple(s[1:])
        fixed.append(s)
    return collapse([s for s in fixed if _len(_sub(s[-1], s[0])) > 0.05])


# ---------------------------------------------------------------- matching
def glyph_corners(cs):
    out = []
    for ci, segs in enumerate(cs):
        for c in corners(segs): c['contour'] = ci; out.append(c)
    return out


def bbox(cs):
    pts = [p for segs in cs for s in segs for p in s]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def match(ours, ref, box, rbox, tol, loose=()):
    """Pairs each reference corner with the nearest AT-KPN corner of the same kind. ref positions are mapped
    from the reference box to ours horizontally (the reference can be narrower), vertically as measured.
    loose: points of new stroke-end cuts; a corner there may have a curved side whose tangent differs more."""
    sx = (box[2]-box[0])/max(rbox[2]-rbox[0], 1)
    mapped = [(r, (box[0]+(r['V'][0]-rbox[0])*sx, r['V'][1])) for r in ref]
    cand = []
    for oi, o in enumerate(ours):
        lo = any(_len(_sub(o['V'], q)) < 40 for q in loose)
        for ri, (r, P) in enumerate(mapped):
            if abs(o['turn']-r['turn']) > (35 if lo and 'curve' in (o.get('k1'), o.get('k2')) else 20): continue
            if abs(_angle(o['d1'], r['d1'])) > (32 if lo and o.get('k1') == 'curve' else 15): continue
            if abs(_angle(o['d2'], r['d2'])) > (32 if lo and o.get('k2') == 'curve' else 15): continue
            d = _len(_sub(o['V'], P))
            if d < tol: cand.append((d, oi, ri))
    used_o = set(); used_r = set(); pairs = []
    for d, oi, ri in sorted(cand):
        if oi in used_o or ri in used_r: continue
        used_o.add(oi); used_r.add(ri); pairs.append((ours[oi], mapped[ri][0]))
    return pairs


def apply(cs, ref, tol=60, box=None):
    """Redraw the corners of glyph contours cs that match the reference corners ref (from the profile).
    box: the letter's own bounds, when cs also holds an accent (else the bounds of cs)."""
    if not cs or not ref: return cs, 0
    cs = [collapse(c) for c in cs]; box = box or bbox(cs)
    cs, cut, loose = recut(cs, ref.get('cuts', []), box, ref['box'])
    ours = glyph_corners(cs)
    rbox = ref['box']; refc = [{'V': tuple(r['v']), 'd1': _unit(tuple(r['d1'])), 'd2': _unit(tuple(r['d2'])), 'turn': r['turn'],
                               'a': r['a'], 'b': r['b']} for r in ref['corners']]
    pairs = match(ours, refc, box, rbox, tol, loose)
    targets = {}
    for o, r in pairs: targets.setdefault(o['contour'], []).append((o, (r['a'], r['b'])))
    out = []; done = 0
    for ci, segs in enumerate(cs):
        keep = {}
        for o, ab in sorted(targets.get(ci, []), key=lambda it: it[0]['V']):
            trial = dict(keep); trial[o['key']] = ab
            new = rebuild(segs, trial)
            # accept a corner only if the change stays a corner change: small, local and clean
            size = max(o['a'], o['b'], *ab)+10
            if new is not None and _clean(new) and _xor(rebuild(segs, keep) if keep else segs, new) <= 0.75*size*size:
                keep = trial; done += 1
        out.append(rebuild(segs, keep) if keep else segs)
    return out, done+cut


def _pp(segs):
    import pathops
    p = pathops.Path(); p.moveTo(*segs[0][0])
    for s in segs: p.lineTo(*s[1]) if len(s) == 2 else p.cubicTo(*s[1], *s[2], *s[3])
    p.close(); return p


def _xor(a, b):
    import pathops
    return abs(pathops.op(_pp(a), _pp(b), pathops.PathOp.XOR).area)


def _clean(segs):
    """No self-intersection: simplifying the contour keeps its area."""
    import pathops
    p = _pp(segs); q = pathops.simplify(p, fix_winding=True)
    return abs(abs(q.area)-abs(p.area)) < 1.0


class Redrawn:
    """Base letters' contours before and after their corners were redrawn. Accented letters carry copies of
    their base's contours (equal to within a unit of rounding), which take the same redrawn shape."""
    def __init__(self): self.by = {}

    def add(self, old, new):
        if old != new: self.by.setdefault(tuple(len(s) for s in old), []).append((old, new))

    def get(self, segs):
        o = segs[0][0]
        for old, new in self.by.get(tuple(len(s) for s in segs), []):
            p = old[0][0]
            if all(abs((x[0]-o[0])-(y[0]-p[0])) <= 1.5 and abs((x[1]-o[1])-(y[1]-p[1])) <= 1.5 for s, t in zip(segs, old) for x, y in zip(s, t)):
                dx, dy = o[0]-p[0], o[1]-p[1]
                return [tuple((q[0]+dx, q[1]+dy) for q in s) for s in new]
        return segs


# ---------------------------------------------------------------- stroke ends
def _crossings(segs, P, u):
    """Where the contour crosses the line through P along u: (segment index, t, point), in contour order."""
    out = []
    f = lambda p: _cross(u, _sub(p, P))
    for i, s in enumerate(segs):
        ts = [k/48 for k in range(49)]; vals = [f(_point(s, t)) for t in ts]
        for k in range(48):
            a, b = vals[k], vals[k+1]
            if a == 0 or a*b < 0:
                lo, hi = ts[k], ts[k+1]
                for _ in range(40):
                    m = (lo+hi)/2
                    if (f(_point(s, lo)) <= 0) == (f(_point(s, m)) <= 0): lo = m
                    else: hi = m
                t = (lo+hi)/2; out.append((i, t, _point(s, t)))
    return out


def _part(s, t0, t1):
    """The piece of segment s between parameters t0 < t1."""
    if len(s) == 2: return (_point(s, t0), _point(s, t1))
    s = _split(s, t0)[1] if t0 > 1e-9 else s
    return _split(s, (t1-t0)/(1-t0))[0] if t1 < 1-1e-9 else s


def _extend(segs, P, Q):
    """Level (or square) cut by extension: two straight stroke sides near the cut are extended to the cut line,
    replacing the short end between them. Returns the new contour or None."""
    u = _unit(_sub(Q, P)); L = _len(_sub(Q, P)); n = len(segs); bx = bbox([segs])
    near = lambda p: _len(_sub(p, _add(P, _mul(u, min(max(_dot(_sub(p, P), u), 0), L))))) < 0.9*L+40
    for i, s1 in enumerate(segs):
        if not _is_line(s1) or not near(s1[1]): continue
        for gap in range(1, 6):
            j = (i+gap) % n; s2 = segs[j]
            if j == i: break
            if not _is_line(s2): continue
            if not near(s2[0]): break
            d1 = _unit(_sub(s1[1], s1[0])); d2 = _unit(_sub(s2[1], s2[0]))
            C1 = _meet(s1[0], d1, P, u); C2 = _meet(s2[0], d2, P, u)
            if C1 is None or C2 is None: break
            if _dot(_sub(C1, s1[0]), d1) < 0.5*_len(_sub(s1[1], s1[0])) or _dot(_sub(s2[1], C2), d2) < 0.5*_len(_sub(s2[1], s2[0])): break
            if _dot(_sub(C2, C1), u) <= 0 or not .5*L <= _len(_sub(C2, C1)) <= 1.6*L: break
            if not 60 <= abs(_angle(d1, u)) <= 120 or not 60 <= abs(_angle(u, d2)) <= 120: break   # steep strokes only
            if any(not (bx[0]-5 <= c[0] <= bx[2]+5 and bx[1]-5 <= c[1] <= bx[3]+5) for c in (C1, C2)): break
            mid = [(i+1+m) % n for m in range(gap-1)]
            out = []
            for k in range(n):
                if k in mid: continue
                if k == i: out += [(s1[0], C1), (C1, C2)]
                elif k == j: out.append((C2, s2[1]))
                else: out.append(segs[k])
            return [s for s in out if _len(_sub(s[-1], s[0])) > 0.05]
        # only the nearest pair is tried for each side
    return None


def _cross_cut(segs, P, u, L, cut):
    X = _crossings(segs, P, u); n = len(X)
    for k in range(n):
        (i1, t1, X1), (i2, t2, X2) = X[k], X[(k+1) % n]
        if n < 2 or (i1, t1) == (i2, t2): continue
        if not (-.35*L <= _dot(_sub(X1, P), u) <= 1.35*L and -.35*L <= _dot(_sub(X2, P), u) <= 1.35*L): continue
        if _dot(_sub(X2, X1), u) <= 0 or not .6*L <= _len(_sub(X2, X1)) <= 1.6*L: continue
        m = len(segs)
        idx = [i1] + [(i1+q) % m for q in range(1, (i2-i1) % m+1)] if not (i1 == i2 and t2 > t1) else [i1]
        pts = [_point(segs[j], q/16) for j in idx for q in range(17)]
        if any(_cross(u, _sub(p, P)) < -2.5 for p in pts[1:-1] if _len(_sub(p, X1)) > 3 and _len(_sub(p, X2)) > 3): continue
        if max(_len(_sub(p, _add(P, _mul(u, min(max(_dot(_sub(p, P), u), 0), L))))) for p in pts) > 1.1*L: continue
        out = [(X2, segs[i2][1]) if len(segs[i2]) == 2 else _part(segs[i2], t2, 1)]
        j = (i2+1) % m
        while j != i1: out.append(segs[j]); j = (j+1) % m
        out.append((segs[i1][0], X1) if len(segs[i1]) == 2 else _part(segs[i1], 0, t1))
        out.append((X1, X2))
        new = [s for s in out if _len(_sub(s[-1], s[0])) > 0.05]
        # where the reference cut flows out of the curve, the curve meets the cut tangentially
        for q, s in enumerate(new):
            if len(s) != 4: continue
            if cut.get('smooth_p') and _len(_sub(s[3], X1)) < 1e-6:
                h = _len(_sub(s[3], s[2])); new[q] = (s[0], s[1], _sub(X1, _mul(u, h)), s[3])
            if cut.get('smooth_q') and _len(_sub(s[0], X2)) < 1e-6:
                h = _len(_sub(s[1], s[0])); new[q] = (s[0], _add(X2, _mul(u, h)), s[2], s[3])
        return new
    return None


def _node_turn(segs, k):
    """Turn in degrees at the node where segment k starts."""
    return _angle(_tan(segs[k-1], True), _tan(segs[k]))


def _terminal(segs, P, Q, cut):
    """A curved stroke end cut straight at AT-KPN's own tip. The reference cut flows out of the outer curve
    at one end (smooth) and meets the inner side in a crisp corner at the other. On AT-KPN the smooth end is
    the curve's extreme point along the cut; the rounded cap between that point and the inner side's corner
    is replaced by the straight cut, and the inner side runs straight on to meet it."""
    u = _unit(_sub(Q, P)); L = _len(_sub(Q, P)); n = len(segs)
    smooth_q = cut.get('smooth_q'); E_ref = Q if smooth_q else P
    best = None
    for k in range(n):                                              # extreme nodes with the cut's direction
        if len(segs[k]) != 4 and len(segs[k-1]) != 4: continue
        if abs(_node_turn(segs, k)) > 3 or abs(_angle(_tan(segs[k]), u)) > 4: continue
        d = _len(_sub(segs[k][0], E_ref))
        if d < 0.9*L+50 and (best is None or d < best[0]): best = (d, k)
    if best is None: return None
    e = best[1]; E = segs[e][0]
    step = -1 if smooth_q else 1                                    # walk from E over the cap to the inner side
    j = e; cap = []
    for _ in range(5):
        seg = (j-1) % n if step < 0 else j
        cap.append(seg)
        node = seg if step < 0 else (seg+1) % n                     # the far node of this cap segment
        if abs(_node_turn(segs, node)) > 25: break
        j = node
    else: return None
    K = segs[node][0]; side = (node-1) % n if step < 0 else node     # the inner side segment ending/starting at K
    if len(cap) > 4 or _len(_sub(K, E)) > 1.6*L+60: return None
    d = _tan(segs[side], True) if step < 0 else _mul(_tan(segs[side]), -1)
    C = _meet(K, d, E, u)
    if C is None or _dot(_sub(C, K), d) < -1 or _len(_sub(C, K)) > 0.5*L+20: return None
    bx = bbox([segs])
    if not (bx[0]-3 <= C[0] <= bx[2]+3 and bx[1]-3 <= C[1] <= bx[3]+3): return None   # the letter keeps its size
    if (_dot(_sub(E, C), u) <= 0) if step < 0 else (_dot(_sub(C, E), u) <= 0): return None
    out = []
    for k in range(n):
        if k in cap: continue
        out.append(segs[k])
        if step < 0 and k == side: out += [(K, C), (C, E)]
        if step > 0 and k == (e-1) % n: out += [(E, C), (C, K)]
    if step > 0 and e == 0: out = [(E, C), (C, K)] + out
    return [s for s in out if _len(_sub(s[-1], s[0])) > 0.05]


def recut(cs, cuts, box, rbox):
    """Ends AT-KPN strokes where the reference cuts them straight. Three ways, tried in order:
    a curved stroke end that the reference cuts flowing out of its outer curve is cut at AT-KPN's own tip
    (_terminal); a straight-sided stroke is extended to the cut line (diagonal strokes take level cuts this
    way); and a stroke that runs past the cut line is cut along it. The corners of each new cut get their sizes from apply() afterwards."""
    if not cuts: return cs, 0, []
    sx = (box[2]-box[0])/max(rbox[2]-rbox[0], 1); M = lambda p: (box[0]+(p[0]-rbox[0])*sx, p[1])
    done = 0; ends = []
    for cut in cuts:
        P, Q = M(cut['p']), M(cut['q']); L = _len(_sub(Q, P))
        if L < 20: continue
        u = _unit(_sub(Q, P)); nrm = (u[1], -u[0])                  # into the ink
        if any(len(s) == 2 and abs(_cross(u, _sub(s[0], P))) < 4 and abs(_cross(u, _sub(s[1], P))) < 4
               and _dot(_unit(_sub(s[1], s[0])), u) > .995 and min(_dot(_sub(s[1], P), u), L)-max(_dot(_sub(s[0], P), u), 0) > .5*L
               for segs in cs for s in segs):
            continue                                                # already a straight edge along this line
        for ci, segs in enumerate(cs):
            smooth = cut.get('smooth_p') or cut.get('smooth_q')
            for how in (('terminal',) if smooth else ('extend', 'cross')):
                if how == 'extend': new = _extend(segs, P, Q)
                elif how == 'terminal': new = _terminal(segs, P, Q, cut)
                else: new = _cross_cut(segs, P, u, L, cut)
                # an extension may only add a small wedge (on shallow diagonals it would widen the stroke)
                limit = 0.12*L*L if how == 'extend' else 0.9*L*L+L*40
                if new is not None and _clean(new) and _xor(segs, new) <= limit:
                    ends += [p for s in new for p in (s[0], s[-1]) if s not in segs]
                    cs[ci] = collapse(new); done += 1; break
            else: continue
            break
    return cs, done, ends


# ---------------------------------------------------------------- measuring the reference
def _sheet(paths):
    shapes = json.load(open(paths))
    def bb(s):
        pts = [tuple(p) for c in s for seg in c for p in seg[1:]]
        return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)
    items = sorted(((bb(s), s) for s in shapes), key=lambda it: -(it[0][1]+it[0][3])/2); rows = []
    for it in items:
        cy = (it[0][1]+it[0][3])/2
        if rows and abs(rows[-1]['cy']-cy) < 22: rows[-1]['items'].append(it)
        else: rows.append({'cy': cy, 'items': [it]})
    for r in rows: r['items'].sort(key=lambda it: it[0][0])
    return rows


def _segs(contour, T):
    segs = []; last = None; first = None
    for seg in contour:
        pts = [T(tuple(p)) for p in seg[1:]]
        if seg[0] == 'M': last = first = pts[0]
        elif seg[0] == 'L': segs.append((last, pts[0])); last = pts[0]
        else: segs.append((last, pts[0], pts[1], pts[2])); last = pts[2]
    if last != first: segs.append((last, first))
    return segs


def _area(segs):
    pts = [p for s in segs for p in (s[:1] if len(s) == 2 else [_point(s, k/8) for k in range(8)])]
    return sum(p[0]*q[1]-q[0]*p[1] for p, q in zip(pts, pts[1:]+pts[:1]))/2


def measure(paths, caps):
    """caps: {weight: AT-KPN cap height}; the sheet's H sets its scale."""
    rows = _sheet(paths); prof = {'tension_measured': {}, 'weights': {}}
    for wi, w in enumerate(WEIGHTS):
        H = rows[wi*3]['items'][CHARS[0].index('H')][0]; S = (H[3]-H[1])/caps[w]; out = {}; tens = []
        for ri in range(3):
            row = rows[wi*3+ri]['items']; ref = {0: 'H', 1: 'n', 2: '1'}[ri]; base = row[CHARS[ri].index(ref)][0][1]
            for (bb, shape), ch in zip(row, CHARS[ri]):
                T = lambda p: ((p[0]-bb[0])/S, (p[1]-base)/S)
                cs = [_segs(c, T) for c in shape]
                # outer contours run clockwise in AT-KPN; the sheet's direction is normalised to match
                big = max(cs, key=lambda c: abs(_area(c)))
                if _area(big) > 0: cs = [[tuple(s[::-1]) for s in c[::-1]] for c in cs]
                cs = [collapse(c) for c in cs]; found = glyph_corners(cs)
                for c in found:
                    s = [cs[c['contour']][g] for g in c['gap']]
                    if len(s) == 1 and len(s[0]) == 4 and min(c['a'], c['b']) > 8:
                        tens.append((_len(_sub(s[0][1], s[0][0]))/c['a']+_len(_sub(s[0][3], s[0][2]))/c['b'])/2)
                cuts = []
                for segs in cs:
                    m = len(segs)
                    for k, s in enumerate(segs):
                        if not _is_line(s) or not 25 <= _len(_sub(s[1], s[0])) <= 300: continue
                        u = _unit(_sub(s[1], s[0]))
                        def end(step):                          # turn into (step -1) or out of (step +1) the line
                            j = (k+step) % m; t = 0.0
                            while len(segs[j]) == 2 and _len(_sub(segs[j][1], segs[j][0])) < 8 and j != k:
                                d = _unit(_sub(segs[j][1], segs[j][0])); t += _angle(d, u) if step < 0 else _angle(u, d); j = (j+step) % m
                            if step < 0: return _angle(_tan(segs[j], True), u)
                            return _angle(u, _tan(segs[j]))
                        tp, tq = end(-1), end(1)
                        crisp = lambda t: t < -40
                        smooth = lambda t: abs(t) < 8
                        if (crisp(tp) or crisp(tq)) and (crisp(tp) or smooth(tp)) and (crisp(tq) or smooth(tq)):
                            cuts.append({'p': [round(s[0][0]), round(s[0][1])], 'q': [round(s[1][0]), round(s[1][1])],
                                         'smooth_p': smooth(tp), 'smooth_q': smooth(tq)})
                out[ch] = {'box': [round(v) for v in bbox(cs)], 'cuts': cuts,
                           'corners': [{'v': [round(c['V'][0]), round(c['V'][1])], 'd1': [round(v, 3) for v in c['d1']],
                                        'd2': [round(v, 3) for v in c['d2']], 'turn': round(c['turn']), 'a': round(c['a']), 'b': round(c['b'])}
                                       for c in found]}
        prof['weights'][w] = out
        tens.sort(); prof['tension_measured'][w] = round(tens[len(tens)//2], 3) if tens else None
    return prof


def load():
    return json.loads(PROFILE.read_text())['weights'] if PROFILE.exists() else {}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--measure', metavar='PATHS_JSON', help='path data extracted from the reference sheet')
    a = ap.parse_args()
    if a.measure:
        prof = measure(a.measure, {'Bold': 690, 'Regular': 685, 'Light': 685})
        prof = {'note': 'Corner positions and setbacks measured from the reference outline sheet, in AT-KPN units. '
                        'Scalars only; no outline data. Used by tools/corner_match.py.', **prof}
        PROFILE.write_text(json.dumps(prof, indent=1)+'\n')
        n = sum(len(v['corners']) for w in prof['weights'].values() for v in w.values())
        print('wrote', PROFILE, n, 'corners; tension', prof['tension_measured'])
