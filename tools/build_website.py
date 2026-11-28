"""Build a portable static specimen, catalog and self-contained download ZIPs."""
from pathlib import Path
import hashlib, json, shutil, unicodedata, zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT/'design/config.json').read_text())['version']
DIST = ROOT/'dist'
WEIGHTS = {'Light':300,'Regular':400,'Bold':700}
LANGUAGES = [
    ('English','English','en','Hello, world.'),
    ('Kannada','ಕನ್ನಡ','kn','ನಮಸ್ಕಾರ'),
    ('Hindi','हिन्दी','hi','नमस्ते'),
    ('Marathi','मराठी','mr','नमस्कार'),
    ('Malayalam','മലയാളം','ml','നമസ്കാരം'),
    ('Tamil','தமிழ்','ta','வணக்கம்'),
    ('Telugu','తెలుగు','te','నమస్కారం'),
    ('Bengali','বাংলা','bn','নমস্কার'),
    ('All-languages','All eight languages','en','Hello · ನಮಸ್ಕಾರ · नमस्ते'),
]

# Character sets for the glyph explorer: (id, label, lang tag, tab sample, groups).
# A group is a list of code point ranges (letters and digits only) or an explicit string.
GLYPH_SETS = [
    ('Latin','English','en','Aa',[('Uppercase',[(0x41,0x5B)]),('Lowercase',[(0x61,0x7B)]),('Digits',[(0x30,0x3A)]),
        ('Symbols','&@?!₹$€£%#*+=()'),('Accents','áàâäãåçéèêëíìîïñóòôöõúùûüýÿßæœø')]),
    ('Kannada','Kannada','kn','ಅ',[('Vowels',[(0xC85,0xC95)]),('Consonants',[(0xC95,0xCBA)]),('Digits',[(0xCE6,0xCF0)])]),
    ('Devanagari','Hindi · Marathi','hi','अ',[('Vowels',[(0x905,0x915)]),('Consonants',[(0x915,0x93A)]),('Digits',[(0x966,0x970)])]),
    ('Malayalam','Malayalam','ml','അ',[('Vowels',[(0xD05,0xD15)]),('Consonants',[(0xD15,0xD3B)]),('Chillus',[(0xD7A,0xD80)]),('Digits',[(0xD66,0xD70)])]),
    ('Tamil','Tamil','ta','அ',[('Vowels',[(0xB85,0xB95)]),('Consonants',[(0xB95,0xBBA)]),('Digits',[(0xBE6,0xBF0)])]),
    ('Telugu','Telugu','te','అ',[('Vowels',[(0xC05,0xC15)]),('Consonants',[(0xC15,0xC3A)]),('Digits',[(0xC66,0xC70)])]),
    ('Bengali','Bengali','bn','অ',[('Vowels',[(0x985,0x995)]),('Consonants',[(0x995,0x9BA),(0x9DC,0x9E0)]),('Digits',[(0x9E6,0x9F0)])]),
]

def glyph_data():
    scripts=[]
    for sid,label,tag,sample,groups in GLYPH_SETS:
        out=[]
        for name,spec in groups:
            ranged=isinstance(spec,list)
            chars=[chr(c) for a,b in spec for c in range(a,b)] if ranged else list(spec)
            rows=[]
            for ch in chars:
                cname=unicodedata.name(ch,'')
                if not cname or (ranged and unicodedata.category(ch) not in ('Lo','Lu','Ll','Nd')):continue
                rows.append([ch,cname])
            out.append({'name':name,'chars':rows})
        scripts.append({'id':sid,'label':label,'tag':tag,'sample':sample,'groups':out})
    return {'version':VERSION,'unicode':unicodedata.unidata_version,'scripts':scripts}

