"""Draw the site's share image and icons in the dark hero style, from the built AT-KPN fonts.

Writes site/share.png (1200 x 630 link preview), site/favicon.svg, site/favicon.ico,
site/apple-touch-icon.png and site/icon-512.png. Run after the fonts are built:

    .venv/bin/python tools/make_share_art.py
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT/'site'
BOLD = ROOT/'TTF/English/AT-KPN-English-Bold.ttf'
REGULAR = ROOT/'TTF/English/AT-KPN-English-Regular.ttf'
BG, FG, ACCENT = (0, 0, 0), (255, 255, 255), (247, 225, 0)
# the hero draws English with the system monospace; fall back to AT-KPN where it is missing
MONO = next((p for p in ('/System/Library/Fonts/SFNSMono.ttf', '/System/Library/Fonts/Menlo.ttc') if Path(p).exists()), str(REGULAR))
MONO_CHARS = '#$%&*+=?@0123456789ABCDEFGHKMNOPQRSTUVWXYZabcdeghkmnopqrsuvwxyz:;<>[]{}/'


def share(path, word='Hello', scale=2, seed=7):
    rnd = random.Random(seed)
    W, H = 1200*scale, 630*scale
    img = Image.new('RGB', (W, H), BG)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    # dust, as in the hero
    for _ in range(170):
        z = rnd.random(); r = (1 + z*1.6)*scale; x, y = rnd.random()*W, rnd.random()*H
        d.rectangle([x, y, x+r, y+r], fill=FG+(int(255*(.08+.4*z)*.8),))
    # the word, set large and sampled into a field of small characters
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    size = 100; f = ImageFont.truetype(str(BOLD), size); bb = md.textbbox((0, 0), word, font=f)
    size = int(size*min(W*.80/(bb[2]-bb[0]), H*.46/(bb[3]-bb[1]))); f = ImageFont.truetype(str(BOLD), size)
    bb = md.textbbox((0, 0), word, font=f); cy = H*.5
    md.text(((W-(bb[2]-bb[0]))/2-bb[0], cy-(bb[3]-bb[1])/2-bb[1]), word, font=f, fill=255)
    px = mask.load(); step = 7.0*scale
    mono = ImageFont.truetype(MONO, int(11.5*scale))
    sweep = W*.63
    y, row = 0.0, 0
    while y < H:
        x = step/2 if row % 2 else 0.0
        while x < W:
            if px[int(x), int(y)] > 140:
                jx, jy = x+(rnd.random()-.5)*1.6*scale, y+(rnd.random()-.5)*1.6*scale
                lit = max(0.0, 1-abs(jx-sweep)/(150*scale))
                a = min(1.0, .42+rnd.random()*.58+lit*.5)
                col = ACCENT if lit > .28 and rnd.random() < .85 else FG
                d.text((jx, jy), rnd.choice(MONO_CHARS), font=mono, fill=col+(int(255*a),), anchor='mm')
            x += step
        y += step; row += 1
    img.paste(layer, (0, 0), layer); d = ImageDraw.Draw(img)
    # header: wordmark and the download pill
    m = 56*scale
    brand = ImageFont.truetype(str(BOLD), 34*scale); d.text((m, 50*scale), 'AT-KPN', font=brand, fill=FG, anchor='lm')
    pill = ImageFont.truetype(str(BOLD), 20*scale); label = 'Free download'
    tw = d.textlength(label, font=pill); pw, ph = tw+44*scale, 46*scale
    d.rounded_rectangle([W-m-pw, 50*scale-ph/2, W-m, 50*scale+ph/2], radius=ph/2, fill=ACCENT)
    d.text((W-m-pw/2, 50*scale), label, font=pill, fill=BG, anchor='mm')
    # footer, in the hero caption's manner
    cap = ImageFont.truetype(MONO, 15*scale); yb = H-52*scale
    d.text((m, yb), '01 / 08', font=cap, fill=(150, 150, 150), anchor='lm')
    d.text((m+d.textlength('01 / 08', font=cap)+22*scale, yb), 'ENGLISH', font=cap, fill=ACCENT, anchor='lm')
    tag = ImageFont.truetype(str(REGULAR), 22*scale)
    d.text((W-m, yb), 'A rounded typeface for eight languages · Designed by AT', font=tag, fill=(205, 205, 205), anchor='rm')
    img.resize((1200, 630), Image.LANCZOS).save(path, optimize=True)


def k_path(box=64, pad=13):
    """The Bold K as an SVG path, centred in a box of the given size."""
    font = TTFont(BOLD); gs = font.getGlyphSet(); g = gs[font.getBestCmap()[ord('K')]]
    bp = BoundsPen(gs); g.draw(bp); x0, y0, x1, y1 = bp.bounds
    s = (box-2*pad)/max(x1-x0, y1-y0); w, h = (x1-x0)*s, (y1-y0)*s
    tx, ty = (box-w)/2-x0*s, (box+h)/2+y0*s
    pen = SVGPathPen(gs, ntos=lambda v: f'{v:.2f}'.rstrip('0').rstrip('.'))
    g.draw(TransformPen(pen, (s, 0, 0, -s, tx, ty)))
    return pen.getCommands()


def icon_png(size, radius=.23):
    big = size*8
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big-1, big-1], radius=big*radius, fill=BG+(255,))
    f = ImageFont.truetype(str(BOLD), int(big*.66)); bb = d.textbbox((0, 0), 'K', font=f)
    d.text(((big-(bb[2]-bb[0]))/2-bb[0], (big-(bb[3]-bb[1]))/2-bb[1]), 'K', font=f, fill=ACCENT+(255,))
    return img.resize((size, size), Image.LANCZOS)


def main():
    share(SITE/'share.png')
    (SITE/'favicon.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="15" fill="#000"/><path fill="#f7e100" d="{k_path()}"/></svg>\n')
    icon_png(48).save(SITE/'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    icon_png(180, radius=0).save(SITE/'apple-touch-icon.png')
    icon_png(512).save(SITE/'icon-512.png')
    print('Wrote share.png, favicon.svg, favicon.ico, apple-touch-icon.png and icon-512.png in site/')


if __name__ == '__main__':
    main()
