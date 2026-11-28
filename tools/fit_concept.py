"""Fit AT-KPN Bold to the Study 02 concept artwork with clean, consistent changes.

Every concept word is shaped with the actual Bold component font and placed
over design/approved-concept.png at the same visible height. Two kinds of
change are then fitted to maximise overlap with the artwork:

* per concept letter: a smooth separable warp x' = x + fx(x), y' = y + fy(y)
  (stems stay vertical, curves smooth, baseline and headline pinned); marks and
  subscripts instead get a free quadratic 2D deformation; dots get their own
  size and position; detached marks (e.g. the chandrakkala) their own 2D shape;
* per script: the Bold weight (set from measured stroke thickness) and, for
  Devanagari, a thicker headline. Applying uses the analytic finishing in
  outline_finish.py; the fitted corner_radius is kept only for refitting.

Fitted values are saved in design/concept-fit.json and applied to the editable
sources of all three weights. Warps also reach glyphs that reuse a concept
glyph's contours verbatim (accented letters, conjunct parts). Run on the
committed 0.600 sources, then compile_edited.py.
"""
from pathlib import Path
import argparse, unicodedata, json, math
import numpy as np
import pathops
from PIL import Image
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.qu2cuPen import Qu2CuPen
from ufoLib2 import Font as UFO

import outline_finish
import corner_match

ROOT = Path(__file__).resolve().parents[1]
CONCEPT = ROOT/'design/approved-concept.png'
PARAMS = ROOT/'design/concept-fit.json'
# language, script component, language tag, text, crop box in the concept image
WORDS = [('English', 'Latin', 'en', 'Hello', (255, 145, 900, 275)),
         ('Kannada', 'Kannada', 'kn', 'ನಮಸ್ಕಾರ', (255, 309, 900, 454)),
         ('Hindi', 'Devanagari', 'hi', 'नमस्ते', (255, 481, 900, 615)),
         ('Marathi', 'Devanagari', 'mr', 'नमस्कार', (255, 680, 900, 782)),
         ('Malayalam', 'Malayalam', 'ml', 'നമസ്കാരം', (255, 827, 920, 947)),
         ('Tamil', 'Tamil', 'ta', 'வணக்கம்', (255, 986, 930, 1104)),
         ('Telugu', 'Telugu', 'te', 'నమస్కారం', (255, 1138, 900, 1278)),
         ('Bengali', 'Bengali', 'bn', 'নমস্কার', (255, 1320, 900, 1437))]
SCRIPTS = ['Latin', 'Kannada', 'Devanagari', 'Malayalam', 'Tamil', 'Telugu', 'Bengali']
WEIGHTS = ['Light', 'Regular', 'Bold']
UP = 4                 # concept upsampling factor
KX, KY = 7, 6          # warp knots across each glyph's width and height
PIN = 120.0            # warp falls to zero within this distance of an alignment line
# Bold weight change per script, set from the measured stroke thickness of the
# concept versus the font (qa/visual-comparison.json audit, 24 November 2026).
BOLD_WEIGHT = {'Latin': 0.0, 'Kannada': 0.0, 'Devanagari': 0.0, 'Malayalam': 2.0, 'Tamil': 4.0, 'Telugu': 10.0, 'Bengali': 2.0}
HEADLINE_EXTRA = {'Devanagari': 8.0}          # Bold headline thickened downward (units)
CORNER_STEPS = (10.0, 18.0, 26.0)           # candidate outer corner radius for Bold; inner corners get half
CORNER_SCALE = {'Light': 0.55, 'Regular': 0.75, 'Bold': 1.0}
NO_LETTER_FIT = {'Latin'}
FLEX = {'matraE.dv', 'Kasmall1.kn', 'Kasmall1.te'}   # marks/subscripts: free 2D deformation, no baseline pin


