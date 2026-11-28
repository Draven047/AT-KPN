"""Independent Latin drawings for H, I, K, M, N, W, e, i, l, o and w.

Each letter is constructed here from a handful of measurements: the stem width of the weight and a
target box (left, bottom, right, top). The boxes come from the scalar reference profile in
design/reference-profile.json, so the letters take the reference proportions in every weight, while
the outlines themselves are AT-KPN's own constructions. Without a box the Bold design values are used.
"""
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

STEM={'Light':96,'Regular':140,'Bold':185}

def english(p,char,weight,box=None,xheight=550):
 stem=STEM[weight];delta=185-stem
 if char=='H':
  left,_,right,top=box or (60,0,665,710)
  L=left+stem;R=right-stem;rad=stem*.56;bar=stem*.81;mid=top*365/710;lo=mid-bar/2;hi=mid+bar/2
  p.moveTo((left,top));p.lineTo((L-rad,top));p.curveTo((L,top),(L,top-55),(L,top-120));p.lineTo((L,hi));p.lineTo((R,hi));p.lineTo((R,top));p.lineTo((right-rad,top));p.curveTo((right,top),(right,top-55),(right,top-120));p.lineTo((right,0));p.lineTo((R+rad,0));p.curveTo((R,0),(R,50),(R,120));p.lineTo((R,lo));p.lineTo((L,lo));p.lineTo((L,0));p.lineTo((left+rad,0));p.curveTo((left,0),(left,50),(left,120));p.closePath()
 elif char in ('l','i','I'):
  left,bot,xmax,top=box or {'l':(57,-13,370.6,740),'i':(57,-13,325.6,738.8),'I':(57,0,242,710)}[char]
  right=left+stem;foot=xmax-3.6;rad=stem*.56;boxtop=top
  if char=='i':top=xheight
  p.moveTo((left,top));p.lineTo((right-rad,top));p.curveTo((right,top),(right,top-55),(right,top-120))
  if char!='I':
   # The terminal swells into a rounded bulb and returns into the lower curve.
   # The foot is drawn for the Bold stem; lighter weights scale its height (k) and inner fillet (s)
   # so the foot stays in proportion to the stem instead of keeping Bold's mass.
   k=stem/185;s=(1+k)/2;fy=lambda y:bot+(y+13)*k;ft=fy(132)
   p.lineTo((right,ft+61*s));p.curveTo((right,ft+11*s),(right+26*s,ft),(foot-27,ft));p.curveTo((foot-15,ft),(foot-7,fy(136)),(foot-4,fy(140)));p.curveTo((foot+5,fy(110)),(foot+8,fy(63)),(foot-6,fy(31)));p.curveTo((foot-18,fy(1)),(foot-39,bot),(foot-79,bot));p.curveTo((left+70,bot),(left,fy(59)),(left,fy(180)))
  else:
   p.lineTo((right,0));p.lineTo((left+rad,0));p.curveTo((left,0),(left,50),(left,120))
  p.closePath()
  if char=='i':
   r=stem*.48;cx=(left+right)/2;cy=boxtop-r;k=r*.55228475;p.moveTo((cx+r,cy));p.curveTo((cx+r,cy+k),(cx+k,cy+r),(cx,cy+r));p.curveTo((cx-k,cy+r),(cx-r,cy+k),(cx-r,cy));p.curveTo((cx-r,cy-k),(cx-k,cy-r),(cx,cy-r));p.curveTo((cx+k,cy-r),(cx+r,cy-k),(cx+r,cy));p.closePath()
 elif char=='o':
  x0,y0,x1,y1=box or (40,-15,624,565)
  cx=(x0+x1)/2;cy=(y0+y1)/2;RX=(x1-x0)/2;RY=(y1-y0)/2;K=.63
  p.moveTo((cx+RX,cy));p.curveTo((cx+RX,cy+RY*K),(cx+RX*K,cy+RY),(cx,cy+RY));p.curveTo((cx-RX*K,cy+RY),(cx-RX,cy+RY*K),(cx-RX,cy));p.curveTo((cx-RX,cy-RY*K),(cx-RX*K,cy-RY),(cx,cy-RY));p.curveTo((cx+RX*K,cy-RY),(cx+RX,cy-RY*K),(cx+RX,cy));p.closePath()
  rx=RX-stem;ry=RY-stem*.816;k=.55228475
  q=ReverseContourPen(p);q.moveTo((cx+rx,cy));q.curveTo((cx+rx,cy+ry*k),(cx+rx*k,cy+ry),(cx,cy+ry));q.curveTo((cx-rx*k,cy+ry),(cx-rx,cy+ry*k),(cx-rx,cy));q.curveTo((cx-rx,cy-ry*k),(cx-rx*k,cy-ry),(cx,cy-ry));q.curveTo((cx+rx*k,cy-ry),(cx+rx,cy-ry*k),(cx+rx,cy));q.closePath()
 elif char=='e':
  # Lift the exit, deepen the round tip and retain an asymmetric teardrop counter.
  # The letter is drawn in the Bold box (40..579, -16..567) and mapped to the target box. The inner
  # edges move with the stem so the left wall stays about one stem, the bottom about 0.75 stem and
  # the exit about 0.7 stem in every weight; wall and side allow for the horizontal mapping.
  x0,y0,x1,y1=box or (40,-16,579,567)
  sx=(x1-x0)/539;sy=(y1-y0)/583
  t=TransformPen(p,(sx,0,0,sy,x0-40*sx,y0+16*sy))
  lower=109-delta*.539;join=216+delta*.16;tip=151-delta*.46;wall=178-(178-delta)/sx;side=168-(168-delta*.865)/sx
  t.moveTo((550,tip));t.curveTo((520,tip-12),(457,lower),(370,lower));t.curveTo((288-delta*.55,lower),(241-wall-delta*.15,139+delta*.25),(218-wall,join));t.lineTo((352,join));t.curveTo((512,join),(579,263),(579,350));t.curveTo((579,494),(469,567),(326,567));t.curveTo((142,567),(40,445),(40,270));t.curveTo((40,90),(148,-16),(330,-16));t.curveTo((435,-16),(505,4),(544,38));t.curveTo((557,52),(560,92),(550,tip));t.closePath()
  q=ReverseContourPen(t);q.moveTo((225-wall,342-delta*.35));q.lineTo((345,342-delta*.35));q.curveTo((388+side*.85,342-delta*.35),(411+side,354),(411+side,382));q.curveTo((411+side,416+delta*.6),(377,436+delta*.60),(338,436+delta*.60));q.curveTo((279-delta*.3,436+delta*.60),(242-wall,394+delta*.55),(225-wall,342-delta*.35));q.closePath()
 elif char in ('M','W','w') and box:return zigzag(p,char,weight,box)
 elif char in ('K','N') and box:return straight(p,char,weight,box)
 else:return False
 return True


