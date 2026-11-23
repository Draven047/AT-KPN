"""Local optical corrections derived from the Study 02 outline audit.

Edits are applied to original OFL contours before coordinated width mapping.
Pattern matches carry the same revised hook across all glyphs sharing it.
"""
from copy import deepcopy
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from outline_design import ContourPen


def line(a,b):return (a,b)
def curve(a,b,c,d):return (a,b,c,d)
def move(contours,sx=1,sy=1,dx=0,dy=0):
 return [([tuple((x*sx+dx,y*sy+dy) for x,y in s) for s in segs],closed) for segs,closed in contours]
def bounds(contours):
 pts=[p for segs,_ in contours for s in segs for p in s]
 return (min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)) if pts else None

def pattern_replace(contours,pattern,replacement):
 out=[];count=0
 for segs,closed in contours:
  n=len(segs);found=None
  for start in range(n):
   run=[segs[(start+j)%n] for j in range(len(pattern))]
   if [len(s) for s in run]!=[len(s) for s in pattern]:continue
   dx=run[0][0][0]-pattern[0][0][0];dy=run[0][0][1]-pattern[0][0][1]
   if all(abs(p[0]-q[0]-dx)<.1 and abs(p[1]-q[1]-dy)<.1 for a,b in zip(run,pattern) for p,q in zip(a,b)):
    found=(start,dx,dy);break
  if found:
   start,dx,dy=found;rotated=segs[start:]+segs[:start]
   new=[tuple((x+dx,y+dy) for x,y in s) for s in replacement]
   out.append((new+rotated[len(pattern):],closed));count+=1
  else:out.append((segs,closed))
 return out,count

def headline_band(canonical):
 lines=[s for segs,_ in canonical for s in segs if len(s)==2 and abs(s[0][1]-s[1][1])<.01 and abs(s[0][0]-s[1][0])>200 and s[0][1]>400]
 ys=sorted(set(s[0][1] for s in lines),reverse=True)
 return ys[0],next(y for y in ys[1:] if 30<ys[0]-y<180)

def headlines(contours,top,bottom):
 """Square the left cut; round only the upper-right end. Maintain overlap."""
 out=[];count=0
 for segs,closed in contours:
  candidates=[(abs(s[-1][0]-s[0][0]),i) for i,s in enumerate(segs) if len(s)==2 and abs(s[0][1]-top)<.01 and abs(s[-1][1]-top)<.01 and s[-1][0]-s[0][0]>90]
  if not candidates:out.append((segs,closed));continue
  _,k=max(candidates);ss=segs[k:]+segs[:k];right=None;left=None
  for j in range(1,min(10,len(ss))):
   pts=[p for s in ss[1:j+1] for p in s]
   if min(p[1] for p in pts)<bottom-.1 or max(p[1] for p in pts)>top+.1:break
   if abs(ss[j][-1][1]-bottom)<.01 and max(p[0] for p in pts)-min(p[0] for p in pts)<180:right=j;break
  for j in range(len(ss)-1,max(0,len(ss)-10),-1):
   pts=[p for s in ss[j:] for p in s]
   if min(p[1] for p in pts)<bottom-.1 or max(p[1] for p in pts)>top+.1:break
   if abs(ss[j][0][1]-bottom)<.01 and max(p[0] for p in pts)-min(p[0] for p in pts)<180:left=j;break
  rnew=[];lnew=[]
  if right:
   pts=[p for s in ss[1:right+1] for p in s];a=ss[1][0];b=ss[right][-1];x=max(p[0] for p in pts);r=min((top-bottom)*.32,x-a[0]);r=max(5,r)
   rnew=[line(a,(x-r,top)),curve((x-r,top),(x-r*.45,top),(x,top-r*.45),(x,top-r)),line((x,top-r),(x,bottom)),line((x,bottom),b)];count+=1
  if left:
   pts=[p for s in ss[left:] for p in s];a=ss[left][0];b=ss[-1][-1];x=min(p[0] for p in pts)
   lnew=[line(a,(x,bottom)),line((x,bottom),(x,top)),line((x,top),b)];count+=1
  middle=ss[(right+1 if right else 1):(left if left else len(ss))]
  out.append(([ss[0]]+rnew+middle+lnew,closed))
 return out,count