# ---------------------------------------------------------------- outlines
class Cubics(BasePen):
    """Contours as lists of segments: (p0, p1) lines or (p0, c1, c2, p3) cubics."""
    def __init__(self):
        super().__init__(None); self.contours = []; self.cur = None
    def _moveTo(self, p): self.cur = []; self.start = self.last = p
    def _lineTo(self, p):
        if p != self.last: self.cur.append((self.last, p))
        self.last = p
    def _curveToOne(self, a, b, c): self.cur.append((self.last, a, b, c)); self.last = c
    def _qCurveToOne(self, a, b):
        p0 = self.last
        self.cur.append((p0, (p0[0]+2/3*(a[0]-p0[0]), p0[1]+2/3*(a[1]-p0[1])), (b[0]+2/3*(a[0]-b[0]), b[1]+2/3*(a[1]-b[1])), b)); self.last = b
    def _closePath(self):
        if self.cur is not None:
            if self.last != self.start: self.cur.append((self.last, self.start))
            if self.cur: self.contours.append([tuple(map(tuple, s)) for s in self.cur])
        self.cur = None
    _endPath = _closePath


def read(glyph):
    pen = Cubics(); glyph.draw(pen); return pen.contours


def write(glyph, contours):
    glyph.clearContours(); pen = glyph.getPen()
    r = lambda p: (round(float(p[0]), 2), round(float(p[1]), 2))
    for segs in contours:
        pen.moveTo(r(segs[0][0]))
        for s in segs:
            pen.lineTo(r(s[1])) if len(s) == 2 else pen.curveTo(r(s[1]), r(s[2]), r(s[3]))
        pen.closePath()


def bez(s, t):
    if len(s) == 2: return tuple(s[0][i]+(s[1][i]-s[0][i])*t for i in (0, 1))
    m = 1-t; return tuple(m**3*s[0][i]+3*m*m*t*s[1][i]+3*m*t*t*s[2][i]+t**3*s[3][i] for i in (0, 1))


def tangent(s, t):
    if len(s) == 2: v = (s[1][0]-s[0][0], s[1][1]-s[0][1])
    else:
        m = 1-t; v = tuple(3*m*m*(s[1][i]-s[0][i])+6*m*t*(s[2][i]-s[1][i])+3*t*t*(s[3][i]-s[2][i]) for i in (0, 1))
        if math.hypot(*v) < 1e-6: v = (s[3][0]-s[0][0], s[3][1]-s[0][1])
    l = math.hypot(*v) or 1.0; return (v[0]/l, v[1]/l)


def area(segs):
    return sum(p[0]*q[1]-q[0]*p[1] for s in segs for p, q in zip(s, s[1:]))/2


# ---------------------------------------------------------------- placement
def shaped(path, text, lang):
    f = hb.Font(hb.Face(path.read_bytes())); b = hb.Buffer(); b.add_str(text); b.guess_segment_properties(); b.language = lang; hb.shape(f, b)
    t = TTFont(path); x = 0; run = []
    for i, p in zip(b.glyph_infos, b.glyph_positions):
        run.append((t.getGlyphName(i.codepoint), x+p.x_offset, p.y_offset)); x += p.x_advance
    return run


def concept_field(box):
    im = Image.open(CONCEPT).convert('L').crop(box)
    ink = 1-np.asarray(im, dtype=float)/255
    m = ink > 0.5; ys, xs = np.nonzero(m)
    big = ndimage.zoom(ink, UP, order=3); big = ndimage.gaussian_filter(big, UP*0.5)
    return big, (xs.min(), ys.min(), xs.max()+1, ys.max()+1), m