# ---------------------------------------------------------------- zig-zag letters (M, W, w)
# M, W and w are built as one thick zig-zag stroke: a centreline through the letter's turning points,
# a perpendicular width per stroke, mitred joins, and a horizontal clip at the baseline (or overshoot)
# and the top line. The clip makes the M's centre V stand on the baseline and the W's and w's middle
# apex reach the top line. Corners are then finished by kind: stroke feet and stroke tops get the
# family's stem end (one crisp corner, one soft corner), clipped joins get round corners, inner joins
# stay sharp.
import math as _m

def _u(a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];l=_m.hypot(dx,dy);return (dx/l,dy/l)

def _hit(p,d,q,e):
 den=d[0]*e[1]-d[1]*e[0];s=((q[0]-p[0])*e[1]-(q[1]-p[1])*e[0])/den;return (p[0]+d[0]*s,p[1]+d[1]*s)

def _clip(poly,y,keep_above):
 out=[];n=len(poly)
 for i in range(n):
  a=poly[i];b=poly[(i+1)%n];ia=(a[1]>=y)==keep_above;ib=(b[1]>=y)==keep_above
  if ia:out.append((a[0],a[1],a[2] if len(a)>2 else 'join'))
  if ia!=ib:
   t=(y-a[1])/(b[1]-a[1]);out.append((a[0]+(b[0]-a[0])*t,y,'clip'))
 return out

