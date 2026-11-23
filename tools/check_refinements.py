"""Checks for the specific visual regressions found in the Study 02 audit."""
from pathlib import Path
import json,sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from outline_design import ContourPen,draw_segment
from build_family import ROOT,CFG
from compare_reference import render,sameheight,mask

def shape(path,text,features=None):
 t=TTFont(path);font=hb.Font(hb.Face(path.read_bytes()));hb.ot_font_set_funcs(font);b=hb.Buffer();b.add_str(text);b.guess_segment_properties();hb.shape(font,b,features or {})
 return [(t.getGlyphName(i.codepoint),i.cluster,p.x_advance,p.x_offset,p.y_offset) for i,p in zip(b.glyph_infos,b.glyph_positions)]
results=[]
for w in CFG['weights']:
 errors=[];p=ROOT/'desktop'/f'AT-KPN-{w}.ttf';tt=TTFont(p);component=ROOT/'build/components'/f'AT-KPNMalayalam-{w}.ttf'
 for text in ['നമസ്കാരം','സ്ക സ്കാ സ്കി സ്കീ സ്കു സ്കൂ സ്കെ സ്കേ സ്കൊ സ്കോ സ്കൗ','സ്ക\u200d സ്ക\u200c']:
  for features in [{},{'ss01':1}]:
   a=shape(p,text,features);b=shape(component,text,features)
   # Component-to-family identities are independently covered by validation;
   # this checks optional substitution selection and positional equality.
   if [r[1:] for r in a]!=[r[1:] for r in b]:errors.append('Alternate positioning differs after merge')
   if any(r[0]=='.notdef' for r in a):errors.append('Missing glyph in Malayalam alternate case')
 normal=shape(p,'നമസ്കാരം');traditional=shape(p,'നമസ്കാരം',{'ss01':1})
 if not any('SaKa.mlm'==r[0] for r in normal):errors.append('Default inline conjunct missing')
 if not any('SaKa.traditional.mlm'==r[0] for r in traditional):errors.append('Traditional ss01 alternate missing')
 if sum(r[2] for r in normal)<=sum(r[2] for r in traditional):errors.append('Inline form does not have its own spacing')
 tamil=TTFont(ROOT/'build/components'/f'AT-KPNTamil-{w}.ttf');gs=tamil.getGlyphSet();pen=ContourPen(gs);gs['KaPulli.tm'].draw(pen);dots=[]
 for segs,closed in pen.contours:
  b=BoundsPen(None);b.moveTo(segs[0][0])
  for s in segs:draw_segment(b,s)
  b.closePath();box=b.bounds
  if box and box[1]>575:
   ratio=(box[2]-box[0])/(box[3]-box[1]);dots.append(ratio)
   if not .98<ratio<1.02:errors.append('Tamil dot is not circular')
 if not dots:errors.append('Tamil dot not found')
 im=sameheight(render(p,'নমস্কার','bn'),91);m=mask(im);pix=m.load();top=[]
 for x in range(20,im.width-20):
  y=next((y for y in range(15) if pix[x,y]),None)
  if y is not None:top.append(y)
 dip=max(top)-min(top)
 if dip>1:errors.append('Bengali headline still has an internal dip')
 result={'weight':w,'pass':not errors,'errors':errors,'tamil_dot_aspect_ratios':dots,'bengali_headline_variation_px_at_91px_ink_height':dip,'malayalam_default_glyphs':[r[0] for r in normal],'malayalam_ss01_glyphs':[r[0] for r in traditional]};results.append(result);print(w,result['pass'],errors)
report={'pass':all(r['pass'] for r in results),'weights':results,'scope':'Round dots, continuous Bengali sample headline, default and optional Malayalam forms, and alternate positioning after merge.'}
(ROOT/'qa/refinement-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if not report['pass']:sys.exit(1)