class Placement:
    """Maps font units of one shaped word onto concept crop pixels (y down)."""
    def __init__(self, ufo, run, box):
        self.field, bb, self.mask = concept_field(box)
        self.items = [(name, x, y, read(ufo[name])) for name, x, y in run]
        bp = BoundsPen(None); self.draw(bp, lambda p: p)                      # exact ink bounds
        xmin, ymin, xmax, ymax = bp.bounds
        self.ax, self.ay = xmin, ymax                                         # ink left / top, font units
        self.s = (bb[3]-bb[1])/(ymax-ymin)
        self.bx, self.by = bb[0], bb[1]
        best = (-1, 0, 0); base = (self.bx, self.by)
        for dx in range(-4, 5):
            for dy in range(-3, 4):
                self.bx, self.by = base[0]+dx, base[1]+dy
                a = self.raster(); iou = (a & self.mask).sum()/(a | self.mask).sum()
                if iou > best[0]: best = (iou, dx, dy)
        self.iou = best[0]; self.bx, self.by = base[0]+best[1], base[1]+best[2]

    def draw(self, pen, f, items=None):
        for _, x, y, cs in (self.items if items is None else items):
            for segs in cs:
                pen.moveTo(f((segs[0][0][0]+x, segs[0][0][1]+y)))
                for s in segs:
                    q = [f((p[0]+x, p[1]+y)) for p in s[1:]]
                    pen.lineTo(q[0]) if len(s) == 2 else pen.curveTo(*q)
                pen.closePath()

    def to_px(self, p, x=0, y=0):
        return (self.bx+(p[0]+x-self.ax)*self.s, self.by+(self.ay-(p[1]+y))*self.s)

    def raster(self, items=None):
        H, W = self.mask.shape; pen = FreeTypePen(None)
        self.draw(pen, lambda p: (lambda q: (q[0], H-q[1]))(self.to_px(p)), items)
        return np.asarray(pen.array(width=W, height=H, contain=False)) > 0.5


# ---------------------------------------------------------------- changes
def bbox(cs):
    xs = [q[0] for sg in cs for s in sg for q in s]; ys = [q[1] for sg in cs for s in sg for q in s]
    return min(xs), min(ys), max(xs), max(ys)


def offset(cs, w):
    """Exact outline offset by w units (positive = heavier) using Skia path ops."""
    if abs(w) < 0.5 or not cs: return cs
    p = pathops.Path(); pen = p.getPen()
    for segs in cs:
        pen.moveTo(segs[0][0])
        for s in segs: pen.lineTo(s[1]) if len(s) == 2 else pen.curveTo(*s[1:])
        pen.closePath()
    p.simplify(fix_winding=True, keep_starting_points=False)
    st = pathops.Path(p); st.stroke(2*abs(w), pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4); st.convertConicsToQuads(0.25)
    res = pathops.op(p, st, pathops.PathOp.UNION if w > 0 else pathops.PathOp.DIFFERENCE, fix_winding=True, clockwise=True)
    out = Cubics(); res.draw(out); return out.contours


class Warp:
    """Separable smooth warp of one glyph; displacement fades out at alignment lines."""
    def __init__(self, kx, dx, ky, dy, pins):
        self.kx, self.dx, self.ky, self.dy = np.asarray(kx, float), np.asarray(dx, float), np.asarray(ky, float), np.asarray(dy, float)
        self.pins = list(pins)

    @classmethod
    def around(cls, cs, pins):
        x0, y0, x1, y1 = bbox(cs)
        return cls(np.linspace(x0, x1, KX), np.zeros(KX), np.linspace(min(y0, 0.0), y1, KY), np.zeros(KY), pins)

    def displace(self, pts):
        x, y = pts[:, 0], pts[:, 1]
        fx = PchipInterpolator(self.kx, self.dx, extrapolate=True)(x)
        fyc = PchipInterpolator(self.ky, self.dy, extrapolate=True); fy = fyc(y)
        for p in self.pins:
            fy = fy-float(fyc(p))*np.clip(1-np.abs(y-p)/PIN, 0, None)
        return np.stack([fx, fy], 1)

    def key(self): return (tuple(self.dx), tuple(self.dy))
    def params(self): return [self.dx, self.dy]
    def penalty(self):
        m = np.abs(np.diff(self.dx, 2)).sum()+np.abs(np.diff(self.dy, 2)).sum()
        return m+0.1*(abs(self.dx.mean())+abs(self.dy.mean()))+0.2*(np.abs(self.dx-self.dx.mean()).sum()+np.abs(self.dy-self.dy.mean()).sum())

    def as_dict(self):
        return {'kx': [round(v, 2) for v in self.kx], 'dx': [round(v, 2) for v in self.dx],
                'ky': [round(v, 2) for v in self.ky], 'dy': [round(v, 2) for v in self.dy], 'pins': self.pins}


