"""Independent Latin drawings, refined against the approved Study 02 edges."""
from fontTools.pens.reverseContourPen import ReverseContourPen

def english(p,char,weight):
 stem={'Light':96,'Regular':140,'Bold':185}[weight];delta=185-stem
 if char=='H':
  left=60;right=665;L=left+stem;R=right-stem;rad=stem*.56;bar=stem*.81;lo=365-bar/2;hi=365+bar/2;top=710
  p.moveTo((left,top));p.lineTo((L-rad,top));p.curveTo((L,top),(L,top-55),(L,top-120));p.lineTo((L,hi));p.lineTo((R,hi));p.lineTo((R,top));p.lineTo((right-rad,top));p.curveTo((right,top),(right,top-55),(right,top-120));p.lineTo((right,0));p.lineTo((R+rad,0));p.curveTo((R,0),(R,50),(R,120));p.lineTo((R,lo));p.lineTo((L,lo));p.lineTo((L,0));p.lineTo((left+rad,0));p.curveTo((left,0),(left,50),(left,120));p.closePath()
 elif char in ('l','i','I'):
  left=57;right=left+stem;top=740 if char=='l' else 550 if char=='i' else 710;reach=80 if char=='i' else 125;foot=right+reach;rad=stem*.56
  p.moveTo((left,top));p.lineTo((right-rad,top));p.curveTo((right,top),(right,top-55),(right,top-120))
  if char!='I':
   # The terminal swells into a rounded bulb and returns into the lower curve.
   p.lineTo((right,193));p.curveTo((right,143),(right+26,132),(foot-27,132));p.curveTo((foot-15,132),(foot-7,136),(foot-4,140));p.curveTo((foot+5,110),(foot+8,63),(foot-6,31));p.curveTo((foot-18,1),(foot-39,-13),(foot-79,-13));p.curveTo((left+70,-13),(left,59),(left,180))
  else:
   p.lineTo((right,0));p.lineTo((left+rad,0));p.curveTo((left,0),(left,50),(left,120))
  p.closePath()
  if char=='i':
   cx=(left+right)/2;cy=690;r=stem*.48;k=r*.55228475;p.moveTo((cx+r,cy));p.curveTo((cx+r,cy+k),(cx+k,cy+r),(cx,cy+r));p.curveTo((cx-k,cy+r),(cx-r,cy+k),(cx-r,cy));p.curveTo((cx-r,cy-k),(cx-k,cy-r),(cx,cy-r));p.curveTo((cx+k,cy-r),(cx+r,cy-k),(cx+r,cy));p.closePath()
 elif char=='o':
  p.moveTo((624,275));p.curveTo((624,458),(516,565),(332,565));p.curveTo((148,565),(40,458),(40,275));p.curveTo((40,92),(148,-15),(332,-15));p.curveTo((516,-15),(624,92),(624,275));p.closePath()
  rx=292-stem;ry=290-stem*.816;k=.55228475
  q=ReverseContourPen(p);q.moveTo((332+rx,275));q.curveTo((332+rx,275+ry*k),(332+rx*k,275+ry),(332,275+ry));q.curveTo((332-rx*k,275+ry),(332-rx,275+ry*k),(332-rx,275));q.curveTo((332-rx,275-ry*k),(332-rx*k,275-ry),(332,275-ry));q.curveTo((332+rx*k,275-ry),(332+rx,275-ry*k),(332+rx,275));q.closePath()
 elif char=='e':
  # Lift the exit, deepen the round tip and retain an asymmetric teardrop counter.
  lower=109-delta*.30;join=216+delta*.16
  p.moveTo((550,151-delta*.15));p.curveTo((520,139-delta*.20),(457,lower),(370,lower));p.curveTo((288,lower),(241-delta*.65,139),(218-delta*.65,join));p.lineTo((352,join));p.curveTo((512,join),(579,263),(579,350));p.curveTo((579,494),(469,567),(326,567));p.curveTo((142,567),(40,445),(40,270));p.curveTo((40,90),(148,-16),(330,-16));p.curveTo((435,-16),(505,4),(544,38));p.curveTo((557,52),(560,92),(550,151-delta*.15));p.closePath()
  q=ReverseContourPen(p);q.moveTo((225-delta*.65,342-delta*.35));q.lineTo((345,342-delta*.35));q.curveTo((388+delta*.55,342-delta*.35),(411+delta*.65,354),(411+delta*.65,382));q.curveTo((411+delta*.65,416+delta*.6),(377,436+delta*.60),(338,436+delta*.60));q.curveTo((279,436+delta*.60),(242-delta*.65,394+delta*.60),(225-delta*.65,342-delta*.35));q.closePath()
 else:return False
 return True