def flatten_headline_dips(contours,top,bottom):
 out=[];hits=0
 for segs,closed in contours:
  ss=[];i=0
  while i<len(segs):
   end=None
   if len(segs[i])==4 and abs(segs[i][0][1]-top)<.1:
    for j in range(i,min(i+8,len(segs))):
     pts=[p for sg in segs[i:j+1] for p in sg]
     if min(p[1] for p in pts)<bottom or max(p[1] for p in pts)>top+.1:break
     b=segs[j][-1];a=segs[i][0]
     if j>i and abs(b[1]-top)<.1 and b[0]>a[0]+40 and top-min(p[1] for p in pts)>2:end=j;break
   if end is not None:ss.append(line(segs[i][0],segs[end][-1]));i=end+1;hits+=1
   else:ss.append(segs[i]);i+=1
  # Make adjacent horizontal pieces one bar for the end-profile treatment.
  merged=[]
  for sg in ss:
   if merged and len(sg)==2 and len(merged[-1])==2 and all(abs(p[1]-top)<.1 for p in (*sg,*merged[-1])):
    merged[-1]=line(merged[-1][0],sg[-1])
   else:merged.append(sg)
  out.append((merged,closed))
 return out,hits

def tamil_stem_caps(contours):
 out=[];hits=0
 for segs,closed in contours:
  ss=[];i=0
  while i<len(segs):
   a=segs[i][0];b=segs[i][-1];end=None
   if len(segs[i])==2 and abs(a[0]-b[0])<.1 and b[1]-a[1]>150 and b[1]>450:
    for j in range(i+1,min(i+8,len(segs))):
     if len(segs[j])==2:
      c,d=segs[j]
      if abs(c[0]-d[0])<.1 and c[1]-d[1]>150 and 40<c[0]-b[0]<240:
       pts=[p for sg in segs[i+1:j] for p in sg];top=max(p[1] for p in pts)
       if top<625 and min(p[1] for p in pts)>400:end=j
      break
   ss.append(segs[i])
   if end:
    c=segs[end][0];r=min((c[0]-b[0])*.55,top-c[1]);r=max(6,r)
    ss += [line(b,(b[0],top)),line((b[0],top),(c[0]-r,top)),curve((c[0]-r,top),(c[0],top),(c[0],top-r*.55),(c[0],top-r)),line((c[0],top-r),c)]
    i=end;hits+=1
   else:i+=1
  out.append((ss,closed))
 return out,hits

def hook_template(canonical,top):
 ss=max(canonical,key=lambda p:len(p[0]))[0];peak=max(range(len(ss)),key=lambda i:ss[i][0][1]);end=ss[peak][0]
 start=peak
 for _ in range(15):
  start=(start-1)%len(ss)
  if abs(ss[start][0][1]-top)<.1:break
 else:return None,None
 run=[];i=start
 while i!=peak:run.append(ss[i]);i=(i+1)%len(ss)
 a=run[0][0];notch=min((s[0] for s in run if s[0][1]>top+70),key=lambda p:p[0]);ix=notch[0];cap=end[1];join=top+(cap-top)*.30
 new=[curve(a,(ix,top),(ix,top+15),(ix,join)),line((ix,join),(ix,cap-35)),curve((ix,cap-35),(ix,cap-10),(ix+20,cap),end)]
 return run,new

def telugu_template(canonical):
 ss=max(canonical,key=lambda p:len(p[0]))[0];n=len(ss)
 # The source contour starts at the peak of the left arm. The inner valley is
 # the lowest point before the much higher right arm (top sign).
 peak=max(range(n),key=lambda i:ss[i][0][1]);valley=min(range(1,peak),key=lambda i:ss[i][0][1]);b=ss[valley][0]
 # Find the source outline's returning shoulder, followed by a short left line.
 candidates=[i for i,s in enumerate(ss) if len(s)==2 and s[-1][0]<s[0][0] and 450<s[0][1]<550 and abs(s[-1][1]-s[0][1])<.1]
 if not candidates:return None,None
 start=(candidates[-1]+1)%n;a=ss[start][0];run=[];i=start
 while i!=valley:
  run.append(ss[i]);i=(i+1)%n
  if len(run)>n:return None,None
 left=min(p[0] for s in run for p in s);cap=ss[0][0][1]-18;ledge=left+(b[0]-left)*.62
 new=[curve(a,(left+25,a[1]),(left,cap-75),(left,cap)),line((left,cap),(ledge,cap)),curve((ledge,cap),(ledge+12,cap-36),(b[0]-30,b[1]+28),b)]
 return run,new

