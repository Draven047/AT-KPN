"""Independent source, merge, portability and repertoire checks for AT-KPN."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,math,subprocess,sys,unicodedata
import uharfbuzz as hb,ots
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from build_family import ROOT,CFG,SCRIPTS,BLOCKS,source_path
from samples import SAMPLES
ENGLISH=['ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz','0123456789','Fresh ideas. Friendly forms.','AT-KPN — English and Indian languages','Hamburgefontsiv','office affine difficult fluff','AVATAR WA To Ta Yo Te VA AW','Café naïve façade résumé Noël Ångström','₹ 1,250.00 £ € $ 50% (offer) [new]','Gill Jill ill fill minimum giggling','Héllo rôle élève','Ĥ q̈ x̄ g̤ c̤̏']

def resource(path):
 t=TTFont(path);h=hb.Font(hb.Face(path.read_bytes()));hb.ot_font_set_funcs(h);return t,h

def shape(t,h,text,lang):
 b=hb.Buffer();b.add_str(text);b.guess_segment_properties();b.language=lang;hb.shape(h,b)
 return [(t.getGlyphName(i.codepoint),i.cluster,p.x_advance,p.y_advance,p.x_offset,p.y_offset) for i,p in zip(b.glyph_infos,b.glyph_positions)]

def cases(script,cmap):
 if script=='Latin':return [(s,'en','sample') for s in ENGLISH]
 rows=[r for r in SAMPLES if r['script']==script];out=[(r[k],r['lang'],'sample') for r in rows for k in ['title','text','clusters']];lang=rows[0]['lang'];lo,hi=BLOCKS[script]
 letters=[chr(cp) for cp in range(lo+0x15,lo+0x3A) if cp in cmap and unicodedata.category(chr(cp))=='Lo'];signs=[chr(cp) for cp in range(lo+0x3E,lo+0x4D) if cp in cmap and unicodedata.category(chr(cp)).startswith('M')];v=chr(lo+0x4D)
 for c in letters:
  out.extend((c+m,lang,'vowel') for m in signs)
  out.extend((c+v+d,lang,'conjunct') for d in letters)
  out.extend((c+v+j+c,lang,'joiner') for j in ['\u200c','\u200d'])
 return out

def validate(weight):
 path=ROOT/'desktop'/f'AT-KPN-{weight}.ttf';tt,h=resource(path);mapper=json.loads((ROOT/'build'/f'merge-map-{weight}.json').read_text());errors=[];expected=set();count=0;source_count=0;missing=[];merge_reg=[];source_reg=[];gs=tt.getGlyphSet()
 @lru_cache(maxsize=None)
 def identity(n):
  p=DecomposingRecordingPen(gs);gs[n].draw(p);return hashlib.sha256(repr((p.value,gs[n].width)).encode()).hexdigest()
 for script in SCRIPTS:
  st,sh=resource(ROOT/'build/components'/f'AT-KPN{script}-{weight}.ttf');expected.update(st.getBestCmap());original,oh=resource(source_path(script,weight))
  for text,lang,kind in cases(script,st.getBestCmap()):
   before=shape(st,sh,text,lang);after=shape(tt,h,text,lang);count+=1
   if any(n[0]=='.notdef' for n in after):missing.append({'script':script,'text':text,'kind':kind})
   mapped=[(identity(mapper['aliases'].get(mapper['maps'][script][n[0]],mapper['maps'][script][n[0]])),)+n[1:] for n in before]
   actual=[(identity(n[0]),)+n[1:] for n in after]
   if mapped!=actual:merge_reg.append({'script':script,'text':text,'kind':kind,'before':before,'after':after})
   if script!='Latin':
    prior=shape(original,oh,text,lang);source_count+=1
    if [n[:2] for n in prior]!=[n[:2] for n in before]:source_reg.append({'script':script,'text':text,'kind':kind,'before':prior,'after':before})
 # Combining accents must not acquire spacing advances, including sequences
 # with no precomposed Unicode character.
 for base,marked in [('H','Ĥ'),('q','q̈'),('x','x̄'),('g','g̤'),('c','c̤̏')]:
  plain=shape(tt,h,base,'en');accented=shape(tt,h,marked,'en')
  if sum(p[2] for p in plain)!=sum(p[2] for p in accented):errors.append('Combining mark changes advance: '+marked)
 # Mixed-script strings must resolve entirely in this single font.
 mixed='Hello ₹ 1,250.00 — '+ ' / '.join(r['title'] for r in SAMPLES)
 # HarfBuzz consumes a single script run, so validate mixed strings via CoreText,
 # and check coverage here. CoreText test performs its own itemization.
 if any(ord(c) not in tt.getBestCmap() for c in mixed):errors.append('Mixed-language Unicode coverage incomplete')
 if missing:errors.append(f'{len(missing)} missing-glyph cases')
 if merge_reg:errors.append(f'{len(merge_reg)} component/merged shaping differences')
 if source_reg:errors.append(f'{len(source_reg)} upstream/edited native glyph-sequence differences')
 cmap=tt.getBestCmap()
 if expected!=set(cmap):errors.append('Coverage differs from component union')
 for cp in range(33,127):
  if cp not in cmap or tt['glyf'][cmap[cp]].numberOfContours==0:errors.append(f'Missing or blank U+{cp:04X}')
 for nid,val in [(16,'AT-KPN'),(17,weight),(6,'AT-KPN-'+weight)]:
  if tt['name'].getDebugName(nid)!=val:errors.append(f'Incorrect name ID {nid}')
 if tt['OS/2'].usWeightClass!=CFG['weights'][weight] or tt['OS/2'].fsType!=0:errors.append('Weight or embedding metadata incorrect')
 if 'SIL Open Font License' not in tt['name'].getDebugName(13):errors.append('Missing OFL metadata')
 bounds=[0,0]
 for n in tt.getGlyphOrder():
  g=tt['glyf'][n]
  if not g.numberOfContours:continue
  g.recalcBounds(tt['glyf']);bounds=[min(bounds[0],g.yMin),max(bounds[1],g.yMax)];points,_,_=g.getCoordinates(tt['glyf'])
  if any(not math.isfinite(v) for p in points for v in p):errors.append('Nonfinite outline '+n)
 if bounds[1]>tt['OS/2'].usWinAscent or -bounds[0]>tt['OS/2'].usWinDescent:errors.append('Clipping metrics exceed bounds')
 web=ROOT/'web'/f'AT-KPN-{weight}.woff2';wf=TTFont(web)
 if wf.getBestCmap()!=cmap:errors.append('WOFF2 coverage mismatch')
 for tag in ['GSUB','GPOS','GDEF','hmtx']:
  if tt[tag].compile(tt)!=wf[tag].compile(wf):errors.append('WOFF2 table mismatch '+tag)
 sanitizer=[];(ROOT/'build/sanitized').mkdir(exist_ok=True)
 for p in [path,web]:
  result=subprocess.run([ots.OTS_SANITIZE,str(p),str(ROOT/'build/sanitized'/p.name)],capture_output=True,text=True);sanitizer.append({'file':p.name,'exit_code':result.returncode,'log':result.stderr.strip()})
  if result.returncode:errors.append('Sanitizer rejected '+p.name)
 report={'font':path.name,'pass':not errors,'errors':errors,'glyphs':len(tt.getGlyphOrder()),'unicode_characters':len(cmap),'merged_shaping_cases':count,'upstream_native_sequence_cases':source_count,'missing_glyph_cases':len(missing),'merge_regressions':len(merge_reg),'upstream_sequence_regressions':len(source_reg),'merge_examples':merge_reg[:30],'upstream_examples':source_reg[:30],'missing_examples':missing[:30],'sanitizer':sanitizer,'outline_y_bounds':bounds,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 print(weight,'PASS' if report['pass'] else 'FAIL',count,'cases',errors,flush=True);return report
if __name__=='__main__':
 reports=[validate(p.stem.removeprefix('AT-KPN-')) for p in sorted((ROOT/'desktop').glob('*.ttf'))]
 report={'pass':all(r['pass'] for r in reports),'fonts':reports,'scope':'Automated source-to-edited glyph sequences, exact component-to-merged outlines and positions, native sample coverage, metadata, bounds, WOFF2 equivalence and OTS. Native-reader review pending.'}
 (ROOT/'qa/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if not report['pass']:sys.exit(1)