class FFD:
    """Move/scale plus quadratic Bernstein free-form deformation over a box (3x3 control displacements)."""
    def __init__(self, box, d=None, a=None):
        x0, y0, x1, y1 = box; mx, my = 0.1*(x1-x0)+20, 0.1*(y1-y0)+20
        self.box = (x0-mx, y0-my, x1+mx, y1+my); self.d = np.zeros((3, 3, 2)) if d is None else np.asarray(d, float)
        self.a = np.zeros(4) if a is None else np.asarray(a, float)          # [dx, dy, x scale %, y scale %]

    def displace(self, pts):
        x0, y0, x1, y1 = self.box
        u = np.clip((pts[:, 0]-x0)/(x1-x0), 0, 1); v = np.clip((pts[:, 1]-y0)/(y1-y0), 0, 1)
        Bu = np.stack([(1-u)**2, 2*u*(1-u), u**2], 1); Bv = np.stack([(1-v)**2, 2*v*(1-v), v**2], 1)
        c = np.array([(x0+x1)/2, (y0+y1)/2])
        whole = (pts-c)*(self.a[2:]/100)+self.a[:2]
        return whole+np.einsum('ni,nj,ijk->nk', Bu, Bv, self.d)

    def key(self): return tuple(self.d.ravel())+tuple(self.a)
    def params(self): return [self.a, self.d.reshape(-1)]
    def penalty(self):
        return (0.15*np.abs(self.d).sum()+0.3*np.abs(np.diff(self.d, axis=0)).sum()+0.3*np.abs(np.diff(self.d, axis=1)).sum()
                + 0.05*np.abs(self.a[:2]).sum()+0.5*np.abs(self.a[2:]).sum())
    def as_dict(self): return {'box': [round(v, 2) for v in self.box], 'd': np.round(self.d, 2).tolist(), 'a': np.round(self.a, 2).tolist()}

    @classmethod
    def load(cls, d):
        f = cls((0, 0, 1, 1)); f.box = tuple(d['box']); f.d = np.asarray(d['d'], float); f.a = np.asarray(d.get('a', [0, 0, 0, 0]), float); return f


class Dot:
    """Similarity change of one solid dot: scale about its centre plus a shift."""
    def __init__(self, v=None): self.v = np.zeros(3) if v is None else np.asarray(v, float)   # [scale-1 (x100), dx, dy]
    def apply(self, pts):
        c = pts.mean(axis=0); return c+(pts-c)*(1+self.v[0]/100)+self.v[1:]
    def key(self): return tuple(self.v)
    def params(self): return [self.v]
    def penalty(self): return 0.2*np.abs(self.v).sum()
    def as_dict(self): return {'v': np.round(self.v, 2).tolist()}


def is_dot(segs, others):
    x0, y0, x1, y1 = bbox([segs])
    return (area(segs) < 0 and max(x1-x0, y1-y0) < 250 and 0.8 < (x1-x0)/max(y1-y0, 1) < 1.25 and all(len(s) == 4 for s in segs)
            and not any(b[0] >= x0 and b[1] >= y0 and b[2] <= x1 and b[3] <= y1 for b in others))


def is_mark(segs, cs):
    """Small detached contour sitting above the main body (e.g. the Malayalam chandrakkala)."""
    main = max(cs, key=lambda c: abs(area(c))); mb = bbox([main]); b = bbox([segs])
    return segs is not main and b[1] > mb[3]-60 and max(b[2]-b[0], b[3]-b[1]) < 420