def circular_dots(contours):
 result=[];count=0
 for segs,closed in contours:
  bb=bounds([(segs,closed)]);a,b,c,d=bb;w=c-a;h=d-b
  # A standalone closed dot, not a counter or an open-ended terminal.
  if closed and b>575 and 35<w<240 and 35<h<240 and .78<w/h<1.25 and sum(len(s)==2 for s in segs)<=1:
   cx=(a+c)/2;cy=(b+d)/2;r=(w+h)/4;k=.55228475*r
   ss=[curve((cx+r,cy),(cx+r,cy+k),(cx+k,cy+r),(cx,cy+r)),curve((cx,cy+r),(cx-k,cy+r),(cx-r,cy+k),(cx-r,cy)),curve((cx-r,cy),(cx-r,cy-k),(cx-k,cy-r),(cx,cy-r)),curve((cx,cy-r),(cx+k,cy-r),(cx+r,cy-k),(cx+r,cy))]
   # Preserve the source winding direction.
   area=sum(s[0][0]*s[-1][1]-s[-1][0]*s[0][1] for s in segs)
   if area<0:ss=[tuple(reversed(s)) for s in reversed(ss)]
   result.append((ss,closed));count+=1
  else:result.append((segs,closed))
 return result,count

def refine(tt,captures,script,weight,sx):
 cmap=tt.getBestCmap();stats={};extra={};protect=None
 if script in ['Devanagari','Bengali','Kannada']:
  n=cmap[ord({'Devanagari':'न','Bengali':'ন','Kannada':'ನ'}[script])];top,bottom=headline_band(captures[n]);protect=bottom-.5 if script!='Kannada' else top-.5
  if script=='Kannada':
   pattern,new=hook_template(captures[n],top);hits=0
   if pattern:
    for name in captures:captures[name],count=pattern_replace(captures[name],pattern,new);hits+=count
   stats['rounded_upper_hooks']=hits
  hits=0;dips=0
  if script in ['Devanagari','Bengali']:
   for name in captures:captures[name],count=flatten_headline_dips(captures[name],top,bottom);dips+=count
  stats['flattened_headline_dips']=dips
  for name in captures:captures[name],count=headlines(captures[name],top,bottom);hits+=count
  stats['headline_ends_rebuilt']=hits
 if script=='Devanagari':
  for name in captures:
   if name.startswith('matraE.'):
    captures[name]=[([tuple((x,top+(y-top)*.86 if y>top else y) for x,y in s) for s in segs],cl) for segs,cl in captures[name]]
   if name.startswith('SaTa.'):
    a=bounds(captures[name])[0];captures[name]=move(captures[name],sx=1.11,dx=-.11*a);advance,lsb=tt['hmtx'][name];tt['hmtx'][name]=(round(advance*1.11),lsb);extra[name]=(1.11,1,-.11*a,0)
  stats['refined_e_matra_and_sta']=True
 if script=='Kannada':
  hits=0
  for name in captures:
   bb=bounds(captures[name])
   if 'small' in name and bb and bb[3]<160 and bb[1]<-180:
    cx=(bb[0]+bb[2])/2;captures[name]=move(captures[name],sx=1.07,sy=.94,dx=-.07*cx,dy=47);hits+=1
  stats['balanced_below_forms']=hits
 if script=='Telugu':
  protect=450;n=cmap[ord('న')];pattern,new=telugu_template(captures[n]);hits=0
  if pattern:
   for name in captures:captures[name],count=pattern_replace(captures[name],pattern,new);hits+=count
  stats['upper_stroke_ledges']=hits
  if 'Kasmall1.te' in captures:
   bb=bounds(captures['Kasmall1.te']);cx=(bb[0]+bb[2])/2
   captures['Kasmall1.te']=move(captures['Kasmall1.te'],sx=1.18,sy=.866,dx=-.18*cx,dy=104);stats['balanced_ka_form']=True
 if script=='Bengali':
  for name in captures:
   if name.startswith('SaKa.'):
    captures[name]=[([tuple((x,y*.80 if y<0 else y) for x,y in s) for s in segs],cl) for segs,cl in captures[name]]
  stats['raised_central_conjunct']=True
 if script=='Tamil':
  hits=0
  for name in captures:captures[name],count=tamil_stem_caps(captures[name]);hits+=count
  stats['flat_stem_starts']=hits
 if script=='Malayalam':
  name=cmap[0xD4D];bb=bounds(captures[name]);cx=(bb[0]+bb[2])/2;bottom=bb[1];height=(bb[3]-bottom)*.84;width=(bb[2]-bb[0])*.91;x=cx-width/2;y=bottom+height;t={'Light':34,'Regular':53,'Bold':76}[weight]
  # A small rounded U, retaining the sign's original anchor and sidebearing.
  a=(x,y-t/2);b=(x+t,y-t/2);r=width/2
  ss=[curve(a,(x,y+t*.15),(x+t,y+t*.15),b),curve(b,(x+t,bottom+t*.50),(x+width-t,bottom+t*.50),(x+width-t,y-t/2)),curve((x+width-t,y-t/2),(x+width-t,y+t*.15),(x+width,y+t*.15),(x+width,y-t/2)),curve((x+width,y-t/2),(x+width,bottom-height*.44),(x,bottom-height*.44),a)]
  captures[name]=[(ss,True)]
  # Keep the original conjunct as an opt-in traditional alternate.
  old='SaKa.mlm';alt='SaKa.traditional.mlm';captures[alt]=deepcopy(captures[old]);tt['hmtx'][alt]=tt['hmtx'][old];order=tt.getGlyphOrder()+[alt];tt.setGlyphOrder(order)
  sa=cmap[0xD38];ka=cmap[0xD15];sa_advance=tt['hmtx'][sa][0];ka_advance=tt['hmtx'][ka][0]
  captures[old]=deepcopy(captures[sa])+move(captures[name],dx=sa_advance)+move(captures[ka],dx=sa_advance)
  tt['hmtx'][old]=(sa_advance+ka_advance,tt['hmtx'][old][1]);stats['inline_sa_ka']=True;stats['traditional_alternate']=alt
  stats['sa_advance']=sa_advance
 return captures,extra,stats,protect

