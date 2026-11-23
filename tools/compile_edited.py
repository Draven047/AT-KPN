"""Build edited UFO outlines with their retained OpenType layout TTX sidecars.

Use this after editing the sources. build_family.py recreates the starting design
from upstream and would overwrite hand edits. Glyph order/names must stay stable;
new glyphs or layout changes require coordinated edits to the TTX sidecar.
"""
from fontTools.ttLib import TTFont,newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from ufoLib2 import Font
from build_family import ROOT,SCRIPTS,CFG,merge,names
import argparse

def compile_component(script,weight):
 (ROOT/'build/components').mkdir(parents=True,exist_ok=True)
 base=f'AT-KPN{script}-{weight}';tt=TTFont();tt.importXML(ROOT/'sources/layout'/f'{base}.ttx');u=Font.open(ROOT/'sources/editable'/f'{base}.ufo')
 order=tt.getGlyphOrder();assert set(order)==set(u.keys()),f'{base}: glyph names changed; update the layout TTX in tandem'
 tt['glyf']=newTable('glyf');tt['glyf'].glyphs={};tt['glyf'].glyphOrder=order;tt['hmtx']=newTable('hmtx');tt['hmtx'].metrics={};tt['loca']=newTable('loca')
 for n in order:
  p=TTGlyphPen(u);u[n].draw(Cu2QuPen(p,max_err=.55));g=p.glyph();tt['glyf'][n]=g;g.recalcBounds(tt['glyf']);tt['hmtx'][n]=(round(u[n].width),getattr(g,'xMin',0))
 names(tt,weight,script);tt.save(ROOT/'build/components'/f'{base}.ttf')
 print('Compiled '+base,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--weights',nargs='+',default=list(CFG['weights']));a=p.parse_args()
 for w in a.weights:
  for s in SCRIPTS:compile_component(s,w)
  merge(w)