class GlyphFit:
    """All fitted changes for one concept glyph."""
    def __init__(self, cs, pins, name):
        self.flex = name in FLEX
        self.warp = None if self.flex else Warp.around(cs, pins)
        self.ffd = FFD(bbox(cs)) if self.flex else None
        self.contours = {}
        boxes = [bbox([c]) for c in cs]
        for i, c in enumerate(cs):
            if is_dot(c, [b for j, b in enumerate(boxes) if j != i]): self.contours[i] = Dot()
            elif not self.flex and len(cs) > 1 and is_mark(c, cs): self.contours[i] = FFD(bbox([c]))

    def parts(self):
        return [x for x in [self.warp, self.ffd] if x is not None]+list(self.contours.values())

    def key(self): return tuple(p.key() for p in self.parts())
    def penalty(self): return sum(p.penalty() for p in self.parts())

    def contour(self, i, segs, shift=(0.0, 0.0)):
        """Transform one contour (index i of the concept glyph), optionally translated by shift."""
        pts = np.array([q for s in segs for q in s], float)-np.asarray(shift)
        if self.warp is not None:
            d = self.warp.displace(pts)
            if isinstance(self.contours.get(i), Dot): d = np.repeat(d.mean(axis=0, keepdims=True), len(d), 0)
            pts = pts+d
        if self.ffd is not None: pts = pts+self.ffd.displace(pts)
        part = self.contours.get(i)
        if isinstance(part, Dot): pts = part.apply(pts)
        elif isinstance(part, FFD): pts = pts+part.displace(pts)
        pts = pts+np.asarray(shift); out = []; k = 0
        for s in segs:
            out.append(tuple(tuple(map(float, pts[k+j])) for j in range(len(s)))); k += len(s)
        return out

    def __call__(self, cs): return [self.contour(i, c) for i, c in enumerate(cs)]

    def as_dict(self):
        return {'warp': self.warp.as_dict() if self.warp else None, 'ffd': self.ffd.as_dict() if self.ffd else None,
                'contours': {str(i): ({'dot': p.as_dict()} if isinstance(p, Dot) else {'ffd': p.as_dict()}) for i, p in self.contours.items()}}

    @classmethod
    def load(cls, d):
        g = cls.__new__(cls); g.flex = d['ffd'] is not None
        g.warp = Warp(d['warp']['kx'], d['warp']['dx'], d['warp']['ky'], d['warp']['dy'], d['warp']['pins']) if d['warp'] else None
        g.ffd = FFD.load(d['ffd']) if d['ffd'] else None
        g.contours = {int(i): (Dot(v['dot']['v']) if 'dot' in v else FFD.load(v['ffd'])) for i, v in d['contours'].items()}
        return g


# ---------------------------------------------------------------- whole-glyph finishing
def _path(cs):
    p = pathops.Path(); pen = p.getPen()
    for segs in cs:
        pen.moveTo(segs[0][0])
        for s in segs: pen.lineTo(s[1]) if len(s) == 2 else pen.curveTo(*s[1:])
        pen.closePath()
    p.simplify(fix_winding=True, keep_starting_points=False, clockwise=True); return p


def _grow(p, w):
    st = pathops.Path(p); st.stroke(2*abs(w), pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4); st.convertConicsToQuads(0.25)
    return pathops.op(p, st, pathops.PathOp.UNION if w > 0 else pathops.PathOp.DIFFERENCE, fix_winding=True, clockwise=True)


def _contours(p):
    out = Cubics(); p.draw(out); return out.contours


def ink_area(cs):
    from fontTools.pens.areaPen import AreaPen
    pen = AreaPen()
    for segs in cs:
        pen.moveTo(segs[0][0])
        for s in segs: pen.lineTo(s[1]) if len(s) == 2 else pen.curveTo(*s[1:])
        pen.closePath()
    return abs(pen.value)


def _soften_path(p, r):
    """Round convex corners to at least r and concave corners to r/2; keep p if topology would change."""
    if r < 0.5: return p
    try:
        before = _contours(p)
        closed = _grow(_grow(_grow(_grow(p, -r), r), r/2), -r/2)
        after = _contours(closed)
    except Exception:
        return p
    if len(after) != len(before) or abs(ink_area(after)-ink_area(before)) > 0.04*ink_area(before): return p
    return closed


def soften(cs, r):
    return _contours(_soften_path(_path(cs), r)) if cs else cs