def _zigzag(pts,widths,bottom,top):
 """Outline of a thick polyline (centreline pts, one width per stroke) clipped to bottom <= y <= top."""
 n=len(pts);d=[_u(pts[i],pts[i+1]) for i in range(n-1)]
 left=lambda k,s:(pts[k][0]-d[s][1]*widths[s]/2,pts[k][1]+d[s][0]*widths[s]/2)
 right=lambda k,s:(pts[k][0]+d[s][1]*widths[s]/2,pts[k][1]-d[s][0]*widths[s]/2)
 L=[left(0,0)];R=[right(0,0)]
 for k in range(1,n-1):
  L.append(_hit(left(k-1,k-1),d[k-1],left(k,k),d[k]));R.append(_hit(right(k-1,k-1),d[k-1],right(k,k),d[k]))
 L.append(left(n-1,n-2));R.append(right(n-1,n-2))
 poly=L+R[::-1]
 return _clip(_clip(poly,bottom,True),top,False)

def _round(p,poly,spec):
 """Draw a closed polygon; spec(i, prev, v, next) gives None (sharp) or (ra, rb, ka, kb):
 the corner starts ra before the vertex and ends rb after it; ka, kb place the handles toward the vertex.
 spec may also give ('path', start, [(c1, c2, end), ...]) to draw the vertex as those curves, or ('skip',)."""
 n=len(poly);pieces=[]
 for i,v in enumerate(poly):
  P,N=poly[i-1],poly[(i+1)%n];r=spec(i,P,v,N)
  if not r:pieces.append(((v[0],v[1]),));continue
  if r[0]=='skip':pieces.append(None);continue
  if r[0]=='path':pieces.append(('path',r[1],r[2]));continue
  ra,rb,ka,kb=r;ua=_u(v,P);ub=_u(v,N)
  la=_m.hypot(P[0]-v[0],P[1]-v[1]);lb=_m.hypot(N[0]-v[0],N[1]-v[1]);ra=min(ra,la*.49);rb=min(rb,lb*.49)
  A=(v[0]+ua[0]*ra,v[1]+ua[1]*ra);B=(v[0]+ub[0]*rb,v[1]+ub[1]*rb)
  pieces.append((A,(A[0]+(v[0]-A[0])*ka,A[1]+(v[1]-A[1])*ka),(B[0]+(v[0]-B[0])*kb,B[1]+(v[1]-B[1])*kb),B))
 end=lambda c:c[2][-1][2] if c[0]=='path' else c[-1]
 s0=next(k for k in range(n) if pieces[k] is not None);start=end(pieces[s0]);p.moveTo(start);last=start
 for k in range(s0+1,s0+n+1):
  c=pieces[k%n]
  if c is None:continue
  first=c[1] if c[0]=='path' else c[0]
  if abs(first[0]-last[0])>.01 or abs(first[1]-last[1])>.01:p.lineTo(first)
  if c[0]=='path':
   for c1,c2,e in c[2]:p.curveTo(c1,c2,e)
  elif len(c)==4:p.curveTo(c[1],c[2],c[3])
  last=end(c)
 p.closePath()

def _fit_x(build,spec,x0,x1,steps=10):
 """Shift the outer centreline ends until the finished outline (corners included) spans x0..x1."""
 from fontTools.pens.boundsPen import BoundsPen
 a,b=0.0,0.0
 for _ in range(steps):
  poly=build(a,b);bp=BoundsPen(None);_round(bp,poly,spec);bb=bp.bounds;a+=x0-bb[0];b+=x1-bb[2]
 return build(a,b)

