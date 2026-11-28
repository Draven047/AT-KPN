"""Export the current family into TTF/ and genuine CFF OTF/ language folders.

Keeps the released multilingual fonts intact. Native exports include the Latin
component, all native shaping features and the optional Malayalam ss01 form.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

import cffsubr
import ots
import uharfbuzz as hb
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.basePen import BasePen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

from build_family import ROOT, CFG, TAGS
from validate_family import cases, resource, shape

LANGUAGES = {
    'English': ('Latin', 'en'),
    'Kannada': ('Kannada', 'kn'),
    'Hindi': ('Devanagari', 'hi'),
    'Marathi': ('Devanagari', 'mr'),
    'Malayalam': ('Malayalam', 'ml'),
    'Tamil': ('Tamil', 'ta'),
    'Telugu': ('Telugu', 'te'),
    'Bengali': ('Bengali', 'bn'),
}


def rename(font, language, weight):
    family = 'AT-KPN ' + language
    ps = 'AT-KPN-' + language + '-' + weight
    values = {
        1: family + ' Light' if weight == 'Light' else family,
        2: 'Regular' if weight == 'Light' else weight,
        3: CFG['version'] + ';ATKP;' + ps,
        4: family + ' ' + weight,
        6: ps,
        16: family,
        17: weight,
    }
    for nid, value in values.items():
        font['name'].removeNames(nameID=nid)
        for platform, encoding, lang in [(3, 1, 0x409), (1, 0, 0)]:
            font['name'].setName(value, nid, platform, encoding, lang)


def cff_export(ttf_path, otf_path):
    font = TTFont(ttf_path, recalcTimestamp=False)
    glyphs = font.getGlyphSet()
    charstrings = {}
    for name in font.getGlyphOrder():
        # BasePen converts each quadratic to an equivalent cubic. Control points
        # are rounded to whole units (at most 0.5 units, i.e. 1/2000 em), as in
        # standard CFF fonts; this keeps the OTF downloads within hosting limits.
        pen = T2CharStringPen(font['hmtx'][name][0], glyphs, roundTolerance=0.5)
        glyphs[name].draw(pen)
        # Preserve individual segments, including upstream backtracking lines.
        # CFF optimization can otherwise collapse those small outline details.
        charstrings[name] = pen.getCharString(optimize=False)
    for tag in ['glyf', 'loca', 'maxp', 'fpgm', 'prep', 'cvt ', 'gasp', 'hdmx', 'LTSH', 'VDMX']:
        if tag in font:
            del font[tag]
    builder = FontBuilder(font=font)
    builder.setupCFF(font['name'].getDebugName(6), {
        'version': CFG['version'],
        'FullName': font['name'].getDebugName(4),
        'FamilyName': font['name'].getDebugName(16),
        'Weight': font['name'].getDebugName(17),
        'Notice': font['name'].getDebugName(0),
        'isFixedPitch': False,
        'ItalicAngle': 0,
        'UnderlinePosition': font['post'].underlinePosition,
        'UnderlineThickness': font['post'].underlineThickness,
    }, charstrings, {})
    builder.setupMaxp()
    font['post'].formatType = 3.0
    font['head'].indexToLocFormat = 0
    # Lossless CFF subroutinization keeps downloads within hosting limits.
    cffsubr.subroutinize(font)
    font.save(otf_path)


class CubicPen(BasePen):
    """Canonical commands for verifying quadratic-to-cubic outline geometry."""
    def __init__(self, glyphs):
        super().__init__(glyphs)
        self.commands = []

    def _moveTo(self, pt): self.commands.append(('M', pt))
    def _lineTo(self, pt):
        # CFF specialization removes intermediate points on a straight line.
        # Normalize that lossless simplification on both sides of the check.
        if len(self.commands) >= 2 and self.commands[-1][0] == 'L':
            before = self.commands[-2]
            if before[0] in ('M', 'L', 'C'):
                a, b = before[-1], self.commands[-1][-1]
                v, w = (b[0]-a[0], b[1]-a[1]), (pt[0]-b[0], pt[1]-b[1])
                if abs(v[0]*w[1]-v[1]*w[0]) < 1e-6 and v[0]*w[0]+v[1]*w[1] >= 0:
                    self.commands.pop()
        self.commands.append(('L', pt))
    def _curveToOne(self, a, b, c): self.commands.append(('C', a, b, c))
    def _closePath(self): self.commands.append(('Z',))
    def _endPath(self): self.commands.append(('E',))


def commands(glyphs, name):
    pen = CubicPen(glyphs)
    glyphs[name].draw(pen)
    return pen.commands


def outline_error(first, second):
    if len(first) != len(second):
        return float('inf')
    maximum = 0.0
    for a, b in zip(first, second):
        if a[0] != b[0] or len(a) != len(b):
            return float('inf')
        for p, q in zip(a[1:], b[1:]):
            maximum = max(maximum, abs(p[0]-q[0]), abs(p[1]-q[1]))
    return maximum


def alternate_shape(font, path, text, lang):
    h = hb.Font(hb.Face(path.read_bytes()))
    hb.ot_font_set_funcs(h)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.language = lang
    hb.shape(h, buffer, {'ss01': 1})
    return [(font.getGlyphName(i.codepoint), i.cluster, p.x_advance,
             p.y_advance, p.x_offset, p.y_offset)
            for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def export():
    reports = []
    for weight in CFG['weights']:
        original_path = ROOT/'desktop'/('AT-KPN-' + weight + '.ttf')
        original, original_hb = resource(original_path)
        original_glyphs = original.getGlyphSet()
        latin_cmap = TTFont(ROOT/'build/components'/('AT-KPNLatin-' + weight + '.ttf')).getBestCmap()
        for language, (script, lang) in LANGUAGES.items():
            native_cmap = TTFont(ROOT/'build/components'/('AT-KPN' + script + '-' + weight + '.ttf')).getBestCmap()
            keep = set(latin_cmap) | set(native_cmap)
            font = TTFont(original_path, recalcTimestamp=False)
            options = subset.Options()
            options.glyph_names = True
            options.name_IDs = ['*']
            options.name_languages = ['*']
            options.name_legacy = True
            options.layout_features = ['*']
            options.layout_scripts = sorted(TAGS['Latin'] | TAGS[script])
            options.notdef_glyph = True
            options.notdef_outline = True
            options.hinting = False
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(unicodes=keep)
            subsetter.subset(font)
            rename(font, language, weight)
            filename = 'AT-KPN-' + language + '-' + weight
            paths = {}
            for fmt in ['TTF', 'OTF']:
                folder = ROOT/fmt/language
                folder.mkdir(parents=True, exist_ok=True)
                paths[fmt] = folder/(filename + '.' + fmt.lower())
            font.save(paths['TTF'])
            cff_export(paths['TTF'], paths['OTF'])
            test_cases = cases(script, native_cmap)
            if script != 'Latin':
                test_cases += cases('Latin', latin_cmap)
            for fmt, path in paths.items():
                result, result_hb = resource(path)
                errors = []
                if set(result.getBestCmap()) != keep:
                    errors.append('Unicode coverage changed')
                if fmt == 'OTF' and (result.sfntVersion != 'OTTO' or 'CFF ' not in result or 'glyf' in result):
                    errors.append('Not a CFF OpenType font')
                max_error = 0.0
                out_glyphs = result.getGlyphSet()
                for name in result.getGlyphOrder():
                    delta = outline_error(commands(original_glyphs, name), commands(out_glyphs, name))
                    max_error = max(max_error, delta)
                    if delta > 0.51:
                        errors.append('Outline differs: ' + name)
                    if result['hmtx'][name] != original['hmtx'][name]:
                        errors.append('Metrics differ: ' + name)
                for text, case_lang, kind in test_cases:
                    before = shape(original, original_hb, text, case_lang)
                    after = shape(result, result_hb, text, case_lang)
                    if before != after or any(r[0] == '.notdef' for r in after):
                        errors.append('Shaping differs: ' + text)
                if script == 'Malayalam':
                    for text in ['നമസ്കാരം', 'സ്ക സ്കാ സ്കി സ്കീ സ്കു സ്കൂ സ്കെ സ്കേ സ്കൊ സ്കോ സ്കൗ']:
                        if alternate_shape(original, original_path, text, lang) != alternate_shape(result, path, text, lang):
                            errors.append('Malayalam alternate differs')
                with tempfile.TemporaryDirectory(prefix='atkpn-ots-') as tmp:
                    checked = subprocess.run([ots.OTS_SANITIZE, str(path), str(Path(tmp)/path.name)], capture_output=True, text=True)
                if checked.returncode:
                    errors.append('OpenType Sanitizer rejected font: ' + checked.stderr.strip())
                report = {'file': str(path.relative_to(ROOT)), 'pass': not errors,
                          'glyphs': len(result.getGlyphOrder()), 'unicode_characters': len(keep),
                          'shaping_cases': len(test_cases), 'max_outline_control_point_error_units': max_error,
                          'sanitizer_exit_code': checked.returncode, 'errors': errors[:20],
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                reports.append(report)
                print(report['file'], 'PASS' if report['pass'] else 'FAIL', report['errors'], flush=True)
    report = {'pass': all(r['pass'] for r in reports), 'version': CFG['version'], 'files': reports,
              'scope': '48 language fonts; exact Unicode/metric/shaping preservation, CFF outline geometry within 0.5 units (whole-unit coordinates), native alternate retention and OpenType Sanitizer. Native exports include English.'}
    (ROOT/'qa/language-exports.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    assert report['pass'], 'Language export validation failed; see qa/language-exports.json'
    (ROOT/'LANGUAGE-FONTS.sha256').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in reports))
    print('Validated', len(reports), 'fonts.', flush=True)


if __name__ == '__main__':
    export()
