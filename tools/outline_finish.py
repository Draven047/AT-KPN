"""Analytic outline finishing for AT-KPN.

Every step works on the drawn nodes themselves, so a glyph keeps its node structure:
no boolean or stroke operation re-traces the outline. Contours are lists of segments,
(p0, p1) lines or (p0, c1, c2, p3) cubics, as produced by fit_concept.read().

  wind()      outer contours clockwise, counters counter-clockwise
  tidy()      drop degenerate segments
  smooth()    make near-smooth nodes exactly smooth; extrema exactly horizontal/vertical
  terminals() one shape for every square stem end: flat cut, one crisp corner, one large soft corner
  embolden()  parallel offset by a few units (Tiller-Hanson control-polygon offset, mitred corners)
  headline()  thicken a headline downward
  quality()   outline statistics used by tools/check_outlines.py
"""
import math

SMOOTH_MAX = 12.0     # a node turning less than this many degrees is meant to be smooth
SNAP = 3.0            # a smooth extremum within this many degrees of an axis is put on the axis
CORNER = 25.0         # a node turning more than this is a drawn corner


def _sub(a, b): return (a[0]-b[0], a[1]-b[1])
def _add(a, b): return (a[0]+b[0], a[1]+b[1])
def _mul(a, k): return (a[0]*k, a[1]*k)
def _len(a): return math.hypot(a[0], a[1])
def _dot(a, b): return a[0]*b[0]+a[1]*b[1]
def _cross(a, b): return a[0]*b[1]-a[1]*b[0]


def _unit(a):
    l = _len(a); return (a[0]/l, a[1]/l) if l > 1e-9 else (0.0, 0.0)


def tangent(s, end=False):
    """Unit tangent at the start or the end of a segment (travel direction)."""
    pts = s[::-1] if end else s
    for q in pts[1:]:
        v = _sub(q, pts[0])
        if _len(v) > 1e-6: break
    return _unit(_mul(v, -1) if end else v)


def turn(a, b):
    """Signed angle in degrees from direction a to direction b."""
    return math.degrees(math.atan2(_cross(a, b), _dot(a, b)))


def point(s, t):
    if len(s) == 2: return (s[0][0]+(s[1][0]-s[0][0])*t, s[0][1]+(s[1][1]-s[0][1])*t)
    m = 1-t; return tuple(m**3*s[0][i]+3*m*m*t*s[1][i]+3*m*t*t*s[2][i]+t**3*s[3][i] for i in (0, 1))


def polygon(segs, n=8):
    out = []
    for s in segs:
        out += [s[0]] if len(s) == 2 else [point(s, k/n) for k in range(n)]
    return out


def signed_area(segs):
    """Exact signed area; clockwise contours are negative."""
    from fontTools.pens.areaPen import AreaPen
    pen = AreaPen(); pen.moveTo(segs[0][0])
    for s in segs: pen.lineTo(s[1]) if len(s) == 2 else pen.curveTo(*s[1:])
    pen.closePath(); return pen.value


def _inside(p, poly):
    x, y = p; c = False; j = len(poly)-1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi: c = not c
        j = i
    return c


def reverse(segs):
    return [tuple(reversed(s)) for s in reversed(segs)]


def wind(cs):
    """Outer contours clockwise (negative area), counters counter-clockwise, by nesting depth."""
    polys = [polygon(c) for c in cs]; out = []
    for i, c in enumerate(cs):
        probe = point(c[0], 0.5)
        depth = sum(1 for j, q in enumerate(polys) if j != i and _inside(probe, q))
        a = signed_area(c)
        want_negative = depth % 2 == 0
        out.append(reverse(c) if (a < 0) != want_negative and abs(a) > 1e-6 else c)
    return out