def append_traditional_feature(tt,sa_advance):
 """Retain the original Malayalam construction as ss01 without changing input."""
 from fontTools.ttLib.tables import otTables
 old='SaKa.mlm';alt='SaKa.traditional.mlm';ka=tt.getBestCmap()[0xD15]
 if 'GDEF' in tt:
  gd=tt['GDEF'].table.GlyphClassDef.classDefs;gd[alt]=gd.get(old,1)
 # Copy original anchors for the retained form, and attach new default marks to
 # the Ka at the end of the inline construction.
 def anchors(st,kind):
  if kind==9:return anchors(st.ExtSubTable,st.ExtensionLookupType)
  if kind==4 and old in st.BaseCoverage.glyphs:
   names=st.BaseCoverage.glyphs;records=st.BaseArray.BaseRecord;i=names.index(old);original=deepcopy(records[i]);names.append(alt);records.append(original);st.BaseArray.BaseCount=len(records)
   if ka in names:
    replacement=deepcopy(records[names.index(ka)])
    for anchor in replacement.BaseAnchor:
     if anchor:anchor.XCoordinate+=round(sa_advance)
    records[i]=replacement
 if 'GPOS' in tt:
  for lookup in tt['GPOS'].table.LookupList.Lookup:
   for st in lookup.SubTable:anchors(st,lookup.LookupType)
 gsub=tt['GSUB'].table;lookup=otTables.Lookup();lookup.LookupType=1;lookup.LookupFlag=0;st=otTables.SingleSubst();st.mapping={old:alt};lookup.SubTable=[st];lookup.SubTableCount=1
 idx=len(gsub.LookupList.Lookup);gsub.LookupList.Lookup.append(lookup);gsub.LookupList.LookupCount+=1
 fr=otTables.FeatureRecord();fr.FeatureTag='ss01';fr.Feature=otTables.Feature();fr.Feature.FeatureParams=None;fr.Feature.LookupListIndex=[idx];fr.Feature.LookupCount=1
 fi=len(gsub.FeatureList.FeatureRecord);gsub.FeatureList.FeatureRecord.append(fr);gsub.FeatureList.FeatureCount+=1
 for sr in gsub.ScriptList.ScriptRecord:
  for lang in [sr.Script.DefaultLangSys]+[r.LangSys for r in sr.Script.LangSysRecord]:
   if lang:lang.FeatureIndex.append(fi);lang.FeatureCount=len(lang.FeatureIndex)
 indexed=sorted(enumerate(gsub.FeatureList.FeatureRecord),key=lambda p:p[1].FeatureTag);mapping={i:j for j,(i,_) in enumerate(indexed)};gsub.FeatureList.FeatureRecord=[r for _,r in indexed]
 for sr in gsub.ScriptList.ScriptRecord:
  for lang in [sr.Script.DefaultLangSys]+[r.LangSys for r in sr.Script.LangSysRecord]:
   if lang:
    lang.FeatureIndex=sorted(mapping[i] for i in lang.FeatureIndex)
    if lang.ReqFeatureIndex!=0xFFFF:lang.ReqFeatureIndex=mapping[lang.ReqFeatureIndex]
 tt.reorderGlyphs(tt.getGlyphOrder())