def zigzag(p,char,weight,box):
 stem=STEM[weight];k=(stem-96)/89            # 0 for Light, 1 for Bold
 x0,y0,x1,top=box
 def spec(i,P,v,N):
  if v[2]!='clip':return None
  ends=[q for q in (P,N) if q[2]=='clip' and abs(q[1]-v[1])<.5]
  if not ends:return None
  e=ends[0];w=abs(e[0]-v[0]);first=v[0]<e[0]
  end_of_stroke=(char=='M' and v[1]==bottom and (v[0]<x0+stem*1.6 or v[0]>x1-stem*1.6)) or (char!='M' and v[1]==top and (v[0]<x0+stem*1.6 or v[0]>x1-stem*1.6))
  if end_of_stroke:
   # stem end: on a foot the left corner is soft and the right crisp; on a top the left is crisp, the right soft
   if (first if v[1]==bottom else not first)==False:return None
   return (w*.56,w*.65,1.0,.542) if e is P else (w*.65,w*.56,.542,1.0)
  r=min(stem*.42,w*.45)
  return (r,r*1.25,.552,.552) if e is P else (r*1.25,r,.552,.552)
 if char=='M':
  leg=stem*(1.04+.08*k);diag=stem*(.9-.2*k);sp=top*.05;cx=(x0+x1)/2;bottom=0
  def build(a,b):
   # legs lean outward by sp over the cap height; the ends run past the clip lines and are cut level
   xl=x0+leg/2+a;xr=x1-leg/2+b;at=lambda x,y,s:(x+s*y/top,y)
   pts=[at(xl,-100,sp),at(xl,top+160,sp),(cx,-160),at(xr,top+160,-sp),at(xr,-100,-sp)]
   return _zigzag(pts,[leg,diag,diag,leg],bottom,top)
 else:
  outer=stem*1.04;inner=stem*(.97-.09*k);bottom=y0;cx=(x0+x1)/2
  def build(a,b):
   q=(x1-x0)/4;lo=bottom-150;hi=top+150
   pts=[(x0+outer*.5+a-q*.04,hi),(x0+q*1.02,lo),(cx,hi),(x1-q*1.02,lo),(x1-outer*.5+b+q*.04,hi)]
   return _zigzag(pts,[outer,inner,inner,outer],bottom,top)
 poly=_fit_x(build,spec,x0,x1)
 _round(p,poly,spec)
 return True


# ---------------------------------------------------------------- straight-stroke letters (K, N)
# K and N are built from the same parts as the zig-zag letters: straight stems, slanted strokes of a
# set perpendicular width, and level cuts at the baseline and top line. The proportions are scalar
# measurements (stroke width as a share of the stem, slope, the height where strokes meet); the corners
# follow the stem-end rule. K's arm and leg meet the stem at one point at half height, its arm is cut
# level at the top line and both stroke ends round their acute corner. N's diagonal leaves the top of
# the left stem and lands at the foot of the right stem.

def _area(poly):
 return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2

def _union(polys):
 import pathops
 path=pathops.Path()
 for poly in polys:
  pen=path.getPen();pen.moveTo(poly[0][:2])
  for q in poly[1:]:pen.lineTo(q[:2])
  pen.closePath()
 path.simplify(fix_winding=True)
 from fontTools.pens.recordingPen import RecordingPen
 rec=RecordingPen();path.draw(rec);out=[];cur=[]
 for op,a in rec.value:
  if op=='moveTo':cur=[a[0]]
  elif op=='lineTo':cur.append(a[0])
  elif op in('closePath','endPath'):
   if len(cur)>2 and abs(cur[0][0]-cur[-1][0])<.01 and abs(cur[0][1]-cur[-1][1])<.01:cur.pop()
   out.append(cur);cur=[]
 return out

def _level(poly,levels):
 """Clockwise polygon with each vertex tagged 'clip' when it lies on one of the level lines."""
 if _area(poly)>0:poly=poly[::-1]
 return [(q[0],q[1],'clip' if any(abs(q[1]-l)<.5 for l in levels) else 'join') for q in poly]

