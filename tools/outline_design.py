"""Editable draft outline treatment: asymmetric, tangent-continuous soft terminals.

This is a procedural first design pass, not a claim of hand-drawn Cocon identity.
This module changes outlines only. The build separately coordinates native widths, anchors and positioning.
"""
import math
from fontTools.pens.basePen import BasePen
from fontTools.misc.bezierTools import splitCubicAtT

def add(a,b): return (a[0]+b[0],a[1]+b[1])
def sub(a,b): return (a[0]-b[0],a[1]-b[1])
def mul(a,k): return (a[0]*k,a[1]*k)
def length(a): return math.hypot(*a)
def unit(a):
    n=length(a)
    return mul(a,1/n) if n>1e-8 else (0,0)
def dot(a,b): return a[0]*b[0]+a[1]*b[1]

class ContourPen(BasePen):
    def __init__(self,glyphSet):
        super().__init__(glyphSet)
        self.contours=[];self.current=[];self.start=None;self.last=None
    def _moveTo(self,p):
        self.current=[];self.start=self.last=p
    def _lineTo(self,p):
        if length(sub(p,self.last))>1e-7:self.current.append((self.last,p))
        self.last=p
    def _curveToOne(self,a,b,c):
        self.current.append((self.last,a,b,c));self.last=c
    def _closePath(self):
        if self.start!=self.last:self._lineTo(self.start)
        if self.current:self.contours.append((self.current,True))
        self.current=[]
    def _endPath(self):
        if self.current:self.contours.append((self.current,False))
        self.current=[]

def point(s,t):
    if len(s)==2:return add(s[0],mul(sub(s[1],s[0]),t))
    u=1-t
    return tuple(u*u*u*s[0][i]+3*u*u*t*s[1][i]+3*u*t*t*s[2][i]+t*t*t*s[3][i] for i in [0,1])

def approx_length(s,t0=0,t1=1):
    if len(s)==2:return length(sub(s[-1],s[0]))*(t1-t0)
    pts=[point(s,t0+(t1-t0)*i/10) for i in range(11)]
    return sum(length(sub(b,a)) for a,b in zip(pts,pts[1:]))

def parameter(s,d,at_end=False):
    if not d:return 1.0 if at_end else 0.0
    total=approx_length(s)
    if len(s)==2:return 1-d/total if at_end else d/total
    lo,hi=0.0,1.0
    for _ in range(13):
        mid=(lo+hi)/2
        value=approx_length(s,mid,1) if at_end else approx_length(s,0,mid)
        if (value>d) != at_end:hi=mid
        else:lo=mid
    return (lo+hi)/2

def trim(s,t0,t1):
    if len(s)==2:return (point(s,t0),point(s,t1))
    cuts=[t for t in [t0,t1] if 1e-8<t<1-1e-8]
    if not cuts:return s
    pieces=splitCubicAtT(*s,*cuts)
    return pieces[1 if t0>1e-8 else 0]

def tangent(s,end=False):
    anchor=s[-1] if end else s[0]
    candidates=list(reversed(s[:-1])) if end else s[1:]
    for p in candidates:
        delta=sub(anchor,p) if end else sub(p,anchor)
        if length(delta)>1e-5:return unit(delta)
    return (0,0)

def draw_segment(pen,s):
    if len(s)==2:pen.lineTo(s[1])
    else:pen.curveTo(*s[1:])

def design(contours,pen,radius,script,headline_y=None):
    rounded=0
    areas=[sum(s[0][0]*s[-1][1]-s[-1][0]*s[0][1] for s in segments) for segments,closed in contours]
    outer_sign=1 if not areas or max(areas,key=abs)>=0 else -1
    for segments,closed in contours:
        n=len(segments)
        trims_start=[0.0]*n;trims_end=[0.0]*n
        terminal_corners={}
        # A free stroke end is a short cap between opposing parallel sides.
        # Its dominant curve follows the stroke direction: a vertical stem
        # and a horizontal arm must not receive the same corner treatment.
        if closed:
            for cap_index,cap_segment in enumerate(segments):
                if len(cap_segment)!=2:continue
                prev=segments[(cap_index-1)%n];nxt=segments[(cap_index+1)%n]
                caplen=approx_length(cap_segment);v=tangent(prev,True);w=tangent(nxt)
                cv=tangent(cap_segment)
                if not 24<caplen<280 or dot(v,w)>-.94 or abs(dot(v,cv))>.25:continue
                if min(approx_length(prev),approx_length(nxt))<caplen*.85:continue
                if (v[0]*cv[1]-v[1]*cv[0])*outer_sign<=0 or (cv[0]*w[1]-cv[1]*w[0])*outer_sign<=0:continue
                if headline_y is not None and any(abs(pt[1]-headline_y)<7 for pt in cap_segment):continue
                a,b=cap_segment
                if abs(a[0]-b[0])<abs(a[1]-b[1]):
                    preferred=min([a,b],key=lambda p:p[1]) if v[0]>0 else max([a,b],key=lambda p:p[1])
                else:preferred=max([a,b],key=lambda p:p[0]) if v[1]>0 else min([a,b],key=lambda p:p[0])
                for corner,pt in [((cap_index-1)%n,a),(cap_index,b)]:
                    terminal_corners[corner]=(caplen*.90 if pt==preferred else caplen*.045)
        for i in range(n if closed else n-1):
            j=(i+1)%n;a,b=segments[i],segments[j];p=a[-1]
            v,w=tangent(a,True),tangent(b)
            angle=math.acos(max(-1,min(1,dot(v,w))))
            if angle<0.27 or angle>2.85:continue
            la,lb=approx_length(a),approx_length(b)
            if min(la,lb)<4:continue
            # Joining headline edges retain their original continuous span.
            if headline_y is not None and abs(p[1]-headline_y)<7:
                continue
            # Unequal corner radii create the asymmetric softened terminals of
            # the reference rather than a uniform geometric round-rect effect.
            convex=(v[0]*w[1]-v[1]*w[0])*outer_sign>0
            primary=(v[0]*w[1]+v[1]*w[0]) < -0.20
            bias=1.70 if convex and primary else 0.12
            cap=0.58 if convex and primary else 0.15
            distance=min(radius*bias*math.tan(angle/2),la*cap,lb*cap)
            if i in terminal_corners:
                distance=min(terminal_corners[i],la*.90,lb*.90)
            if distance<1.2:continue
            trims_end[i]=distance;trims_start[j]=distance;rounded+=1
        for i,s in enumerate(segments):
            total=trims_start[i]+trims_end[i]
            available=approx_length(s)*0.96
            if total>available:
                trims_start[i]*=available/total;trims_end[i]*=available/total
        pieces=[trim(s,parameter(s,trims_start[i]),parameter(s,trims_end[i],True)) for i,s in enumerate(segments)]
        pen.moveTo(pieces[0][0])
        for i,s in enumerate(pieces):
            draw_segment(pen,s)
            if not closed and i==n-1:break
            nxt=pieces[(i+1)%n]
            if trims_end[i]>0:
                a,b=s[-1],nxt[0];v,w=tangent(s,True),tangent(nxt)
                angle=math.acos(max(-1,min(1,dot(v,w))))
                chord=length(sub(b,a))
                handle=chord/(2*max(math.sin(angle/2),0.01))*4/3*math.tan(angle/4)
                handle=min(handle,chord*0.65)
                pen.curveTo(add(a,mul(v,handle)),sub(b,mul(w,handle)),b)
            elif length(sub(s[-1],nxt[0]))>0.01:pen.lineTo(nxt[0])
        if closed:pen.closePath()
        else:pen.endPath()
    return rounded
