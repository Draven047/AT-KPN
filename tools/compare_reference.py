"""Prove the released Bold against the approved Study 02 concept artwork.

Outputs
  specimen/AT-KPN-concept-sheet.png    the concept sheet next to the same sheet set in AT-KPN
  specimen/AT-KPN-concept-overlay.png  each word overlaid (red = concept only, blue = font only)
  qa/visual-comparison.json            overlap (IoU) per word after whole-pixel alignment
"""
from pathlib import Path
import hashlib, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont
from render_proofs import draw_text

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'design/config.json').read_text())
ROWS = [('English','en','Hello',(255,145,900,275)),('Kannada','kn','ನಮಸ್ಕಾರ',(255,309,900,454)),('Hindi','hi','नमस्ते',(255,481,900,615)),
        ('Marathi','mr','नमस्कार',(255,680,900,782)),('Malayalam','ml','നമസ്കാരം',(255,827,920,947)),('Tamil','ta','வணக்கம்',(255,986,930,1104)),
        ('Telugu','te','నమస్కారం',(255,1138,900,1278)),('Bengali','bn','নমস্কার',(255,1320,900,1437))]
LABEL = lambda n: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', n)


def mask(im): return im.convert('L').point(lambda p: 255 if p < 128 else 0)
def trim(im): return im.crop(mask(im).getbbox())
def sameheight(im, h): return im.resize((round(im.width*h/im.height), h), Image.Resampling.LANCZOS)


def render(path, text, lang, size=600):
    im = Image.new('RGB', (size*len(text)+800, size*3), 'white')
    draw_text(im, path, size, text, 200, int(size*1.8), lang, color='black')
    return trim(im)


def stroke(a):
    """Median stroke thickness (px): twice the distance to the edge along ridge pixels."""
    dt = ndimage.distance_transform_edt(a); ridge = (dt == ndimage.maximum_filter(dt, size=3)) & (dt > 1)
    return float(np.median(2*dt[ridge])) if ridge.any() else 0.0


def font_for(language):
    return ROOT/'TTF'/language/f'AT-KPN-{language}-Bold.ttf'


def placed(concept, language, lang, text, box):
    """Font word at the size and position that best overlaps the concept word (size within 5%)."""
    crop = concept.crop(box); bb = mask(crop).getbbox(); ref = np.asarray(mask(crop.crop(bb))) > 0
    base = sameheight(render(font_for(language), text, lang), ref.shape[0])
    best = (-1,)
    pad = 12
    for k in np.arange(0.95, 1.051, 0.01):
        word = base.resize((max(1, round(base.width*k)), max(1, round(base.height*k))), Image.Resampling.LANCZOS)
        w = np.asarray(mask(word)) > 0
        H = max(ref.shape[0], w.shape[0])+2*pad; Wd = max(ref.shape[1], w.shape[1])+2*pad
        A = np.zeros((H, Wd), bool); A[pad:pad+ref.shape[0], pad:pad+ref.shape[1]] = ref
        for dx in range(-8, 9):
            for dy in range(-6, 7):
                B = np.zeros((H, Wd), bool); y0 = pad+dy; x0 = pad+dx
                B[y0:y0+w.shape[0], x0:x0+w.shape[1]] = w
                iou = (A & B).sum()/(A | B).sum()
                if iou > best[0]: best = (iou, dx, dy, A, B, word)
    iou, dx, dy, A, B, word = best
    return word, (box[0]+bb[0]+dx, box[1]+bb[1]+dy), (iou, dx, A, B)


if __name__ == '__main__':
    concept = Image.open(ROOT/'design/approved-concept.png').convert('RGB')
    sheet = concept.copy()
    for *_, box in ROWS:                                   # clear the lettering, keep header and labels
        ImageDraw.Draw(sheet).rectangle((box[0], box[1], box[2]+60, box[3]), fill=concept.getpixel((1000, 5)))
    rows, tiles = [], []
    for language, lang, text, box in ROWS:
        word, pos, (iou, dx, A, B) = placed(concept, language, lang, text, box)
        sheet.paste(word, pos, mask(word))
        img = np.full(A.shape+(3,), 255, np.uint8); img[A & ~B] = (225, 55, 55); img[B & ~A] = (55, 105, 225); img[A & B] = (20, 20, 20)
        tiles.append((language, Image.fromarray(img), iou))
        sc, sf = stroke(A), stroke(B)
        rows.append({'language': language, 'text': text, 'iou': round(float(iou), 3), 'stroke_font_vs_concept': round(sf/sc, 3) if sc else None})
    d = ImageDraw.Draw(sheet); d.rectangle((40, 1480, 1000, 1530), fill='white')
    d.text((55, 1488), f'Set in AT-KPN {CFG["version"]} Bold, the actual font', font=LABEL(20), fill='#222')
    both = Image.new('RGB', (2*concept.width+60, concept.height+60), 'white'); b = ImageDraw.Draw(both)
    both.paste(concept, (0, 60)); both.paste(sheet, (concept.width+60, 60))
    b.text((20, 18), 'CONCEPT IMAGE', font=LABEL(24), fill='#555'); b.text((concept.width+80, 18), f'AT-KPN {CFG["version"]} FONT', font=LABEL(24), fill='#555')
    (ROOT/'specimen').mkdir(exist_ok=True); both.save(ROOT/'specimen/AT-KPN-concept-sheet.png')
    H = sum(t.height+40 for _, t, _ in tiles)+60; W = max(t.width for _, t, _ in tiles)*2+80
    ov = Image.new('RGB', (W, H), 'white'); o = ImageDraw.Draw(ov); y = 50
    o.text((20, 12), 'red = only in concept · blue = only in font · black = both', font=LABEL(20), fill='#444')
    for language, t, iou in tiles:
        ov.paste(t.resize((t.width*2, t.height*2), Image.Resampling.NEAREST), (20, y)); o.text((20, y+t.height*2+4), f'{language}: overlap {iou:.3f}', font=LABEL(16), fill='#444'); y += t.height*2+40
    ov = ov.crop((0, 0, W, y)); ov.save(ROOT/'specimen/AT-KPN-concept-overlay.png')
    report = {'version': CFG['version'], 'concept_sha256': hashlib.sha256((ROOT/'design/approved-concept.png').read_bytes()).hexdigest(),
              'method': 'Each concept word versus the same text in the Bold language font, at the size (within 5% of equal ink height) and whole-pixel position that overlap best; IoU of the binarised shapes.',
              'rows': rows, 'mean_iou': round(float(np.mean([r['iou'] for r in rows])), 3)}
    (ROOT/'qa/visual-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report['rows'], ensure_ascii=False), 'mean', report['mean_iou'])