def straight(p,char,weight,box):
 stem=STEM[weight];k=(stem-96)/89            # 0 for Light, 1 for Bold
 x0,y0,x1,top=box;bottom=0

 def band(a,slope,width,lo,hi):
  """A straight stroke whose lower-left edge passes through a with slope dx/dy, cut level at lo and hi."""
  d=_u((0,0),(slope,1));nrm=(d[1],-d[0])
  c=(a[0]+nrm[0]*width/2,a[1]+nrm[1]*width/2)
  return _zigzag([(c[0]+slope*(lo-200-c[1]),lo-200),(c[0]+slope*(hi+200-c[1]),hi+200)],[width],lo,hi)

 if char=='N':
  # The diagonal's lower edge leaves the left stem high up (lower in the heavier weights, where the
  # diagonal is wider) and lands on the right stem just under the baseline.
  diag=stem*.9;xl=x0+stem/2;xr=x1-stem/2
  a=(x0+stem,top*(.88-.28*k));b=(x1-stem,-top*(.10-.06*k));d=_u(b,a);nrm=(-d[1],d[0])
  if nrm[1]<0:nrm=(-nrm[0],-nrm[1])
  c0=(a[0]+nrm[0]*diag/2,a[1]+nrm[1]*diag/2);c1=(b[0]+nrm[0]*diag/2,b[1]+nrm[1]*diag/2)
  yat=lambda x:c0[1]+(c1[1]-c0[1])*(x-c0[0])/(c1[0]-c0[0])
  polys=[_zigzag([(xl,-200),(xl,yat(xl)),(xr,yat(xr)),(xr,top+200)],[stem,diag,stem],bottom,top)]
  levels=(bottom,top)
 else:
  # The arm and the leg each meet the stem along their own edge: the arm a little above half height,
  # the leg at about half height, so the two strokes cross just right of the stem.
  arm=stem*.9;leg=stem*.92;ls=-(.69+.07*k);sa=.75+.06*k;ya=top*(.67-.09*k);yl=top*(.52-.035*k);ov=stem*.06
  rect=[(x0,bottom),(x0,top),(x0+stem,top),(x0+stem,bottom)]
  # the inner ends of both strokes are trimmed along the middle of the stem
  def trim(poly):
   out=[];n=len(poly);xc=x0+stem*.5
   for i in range(n):
    a,b=poly[i],poly[(i+1)%n]
    if a[0]>=xc:out.append(a)
    if (a[0]>=xc)!=(b[0]>=xc):t=(xc-a[0])/(b[0]-a[0]);out.append((xc,a[1]+(b[1]-a[1])*t,'join'))
   return out
  def side(poly,a,s):
   # keep the part of poly to the right of the line through a with slope dx/dy = s
   f=lambda q:s*(q[1]-a[1])-(q[0]-a[0]);out=[];n=len(poly)
   for i in range(n):
    u,v=poly[i],poly[(i+1)%n]
    if f(u)<=0:out.append(u)
    if (f(u)<=0)!=(f(v)<=0):t=f(u)/(f(u)-f(v));out.append((u[0]+(v[0]-u[0])*t,u[1]+(v[1]-u[1])*t,'join'))
   return out
  # each stroke stops at the other's inner edge, so arm and leg meet in a point inside the stem and
  # leave a small notch above and below it
  al=(x0+stem-ov,ya);ll=(x0+stem-ov,yl)
  legp=lambda s:trim(side(band(ll,ls,leg,y0,top),al,s));armp=lambda s:trim(side(band(al,s,arm,bottom,top),ll,ls))
  # the arm's slope is set so its top corner (before rounding) reaches the box edge; Light shares the
  # Regular box, so its arm aims short by the stem difference and keeps the Regular slope
  edge=x1-max(0,STEM['Regular']-stem)
  for _ in range(40):
   tip=max(q[0] for q in armp(sa));sa+=(edge-tip)/(top-ya)
  polys=_union([rect,legp(sa),armp(sa)]);levels=(bottom,y0,top)

 feet={}
 if char=='K':
  # K's leg ends in a kick, as in the reference: its outer edge bends out to a sharp point a little above
  # the baseline, a quarter stem out from the leg, one round curve sweeps from there down to the baseline, and the inner
  # edge curves into that bottom. Heights and offsets are scaled from the reference K in each weight.
  for poly in polys:
   q=_level(poly,levels);n=len(q)
   for i,v in enumerate(q):
    N=q[(i+1)%n]
    if abs(v[1]-y0)<.5 and abs(N[1]-y0)<.5 and min(v[0],N[0])>x0+stem*1.2 and v[0]>N[0]:
     P=q[i-1];NN=q[(i+2)%n]
     dR=_u(P,v);dL=_u(N,NN)                                   # down the outer edge; up the inner edge
     yT=top*(.057+.083*k);xR=v[0]+dR[0]*(yT-v[1])/dR[1]
     T=(min(x1,xR+stem*.25),yT)                                 # the point stands a quarter stem out of the leg
     ang=_m.radians(23-11*k);eT=(_m.cos(ang),-_m.sin(ang))
     yP=yT+stem*.45;Pf=(v[0]+dR[0]*(yP-v[1])/dR[1],yP)
     B=(T[0]-stem*.65,y0)
     yQ=y0+stem*.45;Q=(N[0]+dL[0]*(yQ-N[1])/dL[1],yQ)
     def joint(A,da,C,dc,t=.6):
      den=da[0]*dc[1]-da[1]*dc[0]
      s=((C[0]-A[0])*dc[1]-(C[1]-A[1])*dc[0])/den;X=(A[0]+da[0]*s,A[1]+da[1]*s)
      la=_m.hypot(X[0]-A[0],X[1]-A[1])*t;lc=_m.hypot(C[0]-X[0],C[1]-X[1])*t
      return ((A[0]+da[0]*la,A[1]+da[1]*la),(C[0]-dc[0]*lc,C[1]-dc[1]*lc),C)
     h=.62
     path=[joint(Pf,dR,T,eT),
           ((T[0],T[1]-(T[1]-y0)*h),(B[0]+(T[0]-B[0])*h,y0),B),
           joint(B,(-1,0),Q,dL)]
     feet[(round(v[0],3),round(v[1],3))]=('path',Pf,path);feet[(round(N[0],3),round(N[1],3))]=('skip',)
 def spec(i,P,v,N):
  if (round(v[0],3),round(v[1],3)) in feet:return feet[(round(v[0],3),round(v[1],3))]
  if v[2]!='clip':return None
  ends=[q for q in (P,N) if q[2]=='clip' and abs(q[1]-v[1])<.5]
  if not ends:return None
  e=ends[0];right=v[0]>e[0]
  # soft: the right end of a top cut and the left end of a foot
  if right!=(v[1]>top/2):return None
  w=stem       # every soft corner is the stem's, also on the wider slanted cuts
  return (w*.56,w*.65,1.0,.542) if e is P else (w*.65,w*.56,.542,1.0)
 for poly in polys:_round(p,_level(poly,levels),spec)
 return True


