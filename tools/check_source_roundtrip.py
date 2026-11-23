"""Prove that the shipped editable sources reproduce every component glyph."""
import hashlib,json,subprocess,sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from build_family import ROOT,SCRIPTS,CFG

def snapshot():
 out={}
 for w in CFG['weights']:
  for s in SCRIPTS:
   p=ROOT/'build/components'/f'AT-KPN{s}-{w}.ttf';f=TTFont(p);gs=f.getGlyphSet();glyphs={}
   for n in f.getGlyphOrder():
    pen=DecomposingRecordingPen(gs);gs[n].draw(pen);glyphs[n]=hashlib.sha256(repr((pen.value,f['hmtx'][n])).encode()).hexdigest()
   out[p.name]={'glyphs':glyphs,'tables':{tag:hashlib.sha256(f[tag].compile(f)).hexdigest() for tag in ['GSUB','GPOS','GDEF','cmap'] if tag in f}}
 return out
before=snapshot();p=subprocess.run([sys.executable,str(ROOT/'tools/compile_edited.py')],cwd=ROOT)
assert p.returncode==0
results=[]
for name,now in snapshot().items():
 old=before[name];changed=[n for n,digest in old['glyphs'].items() if now['glyphs'].get(n)!=digest];tables=[t for t,digest in old['tables'].items() if now['tables'].get(t)!=digest]
 results.append({'font':name,'glyphs':len(old['glyphs']),'changed_glyphs':changed,'changed_layout_tables':tables,'pass':not changed and not tables})
report={'pass':all(r['pass'] for r in results),'components':results,'scope':'All 21 UFOs and layout TTX files recompiled; exact outline command, advance, bearing, cmap and layout table comparison.'}
(ROOT/'qa/source-roundtrip.json').write_text(json.dumps(report,indent=2)+'\n');print('Editable source round trip:',report['pass'])
if not report['pass']:sys.exit(1)