def _headline_path(p, cs, hb, d):
    """Extend headline undersides (leftward horizontal segments at y = hb) down by d units."""
    rects = []
    for segs in cs:
        for s in segs:
            if len(s) == 2 and abs(s[0][1]-hb) < 1.5 and abs(s[1][1]-hb) < 1.5 and s[0][0]-s[1][0] > 20:
                x0, x1 = s[1][0], s[0][0]
                rects.append([((x0, hb), (x0, hb-d)), ((x0, hb-d), (x1, hb-d)), ((x1, hb-d), (x1, hb)), ((x1, hb), (x0, hb))])
    if not rects: return p
    return pathops.op(p, _path(rects), pathops.PathOp.UNION, fix_winding=True, clockwise=True)


def headline_bottom(ufo, top):
    from collections import Counter
    ys = Counter()
    for g in ufo:
        for segs in read(g):
            for s in segs:
                if len(s) == 2 and abs(s[0][1]-s[1][1]) < 0.5 and s[0][0]-s[1][0] > 60 and top-200 < s[0][1] < top-40:
                    ys[round(s[0][1])] += 1
    return float(ys.most_common(1)[0][0]) if ys else None


def finish_path(cs, script, weight, corner, hb):
    """Script-wide finishing applied to every glyph: headline, weight, corners (in that order). Returns a Skia path."""
    p = _path(cs)
    if weight == 'Bold' and hb is not None and script in HEADLINE_EXTRA: p = _headline_path(p, cs, hb, HEADLINE_EXTRA[script])
    if weight == 'Bold' and BOLD_WEIGHT.get(script): p = _grow(p, BOLD_WEIGHT[script])
    return _soften_path(p, corner*CORNER_SCALE[weight])


def overlapping(cs):
    """True when contours overlap or cross, so the union differs from the drawn area."""
    if len(cs) < 2: return False
    try:
        drawn = abs(sum(outline_finish.signed_area(c) for c in outline_finish.wind(cs)))
        union = ink_area(_contours(_path(cs)))
    except Exception:
        return False
    return abs(drawn-union) > 0.002*union+20


def finish(cs, script, weight, corner, hb):
    return _contours(finish_path(cs, script, weight, corner, hb)) if cs else cs


def alignment_lines(ufo, script):
    """Heights that must not move: the baseline, plus the headline top for Devanagari/Bengali."""
    lines = [0.0]
    if script in ('Devanagari', 'Bengali'):
        from collections import Counter
        ys = Counter()
        for g in ufo:
            for segs in read(g):
                for s in segs:
                    # top edges of the headline run rightward (TrueType order: ink on the right, i.e. below)
                    if len(s) == 2 and abs(s[0][1]-s[1][1]) < 0.5 and s[1][0]-s[0][0] > 150 and s[0][1] > 400:
                        ys[round(s[0][1])] += 1
        if ys: lines.append(float(ys.most_common(1)[0][0]))
    return lines


def signature(segs):
    if not segs: return None
    x0, y0 = segs[0][0]
    return tuple(tuple((round(p[0]-x0, 1), round(p[1]-y0, 1)) for p in s) for s in segs)


def score(pls, base, shapes):
    tot = []
    for pl, b in zip(pls, base):
        pl.items = [(n, x, y, shapes[n] or cs) for n, x, y, cs in b]
        a = pl.raster(); tot.append((a & pl.mask).sum()/(a | pl.mask).sum())
    return float(np.mean(tot)), [float(v) for v in tot]