# ---------------------------------------------------------------- stem weight of f and r
# The scaled f and r came out lighter than the other lowercase stems (about 0.88 of the stem). Their
# stem is widened to the weight's stem by a smooth horizontal warp: the left edge stays, the right edge
# moves out, and everything right of the stem is drawn back in so the letter keeps its box. Only the
# letter's own contours are moved, not accents above or below it.

def _smooth(t):
 t=min(1.0,max(0.0,t));return t*t*(3-2*t)

def widen_stem(contours,stem,top):
 def own(segs):
  ys=[pt[1] for s in segs for pt in s];return min(ys)>-30 and max(ys)<top+30
 def bez(s,t):
  if len(s)==2:return (s[0][0]+(s[1][0]-s[0][0])*t,s[0][1]+(s[1][1]-s[0][1])*t)
  u=1-t;a,b,c,d=s;return (u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0],u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1])
 y=top*.3;xs=[]
 for segs,closed in contours:
  if not own(segs):continue
  for s in segs:
   pts=[bez(s,i/24) for i in range(25)]
   for a,b in zip(pts,pts[1:]):
    if (a[1]-y)*(b[1]-y)<0:xs.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
 xs.sort()
 if len(xs)<2:return contours
 sl,sr=xs[0],xs[1];d=stem-(sr-sl)
 if d<2:return contours
 xmax=max(pt[0] for segs,_ in contours if own(segs) for s in segs for pt in s)
 warp=lambda x:x+d*_smooth((x-sl)/(sr-sl))-d*_smooth((x-sr)/(xmax-sr))
 return [([tuple((warp(pt[0]),pt[1]) for pt in s) for s in segs] if own(segs) else segs,closed) for segs,closed in contours]
