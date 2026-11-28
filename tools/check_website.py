"""Verify that every advertised download exists, is valid, and is packaged."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import hashlib,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
catalog=json.loads((DIST/'catalog.json').read_text())
assert len(catalog['languages'])==9
assert catalog['fileCount']==108
files=[]
for language in catalog['languages']:
    assert set(language['fonts'])=={'Light','Regular','Bold'}
    for weight,formats in language['fonts'].items():
        assert set(formats)=={'TTF','OTF','WOFF2','WOFF'}
        for fmt,data in formats.items():
            path=DIST/data['path'];blob=path.read_bytes()
            assert len(blob)==data['bytes']
            assert hashlib.sha256(blob).hexdigest()==data['sha256']
            assert blob[:4]=={'TTF':b'\x00\x01\x00\x00','OTF':b'OTTO','WOFF2':b'wOF2','WOFF':b'wOFF'}[fmt]
            files.append(data['path'])
bundles=list(catalog['bundles'].values())+[l['bundle'] for l in catalog['languages']]
for data in bundles:
    path=DIST/data['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==data['sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert {'OFL.txt','AUTHORS.md','FONT-README.txt'}<=set(z.namelist())
        for item in z.namelist():
            assert not item.startswith('/') and '..' not in Path(item).parts
            assert z.read(item)==(DIST/item).read_bytes()
        for name in z.namelist():
            if name.endswith('.css'):
                for url in re.findall(r"url\(['\"]?([^)'\"]+)",z.read(name).decode()):
                    assert url in z.namelist(),(path,name,url)
with zipfile.ZipFile(DIST/catalog['bundles']['complete']['path']) as z:
    assert set(files)<=set(z.namelist())
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        for key in ['href','src']:
            if key in attrs:self.links.append(attrs[key])
parser=Links();html=(DIST/'index.html').read_text();parser.feed(html)
assert len(parser.ids)==len(set(parser.ids))
assert '{{' not in html and '<!-- DOWNLOAD_ROWS -->' not in html
for href in parser.links:
    target=urlparse(href)
    if target.scheme or target.netloc:continue
    if target.path:assert (DIST/unquote(target.path)).is_file(),href
    elif target.fragment:assert target.fragment in parser.ids,href
for path in DIST.glob('*.css'):
    for url in re.findall(r"url\(['\"]?([^)'\"]+)",path.read_text()):
        assert (DIST/url).is_file(),(path,url)
glyphs=json.loads((DIST/'glyphs.json').read_text())
assert [s['id'] for s in glyphs['scripts']]==['Latin','Kannada','Devanagari','Malayalam','Tamil','Telugu','Bengali']
glyph_count=sum(len(g['chars']) for s in glyphs['scripts'] for g in s['groups'])
assert all(g['chars'] for s in glyphs['scripts'] for g in s['groups']) and glyph_count>350
assert all(len(ch)==1 and name for s in glyphs['scripts'] for g in s['groups'] for ch,name in g['chars'])
assert all(p.stat().st_size<25*1024*1024 for p in DIST.rglob('*') if p.is_file()),'Asset exceeds static hosting file limit'
report={'pass':True,'font_downloads':len(files),'zip_bundles':len(bundles),'explorer_characters':glyph_count,'scope':'All catalog hashes, font magic signatures, ZIP CRC/content/license/CSS dependencies, complete family contents, glyph explorer data and internal page links verified.'}
(ROOT/'qa/website-assets.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