def fit_script(script):
    words = [w for w in WORDS if w[1] == script]
    ufo = UFO.open(ROOT/'sources/editable'/f'AT-KPN{script}-Bold.ufo'); comp = ROOT/'build/components'/f'AT-KPN{script}-Bold.ttf'
    pins = alignment_lines(ufo, script); hb = headline_bottom(ufo, pins[-1]) if len(pins) > 1 else None
    pls = [Placement(ufo, shaped(comp, w[3], w[2]), w[4]) for w in words]; base = [list(pl.items) for pl in pls]
    names = sorted({it[0] for pl in pls for it in pl.items}); orig = {n: read(ufo[n]) for n in names}
    before = score(pls, base, orig)
    fits = {n: GlyphFit(orig[n], pins, n) for n in names if orig[n]}
    state = {'corner': 0.0}; cache = {}
    class Shapes(dict):
        def __missing__(self, n):
            if not orig[n]: return orig[n]
            key = (n, state['corner'], fits[n].key())
            if key not in cache: cache[key] = finish(fits[n](orig[n]), script, 'Bold', state['corner'], hb)
            return cache[key]
    shapes = Shapes()
    best = None
    for r in CORNER_STEPS:                                 # corner softness for this script
        state['corner'] = r; v = score(pls, base, shapes)[0]
        if best is None or v > best[0]: best = (v, r)
    state['corner'] = best[1]
    pen = lambda: sum(f.penalty() for f in fits.values())/len(fits)/4000
    cur = score(pls, base, shapes)[0]-pen()
    for step in (48.0, 24.0, 12.0, 6.0, 3.0):
        for _ in range(2):
            for n, f in fits.items():
                for part in f.parts():
                    for arr in part.params():
                        if step > 24 and not isinstance(part, FFD): continue  # big moves only for marks/subscripts
                        scale = 0.25 if isinstance(part, Dot) else 1.0          # dot scale is in percent
                        for k in range(len(arr)):
                            for sgn in (1, -1):
                                arr[k] += sgn*step*scale; v = score(pls, base, shapes)[0]-pen()
                                if v > cur+1e-4: cur = v
                                else: arr[k] -= sgn*step*scale
    after = score(pls, base, shapes)
    print(script, 'IoU', [round(v, 3) for v in before[1]], '->', [round(v, 3) for v in after[1]], 'corner', state['corner'], flush=True)
    return {'words': [w[0] for w in words], 'iou_before': [round(v, 3) for v in before[1]], 'iou_after': [round(v, 3) for v in after[1]],
            'bold_weight_offset': BOLD_WEIGHT[script], 'headline_extra': HEADLINE_EXTRA.get(script, 0.0), 'corner_radius': state['corner'],
            'glyphs': {n: f.as_dict() for n, f in fits.items()}}


SHARED = {0x20, 0xA0, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x25CC, 0x964, 0x965}