def tidy(segs, eps=0.6):
    """Remove segments shorter than eps (neighbours join at their start) and points inside straight lines."""
    out = []
    for s in segs:
        if all(_len(_sub(q, s[0])) < eps for q in s[1:]): continue
        out.append(tuple(s))
    for i in range(len(out)):                                   # re-close the chain exactly
        s = out[i]; nxt = out[(i+1) % len(out)]
        if s[-1] != nxt[0]: out[i] = s[:-1]+(nxt[0],)
    merged = []                                                 # a point in the middle of a straight line is redundant
    for s in out:
        if merged and len(s) == 2 and len(merged[-1]) == 2 and abs(turn(tangent(merged[-1]), tangent(s))) < 0.05:
            merged[-1] = (merged[-1][0], s[1])
        else: merged.append(s)
    if len(merged) > 2 and len(merged[0]) == 2 and len(merged[-1]) == 2 and abs(turn(tangent(merged[-1]), tangent(merged[0]))) < 0.05:
        merged[0] = (merged[-1][0], merged[0][1]); merged.pop()
    return merged


def smooth(segs, lo=0.05, hi=SMOOTH_MAX, snap=SNAP):
    """Give every near-smooth node one tangent direction; put smooth extrema on the axes."""
    segs = [list(s) for s in segs]; n = len(segs)
    for i in range(n):
        a, b = segs[i-1], segs[i]; p = b[0]
        if len(a) == 2 and len(b) == 2: continue
        ta, tb = tangent(a, True), tangent(b)
        t = turn(ta, tb)
        if abs(t) > hi: continue
        la = _len(_sub(a[3], a[2])) if len(a) == 4 else 0.0
        lb = _len(_sub(b[1], b[0])) if len(b) == 4 else 0.0
        if len(a) == 2: d = ta
        elif len(b) == 2: d = tb
        else:
            if la < 0.5 or lb < 0.5: continue                    # a retracted handle: nothing to rotate
            d = _unit(_add(_mul(ta, la), _mul(tb, lb)))
            ang = math.degrees(math.atan2(d[1], d[0])) % 90.0
            if min(ang, 90.0-ang) <= snap:
                ax = (round(d[0]), 0.0) if abs(d[0]) > abs(d[1]) else (0.0, round(d[1]))
                nrm = (-ax[1], ax[0]); sa = _dot(_sub(a[0], p), nrm); sb = _dot(_sub(b[-1], p), nrm)
                if sa*sb > 0 and min(abs(sa), abs(sb)) > 1.0: d = ax   # both neighbours on one side: an extremum
        if abs(t) < lo and d == ta: continue
        if len(a) == 4 and la >= 0.5: a[2] = _sub(p, _mul(d, la))
        if len(b) == 4 and lb >= 0.5: b[1] = _add(p, _mul(d, lb))
    return [tuple(s) for s in segs]


SOFT_CUT = 0.56       # soft corner of a stem end: reach along the cut, in stem widths
SOFT_SIDE = 0.65      # ... and along the side of the stem
SOFT_HANDLE = 0.542   # handle on the side, as a share of the reach; the cut handle runs to the corner


