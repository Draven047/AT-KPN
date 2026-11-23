"""Create WOFF/WOFF2 exports and the combined CFF OTF from released outlines."""
from pathlib import Path
import hashlib, json
from fontTools.ttLib import TTFont
from export_language_fonts import cff_export

ROOT = Path(__file__).resolve().parents[1]
reports = []
inputs = [(p.parent.name, p) for p in sorted((ROOT/'TTF').glob('*/*.ttf'))]
inputs += [('All-languages', p) for p in sorted((ROOT/'desktop').glob('*.ttf'))]
for language, path in inputs:
    original = TTFont(path)
    for flavor in ['woff', 'woff2']:
        folder = ROOT/'web'/language
        folder.mkdir(parents=True, exist_ok=True)
        output = folder/(path.stem+'.'+flavor)
        font = TTFont(path, recalcTimestamp=False)
        font.flavor = flavor
        font.save(output)
        result = TTFont(output)
        assert original.getBestCmap() == result.getBestCmap()
        for tag in ['glyf', 'hmtx', 'GSUB', 'GPOS', 'GDEF']:
            assert original[tag].compile(original) == result[tag].compile(result), (output,tag)
        reports.append({'file':str(output.relative_to(ROOT)), 'pass':True, 'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
    if language == 'All-languages':
        cff_export(path, path.with_suffix('.otf'))
        result = TTFont(path.with_suffix('.otf'))
        assert result.sfntVersion == 'OTTO' and 'CFF ' in result
        for tag in ['hmtx', 'GSUB', 'GPOS', 'GDEF']:
            assert original[tag].compile(original) == result[tag].compile(result)
        reports.append({'file':str(path.with_suffix('.otf').relative_to(ROOT)), 'pass':True, 'sha256':hashlib.sha256(path.with_suffix('.otf').read_bytes()).hexdigest()})
(ROOT/'qa/web-exports.json').write_text(json.dumps({'pass':True,'files':reports,'scope':'WOFF and WOFF2 lossless outline and layout comparison; combined OTF CFF format and layout preservation.'},indent=2)+'\n')
print('Prepared and checked',len(reports),'additional font files.')