def describe(path):
    return {'path':path.relative_to(DIST).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def archive(name, files):
    output = DIST/'downloads'/name
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(set(files)):
            entry = zipfile.ZipInfo(path.relative_to(DIST).as_posix(),(2026,11,23,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o644 << 16
            z.writestr(entry,path.read_bytes())
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert 'OFL.txt' in z.namelist()
    return describe(output)

def build():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST/'downloads').mkdir()
    for p in (ROOT/'site').iterdir():
        if p.is_file(): shutil.copy2(p,DIST/p.name)
    for name in ['OFL.txt','AUTHORS.md','FONTLOG.md','PROVENANCE.md','LICENSE-CODE.txt']:
        shutil.copy2(ROOT/name,DIST/name)
    instructions = '''AT-KPN '''+VERSION+''' — eight languages, three weights

TTF and OTF are desktop font formats. Choose one format per family, open the
files and install them using your operating system's font manager.

WOFF2 and WOFF are web fonts. In a web or all-formats package, keep fonts/
beside the included AT-KPN*.css stylesheet, then link that stylesheet.
Use font-family: 'AT-KPN' for the combined family when included, or a language
family such as 'AT-KPN Kannada'. Available weights: 300, 400, 700.

Every Indian-language family includes English. Hindi and Marathi share the
Devanagari design. The combined family covers all eight languages in one font.
Malayalam's stacked alternate is available with font-feature-settings: 'ss01' 1.

Font software: SIL Open Font License 1.1. See OFL.txt and AUTHORS.md.
Source and contributions: https://github.com/Draven047/AT-KPN
'''
    (DIST/'FONT-README.txt').write_text(instructions)
    common=[DIST/n for n in ['OFL.txt','AUTHORS.md','FONT-README.txt']]
    catalog={'version':VERSION,'weights':WEIGHTS,'languages':[],'bundles':{},'repository':'https://github.com/Draven047/AT-KPN'}
    all_files=[]; css=[]
    for language,native,tag,sample in LANGUAGES:
        row={'id':language,'name':language.replace('-',' '),'native':native,'tag':tag,'sample':sample,'fonts':{}}
        lang_files=[]
        css_start=len(css)
        family='AT-KPN' if language=='All-languages' else 'AT-KPN '+language
        for weight,value in WEIGHTS.items():
            stem='AT-KPN-'+weight if language=='All-languages' else 'AT-KPN-'+language+'-'+weight
            row['fonts'][weight]={}
            for fmt in ['TTF','OTF','WOFF2','WOFF']:
                if fmt in ['TTF','OTF']:
                    source=ROOT/'desktop'/(stem+'.'+fmt.lower()) if language=='All-languages' else ROOT/fmt/language/(stem+'.'+fmt.lower())
                else: source=ROOT/'web'/language/(stem+'.'+fmt.lower())
                target=DIST/'fonts'/fmt/language/source.name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
                row['fonts'][weight][fmt]=describe(target)
                lang_files.append(target)
            w2=row['fonts'][weight]['WOFF2']['path'];w1=row['fonts'][weight]['WOFF']['path']
            css.append("@font-face{font-family:'%s';src:url('%s') format('woff2'),url('%s') format('woff');font-style:normal;font-weight:%s;font-display:swap;}"%(family,w2,w1,value))
        all_files+=lang_files
        language_css=DIST/('AT-KPN-'+language+'.css')
        language_css.write_text('\n'.join(css[css_start:])+'\n')
        row['bundle']=archive('AT-KPN-'+language+'-all-formats.zip',lang_files+common+[language_css])
        catalog['languages'].append(row)
    (DIST/'AT-KPN.css').write_text('\n'.join(css)+'\n')
    catalog['bundles']['complete']=archive('AT-KPN-'+VERSION+'-Complete.zip',all_files+common+[DIST/'AT-KPN.css'])
    for fmt in ['TTF','OTF']:
        catalog['bundles'][fmt.lower()]=archive('AT-KPN-'+VERSION+'-'+fmt+'.zip',[p for p in all_files if p.suffix=='.'+fmt.lower()]+common)
    catalog['bundles']['web']=archive('AT-KPN-'+VERSION+'-Web.zip',[p for p in all_files if p.suffix in ['.woff','.woff2']]+common+[DIST/'AT-KPN.css'])
    catalog['fileCount']=len(all_files)
    (DIST/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    (DIST/'glyphs.json').write_text(json.dumps(glyph_data(),ensure_ascii=False,separators=(',',':'))+'\n')
    rows=[]
    for row in catalog['languages']:
        links=''.join('<a class="weight-download" data-weight="%s" href="%s" download aria-label="Download %s %s TTF">%s<span>TTF</span></a>'%(w,row['fonts'][w]['TTF']['path'],row['name'],w,w) for w in WEIGHTS)
        rows.append('<div class="download-row" data-language="%s"><div class="download-language"><strong>%s</strong><span lang="%s">%s</span></div><div class="weight-downloads">%s</div><a class="bundle-link" href="%s" download aria-label="Download %s all weights and formats">Language ZIP</a></div>'%(row['id'],row['name'],row['tag'],row['native'],links,row['bundle']['path'],row['name']))
    html=(DIST/'index.html').read_text().replace('<!-- DOWNLOAD_ROWS -->','\n'.join(rows))
    html=html.replace('{{VERSION}}',VERSION)
    html=html.replace('{{COMPLETE_SIZE}}',str(round(catalog['bundles']['complete']['bytes']/1_000_000,1)))
    (DIST/'index.html').write_text(html)
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://at-kpn.vercel.app/sitemap.xml\n')
    (DIST/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://at-kpn.vercel.app/</loc></url></urlset>\n')
    (DIST/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/fonts/*\n  Cache-Control: public, max-age=86400\n')
    print('Built',len(all_files),'font downloads and',len(list((DIST/'downloads').glob('*.zip'))),'ZIP bundles.')
    print('Complete family:',round(catalog['bundles']['complete']['bytes']/1_000_000,1),'MB')

if __name__=='__main__':build()