def terminals(segs, skip=None):
    """Redraw square stem ends in one shape: a flat cut, one crisp corner and one large soft corner.

    A stem end is a short run between two straight, anti-parallel sides that already has exactly one
    crisp right-angle corner. Its other corner, however it was drawn (small arc, bulged cut), becomes
    the family's soft corner, sized from the stem width. skip(direction, corner) can exclude an end.
    """
    n = len(segs)
    if n < 4: return segs
    ends = {}; starts = {}; runs = {}; used = set()
    for i in range(n):
        s1 = segs[i]
        if len(s1) != 2 or i in used: continue
        d = tangent(s1); l1 = _len(_sub(s1[1], s1[0]))
        if l1 < 30: continue
        u = (d[1], -d[0])                                           # across the stem: the ink is on the right
        for count in range(2, 13):
            j = (i+1+count) % n; s2 = segs[j]
            if j == i: break
            if len(s2) != 2 or _dot(tangent(s2), d) > -0.9995: continue
            l2 = _len(_sub(s2[1], s2[0])); w = _dot(_sub(s2[0], s1[1]), u)
            if not 24 <= w <= 320 or min(l1, l2) < 0.5*w: break
            idx = [(i+1+k) % n for k in range(count)]
            if j in used or any(k in used or k in ends or k in starts for k in idx): break
            pts = [q for k in idx for q in segs[k]]
            along = [_dot(_sub(q, s1[1]), d) for q in pts]; across = [_dot(_sub(q, s1[1]), u) for q in pts]
            if min(across) < -2.5 or max(across) > w+2.5 or min(along) < -0.8*w or max(along) > 0.8*w: break
            sharp = []; flag = []
            for k in range(count+1):                                # nodes from the end of side 1 to the start of side 2
                a = segs[(i+k) % n]; b = segs[(i+1+k) % n]; t = turn(tangent(a, True), tangent(b))
                if t < -72: sharp.append((a[-1], t))
                elif t < -60: flag.append((a[-1], t))               # a slanted start of a soft corner
                elif t > 20: sharp = None; break                    # a notch: not a plain stem end
            if sharp is None: break
            if not sharp and len(flag) == 1: sharp = flag           # ... or the stem's only corner
            if len(sharp) != 1 or sharp[0][1] < -105: break
            c = sharp[0][0]; cut = _dot(_sub(c, s1[1]), d); ca = _dot(_sub(c, s1[1]), u)
            first = ca < w/2                                        # crisp corner on side 1?
            if abs(ca-(0 if first else w)) > 2.5: break
            bulge = max(along)-cut
            if bulge > 0.14*w: break                                # a real round cap, not a cut
            if skip and skip(d, c): break
            tip = _add(s1[1], _mul(d, cut))
            if abs(d[0]) < 1e-6 and abs(tip[1]) <= 3: cut -= tip[1]*d[1]      # a foot stands on the baseline
            else:
                if bulge > 6: cut += bulge                          # any other bulged end keeps its full reach
                tip = _add(s1[1], _mul(d, cut))                     # upright and level stems end on whole units
                if abs(d[0]) < 1e-6: cut += (round(tip[1])-tip[1])*d[1]
                elif abs(d[1]) < 1e-6: cut += (round(tip[0])-tip[0])*d[0]
            # the soft corner may use half of its side (the other half belongs to the stem's other end)
            room = l2/2+cut-_dot(_sub(s2[0], s1[1]), d) if first else l1/2+cut
            if room < 0.3*w: break
            b_len = min(SOFT_SIDE*w, room); a_len = min(SOFT_CUT*w, b_len*SOFT_CUT/SOFT_SIDE)
            o = s1[1]; at = lambda al, ac: _add(o, _add(_mul(d, al), _mul(u, ac)))
            if first:
                c1 = at(cut, 0); v = at(cut, w); pc = at(cut, w-a_len); pa = at(cut-b_len, w)
                ends[i] = c1; starts[j] = pa
                runs[i] = [(c1, pc), (pc, v, at(cut-b_len*(1-SOFT_HANDLE), w), pa)]
            else:
                v = at(cut, 0); c2 = at(cut, w); pa = at(cut-b_len, 0); pc = at(cut, a_len)
                ends[i] = pa; starts[j] = c2
                runs[i] = [(pa, at(cut-b_len*(1-SOFT_HANDLE), 0), v, pc), (pc, c2)]
            used.update(idx); break
    if not runs: return segs
    out = []
    for i, s in enumerate(segs):
        if i in used: continue
        if i in starts or i in ends: s = (starts.get(i, s[0]), ends.get(i, s[1]))
        out.append(s)
        if i in runs: out += runs[i]
    return out


def _line_hit(p, d, q, e):
    """Intersection of lines p + s d and q + t e, or None when (nearly) parallel."""
    den = _cross(d, e)
    if abs(den) < 1e-3: return None
    s = _cross(_sub(q, p), e)/den; return _add(p, _mul(d, s))