def apply(params, scripts=SCRIPTS, weights=WEIGHTS):
    """Apply fitted glyph changes (all weights), then script-wide finishing to every glyph."""
    report = {}
    for script in scripts:
        p = params[script]
        for weight in weights:
            path = ROOT/'sources/editable'/f'AT-KPN{script}-{weight}.ufo'; ufo = UFO.open(path)
            pins = alignment_lines(ufo, script); hb = headline_bottom(ufo, pins[-1]) if len(pins) > 1 else None
            # English follows the scalar reference proportions instead of the concept letter warps;
            # it still gets the script-wide corner finishing below.
            fits = {} if script in NO_LETTER_FIT else {n: GlyphFit.load(d) for n, d in p['glyphs'].items() if n in ufo}
            sig = {}                                        # contours reused verbatim elsewhere follow their owner
            for n in fits:
                for i, c in enumerate(read(ufo[n])):
                    k = signature(c)
                    if k: sig.setdefault(k, (n, i, c[0][0]))
            shared = finished = merged = 0
            # Headline ends meet the next letter's headline, so they keep their drawn shape.
            keep_headline = (lambda d, c: abs(d[1]) < 0.3 and hb-30 <= c[1] <= pins[-1]+8) if hb is not None else None
            # The drawn English M, W and w cut their slanted strokes level with the baseline or top line;
            # a stem-end redraw would cut them square to the stroke instead, so they keep their drawn ends.
            level = lambda d, c: abs(d[0]) > 0.02 and abs(d[1]) > 0.02
            # English letters and figures take the reference corner sizes (tools/corner_match.py); accented
            # letters reuse their base letter's redrawn contours, so they are handled after the bases.
            corners = corner_match.load().get(weight, {}) if script == 'Latin' else {}
            base_of = lambda g: chr(g.unicodes[0]) if g.unicodes and chr(g.unicodes[0]) in corners else None
            accented = lambda g: unicodedata.normalize('NFD', chr(g.unicodes[0]))[0] if g.unicodes else None
            redrawn = corner_match.Redrawn(); boxes = {}; cornered = 0
            for g in sorted(ufo, key=lambda g: base_of(g) is None):
                cs = read(g)
                if not cs: continue
                if g.name in fits: cs = fits[g.name](cs)
                else:
                    out = []; hit = False
                    for c in cs:
                        k = signature(c)
                        if k in sig:
                            n, i, origin = sig[k]; out.append(fits[n].contour(i, c, (c[0][0][0]-origin[0], c[0][0][1]-origin[1]))); hit = True
                        else: out.append(c)
                    cs = out; shared += hit
                protect = script != 'Latin' and any(u < 0x900 or u in SHARED for u in g.unicodes)
                if protect: write(g, [outline_finish.smooth(c) for c in outline_finish.wind([outline_finish.tidy(c) for c in cs])]); continue
                # Finishing is analytic: the drawn nodes are kept, so corners stay as drawn (one crisp,
                # one round at a stroke end) and curves keep their extrema. Only the rare glyph built
                # from overlapping pieces is merged with Skia first.
                if overlapping(cs): cs = _contours(_path(cs)); merged += 1
                skip = level if script == 'Latin' and any(unicodedata.normalize('NFD', chr(u))[0] in 'MWwKN' for u in g.unicodes) else keep_headline
                cs = outline_finish.finish(cs, BOLD_WEIGHT.get(script, 0.0) if weight == 'Bold' else 0.0,
                                           hb if weight == 'Bold' and script in HEADLINE_EXTRA else None, HEADLINE_EXTRA.get(script, 0.0), skip)
                if corners:
                    ch = base_of(g)
                    if ch:
                        new, k = corner_match.apply(cs, corners[ch]); cornered += k
                        for c, d in zip(cs, new): redrawn.add(c, d)
                        cs = new; boxes[ch] = corner_match.bbox(cs)
                    else:
                        got = [redrawn.get(c) for c in cs]; b = accented(g)
                        # an accented letter whose letter part differs from its base (an attached cedilla,
                        # an older drawing) has its own corners matched, at the base letter's position
                        if b in boxes and all(x is c for x, c in zip(got, cs)):
                            got, k = corner_match.apply(cs, corners[b], box=boxes[b]); cornered += k
                        cs = got
                    cs = [outline_finish.smooth(c) for c in cs]
                write(g, cs); finished += 1
            ufo.save(path, overwrite=True)
            report[f'{script}-{weight}'] = {'fitted_glyphs': len(fits), 'shared_contour_glyphs': shared, 'finished_glyphs': finished,
                                            'weight_offset': BOLD_WEIGHT[script] if weight == 'Bold' else 0.0,
                                            'merged_overlaps': merged, **({'reference_corners': cornered} if corners else {})}
            print(script, weight, report[f'{script}-{weight}'], flush=True)
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--fit', action='store_true', help='refit parameters from the concept (needs build/components from the 0.600 sources)')
    ap.add_argument('--apply', action='store_true', help='apply design/concept-fit.json to sources/editable')
    ap.add_argument('--scripts', nargs='+', default=SCRIPTS, choices=SCRIPTS, help='with --apply: only these freshly regenerated scripts')
    ap.add_argument('--weights', nargs='+', default=WEIGHTS, choices=WEIGHTS, help='with --apply: only these freshly regenerated weights')
    a = ap.parse_args()
    if a.fit:
        params = {s: fit_script(s) for s in SCRIPTS}
        PARAMS.write_text(json.dumps(params, ensure_ascii=False, indent=1)+'\n')
    if a.apply:
        report = apply(json.loads(PARAMS.read_text()), a.scripts, a.weights)
        out = ROOT/'qa/concept-fit.json'
        if out.exists() and (a.scripts != SCRIPTS or a.weights != WEIGHTS):   # partial run: keep the other entries
            report = {**json.loads(out.read_text())['applied'], **report}
        out.write_text(json.dumps({'parameters': 'design/concept-fit.json', 'applied': report}, indent=2)+'\n')