def embolden(segs, w, miter=3.0):
    """Offset a contour outward (into the white) by w units; correct for small w on smooth outlines.

    Clockwise outer contours and counter-clockwise counters both have the ink on the right,
    so the offset direction is always the left normal.
    """
    if abs(w) < 1e-6: return segs
    left = lambda t: (-t[1], t[0])
    n = len(segs); nodes = []
    for i in range(n):
        a, b = segs[i-1], segs[i]; p = b[0]; ta, tb = tangent(a, True), tangent(b)
        hit = _line_hit(_add(p, _mul(left(ta), w)), ta, _add(p, _mul(left(tb), w)), tb) if abs(turn(ta, tb)) > 1.0 else None
        q = _add(p, _mul(_unit(_add(left(ta), left(tb))), w))
        if hit is not None and _len(_sub(hit, p)) <= miter*abs(w): q = hit
        nodes.append(q)
    out = []
    for i, s in enumerate(segs):
        p0, p3 = nodes[i], nodes[(i+1) % n]
        if len(s) == 2: out.append((p0, p3)); continue
        legs = [(s[k], _sub(s[k+1], s[k])) for k in range(3)]
        off = []
        for (o, v) in legs:
            u = _unit(v); off.append((_add(o, _mul(left(u), w)), u) if _len(v) > 1e-6 else None)
        def ctrl(k, fallback_leg):
            l1, l2 = off[k], off[k+1]
            if l1 is not None and l2 is not None:
                h = _line_hit(l1[0], l1[1], l2[0], l2[1])
                if h is not None and _len(_sub(h, s[k+1])) <= 4*abs(w)+2: return h
            l = off[fallback_leg] or off[1] or off[0] or off[2]
            return _add(s[k+1], _mul(left(l[1]), w)) if l else s[k+1]
        c1 = ctrl(0, 0); c2 = ctrl(1, 2)
        # keep the end tangents: handles stay on the (offset) tangent lines through the new nodes
        t0, t1 = tangent(s), tangent(s, True)
        c1 = _add(p0, _mul(t0, max(_dot(_sub(c1, p0), t0), 0.0))) if _len(_sub(s[1], s[0])) > 1e-6 else p0
        c2 = _add(p3, _mul(t1, min(_dot(_sub(c2, p3), t1), 0.0))) if _len(_sub(s[3], s[2])) > 1e-6 else p3
        out.append((p0, c1, c2, p3))
    return out


def headline(cs, hb, d):
    """Move headline undersides (leftward horizontal lines at y = hb, on clockwise contours) down by d."""
    out = []
    for segs in cs:
        segs = [list(s) for s in segs]; n = len(segs); moved = set()
        for i, s in enumerate(segs):
            if len(s) == 2 and abs(s[0][1]-hb) < 1.5 and abs(s[1][1]-hb) < 1.5 and s[0][0]-s[1][0] > 20: moved |= {i, (i+1) % n}
        for i in moved:                                          # node i = start of segment i
            a, b = segs[i-1], segs[i]; sh = lambda q: (q[0], q[1]-d)
            b[0] = sh(b[0]); a[-1] = b[0]
            if len(b) == 4 and abs(b[1][1]-hb) < d+40: b[1] = sh(b[1])
            if len(a) == 4 and abs(a[2][1]-hb) < d+40: a[2] = sh(a[2])
        out.append([tuple(s) for s in segs])
    return out


def finish(cs, weight_offset=0.0, headline_y=None, headline_extra=0.0, skip=None):
    """Winding, stem ends, headline, weight and node quality, in that order."""
    cs = wind([c for c in (tidy(c) for c in cs) if len(c) > 1])
    cs = [terminals(c, skip) for c in cs]
    if headline_y is not None and headline_extra: cs = headline(cs, headline_y, headline_extra)
    if weight_offset: cs = [embolden(c, weight_offset) for c in cs]
    return [smooth(c) for c in cs]


def quality(cs):
    """Counts used to judge outline quality."""
    q = {'nodes': 0, 'kinks': 0, 'gentle_corners': 0, 'short': 0, 'offaxis': 0, 'corners': 0}
    for segs in cs:
        n = len(segs); q['nodes'] += n
        for i in range(n):
            a, b = segs[i-1], segs[i]
            if _len(_sub(b[-1], b[0])) < 3.0: q['short'] += 1
            t = abs(turn(tangent(a, True), tangent(b)))
            if t > CORNER: q['corners'] += 1
            elif t > SMOOTH_MAX: q['gentle_corners'] += 1
            elif t > 1.5 and (len(a) == 4 or len(b) == 4): q['kinks'] += 1
            if len(a) == 4 and len(b) == 4 and t <= 1.5:
                d = tangent(b); ang = math.degrees(math.atan2(d[1], d[0])) % 90.0; off = min(ang, 90.0-ang)
                if 0.3 < off <= SNAP: q['offaxis'] += 1
    return q
