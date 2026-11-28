"""AT-KPN. Editable Baloo-derived outlines with retained OpenType layout.

Cocon is used only through scalar design measurements. No Cocon font software
or outline data is read by this builder. The approved concept guides the cuts.
"""
from pathlib import Path
import argparse, copy, json, logging, math, unicodedata
from collections import Counter
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.merge import Merger, Options
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from ufoLib2 import Font as UFO
from outline_design import ContourPen, tangent, dot, sub, add, mul, length, draw_segment

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'design/config.json').read_text())
SCRIPTS=['Latin','Devanagari','Kannada','Malayalam','Tamil','Telugu','Bengali']
PREFIX={'Latin':'Baloo2','Devanagari':'Baloo2','Kannada':'BalooTamma2','Malayalam':'BalooChettan2','Tamil':'BalooThambi2','Telugu':'BalooTammudu2','Bengali':'BalooDa2'}
TAGS={'Latin':{'DFLT','latn'},'Devanagari':{'deva','dev2'},'Kannada':{'knda','knd2'},'Malayalam':{'mlym','mlm2'},'Tamil':{'taml','tml2'},'Telugu':{'telu','tel2'},'Bengali':{'beng','bng2'}}
BLOCKS={'Devanagari':(0x900,0x980),'Bengali':(0x980,0xA00),'Tamil':(0xB80,0xC00),'Telugu':(0xC00,0xC80),'Kannada':(0xC80,0xD00),'Malayalam':(0xD00,0xD80)}
PROFILE=json.loads((ROOT/'design/reference-profile.json').read_text())['references']
COPYRIGHT='Copyright (c) 2019 Ek Type (www.ektype.in). Copyright 2026 The AT-KPN Project Authors.'
SHARED={0x20,0xA0,0x200C,0x200D,0x2060,0xFEFF,0x25CC,0x964,0x965}

def source_path(script,weight):
    return ROOT/'sources/upstream/ttf'/f'{PREFIX[script]}-{CFG["source_instances"][weight]}.ttf'

def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def sculpt(contours,pen,limit,headline=None,protect_y=None):
    """Square alternating small convex corners; keep broad bowls and counters.

A corner can span multiple Bézier segments. We intersect its endpoint
 tangents, and only replace it if both tangent distances fit the stroke-end
 radius. Upper-left / lower-right stay crisp, their opposite returns stay soft.
    """
    changes=0
    areas=[sum(cross(s[0],s[-1]) for s in segs) for segs,_ in contours]
    outer=1 if not areas or max(areas,key=abs)>=0 else -1
    for segs,closed in contours:
        if not segs:continue
        
        # Start on a long straight so corners crossing the original start point
        # are considered as a complete curve run.
        lines=[(length(sub(s[-1],s[0])),j) for j,s in enumerate(segs) if len(s)==2]
        if lines:
            start=max(lines)[1];segs=segs[start:]+segs[:start]
        out=[];i=0;n=len(segs)
        pts=[p for s in segs for p in s]
        bw=max(p[0] for p in pts)-min(p[0] for p in pts)
        bh=max(p[1] for p in pts)-min(p[1] for p in pts)
        small_dot=bw<250 and bh<250 and min(bw,bh)>0 and .60<bw/bh<1.65 and sum(len(s)==2 for s in segs)<2
        while i<n:
            match=None
            if closed and not small_dot and len(segs[i])==4:
                for count in range(1,min(4,n-i)+1):
                    run=segs[i:i+count]
                    if any(len(s)!=4 for s in run):break
                    v=tangent(run[0]);w=tangent(run[-1],True)
                    if abs(dot(v,w))>.24 or cross(v,w)*outer<.75:continue
                    if max(abs(v[0]),abs(v[1]))<.94 or max(abs(w[0]),abs(w[1]))<.94:continue
                    a=run[0][0];b=run[-1][-1];den=cross(v,w)
                    t=cross(sub(b,a),w)/den;s=cross(v,sub(b,a))/den
                    if not (1<t<=limit and 1<s<=limit):continue
                    intersect=add(a,mul(v,t));mid=mul(add(a,b),.5)
                    sharp=(intersect[0]-mid[0])*(intersect[1]-mid[1])<0
                    if headline is not None and abs(intersect[1]-headline)<3:sharp=True
                    if protect_y is not None and max(p[1] for seg in run for p in seg)>=protect_y:sharp=False
                    if sharp:match=(count,a,intersect,b)
            if match:
                count,a,corner,b=match;out.extend([(a,corner),(corner,b)]);i+=count;changes+=1
            else:out.append(segs[i]);i+=1
        pen.moveTo(out[0][0])
        for s in out:draw_segment(pen,s)
        if closed:pen.closePath()
        else:pen.endPath()
    return changes

from english_refine import english

def map_tree(obj,sx,sy,dx=0,dy=0,seen=None):
    if obj is None or isinstance(obj,(str,int,float,bool,bytes)):return
    if seen is None:seen=set()
    if id(obj) in seen:return
    seen.add(id(obj))
    if isinstance(obj,(list,tuple)):
        for a in obj:map_tree(a,sx,sy,dx,dy,seen)
    elif hasattr(obj,'__dict__'):
        for k,v in vars(obj).items():
            if k in ('XCoordinate','XPlacement','XAdvance') and isinstance(v,(int,float)):setattr(obj,k,round(v*sx+(dx if k=='XCoordinate' else 0)))
            elif k in ('YCoordinate','YPlacement','YAdvance') and isinstance(v,(int,float)):setattr(obj,k,round(v*sy+(dy if k=='YCoordinate' else 0)))
            else:map_tree(v,sx,sy,dx,dy,seen)

def map_layout(tt,transforms,default):
    if 'GPOS' not in tt:return
    def anchors(obj,glyph):
        sx,sy,dx,dy=transforms.get(glyph,default);map_tree(obj,sx,sy,dx,dy)
    def apply(kind,st):
        if kind==9:return apply(st.ExtensionLookupType,st.ExtSubTable)
        if kind in (4,5,6):
            if kind==4:
                for g,r in zip(st.MarkCoverage.glyphs,st.MarkArray.MarkRecord):anchors(r,g)
                for g,r in zip(st.BaseCoverage.glyphs,st.BaseArray.BaseRecord):anchors(r,g)
            elif kind==5:
                for g,r in zip(st.MarkCoverage.glyphs,st.MarkArray.MarkRecord):anchors(r,g)
                for g,r in zip(st.LigatureCoverage.glyphs,st.LigatureArray.LigatureAttach):anchors(r,g)
            else:
                for g,r in zip(st.Mark1Coverage.glyphs,st.Mark1Array.MarkRecord):anchors(r,g)
                for g,r in zip(st.Mark2Coverage.glyphs,st.Mark2Array.Mark2Record):anchors(r,g)
        elif kind==3:
            for g,r in zip(st.Coverage.glyphs,st.EntryExitRecord):anchors(r,g)
        else:map_tree(st,*default[:2])
    for lookup in tt['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:apply(lookup.LookupType,st)

def names(tt,weight,script=None):
    family='AT-KPN'+(' '+script if script else '')
    ps='AT-KPN'+(script or '')+'-'+weight
    tt['name'].names=[]
    values={0:COPYRIGHT,1:family+' Light' if weight=='Light' else family,2:'Regular' if weight=='Light' else weight,3:f'{CFG["version"]};ATKP;{ps}',4:family+' '+weight,5:f'Version {CFG["version"]}',6:ps,8:'AT-KPN Project',9:'AT-KPN Project; upstream Baloo design by Ek Type',10:'Compact Latin and Indic family, adapted from Baloo 2 with original Latin drawings and asymmetric stroke ends. Approved Study 02 direction.',13:'This Font Software is licensed under the SIL Open Font License, Version 1.1.',14:'https://openfontlicense.org/open-font-license-official-text/',16:family,17:weight}
    for nid,value in values.items():
        tt['name'].setName(value,nid,3,1,0x409)
        tt['name'].setName(value,nid,1,0,0)
    os=tt['OS/2'];os.version=max(4,os.version);os.usWeightClass=CFG['weights'][weight];os.usWidthClass=5;os.fsType=0;os.achVendID='ATKP';os.sxHeight=550;os.sCapHeight=690
    os.fsSelection=(1<<7)|((1<<5) if weight=='Bold' else (1<<6))
    tt['head'].macStyle=1 if weight=='Bold' else 0;tt['head'].fontRevision=float(CFG['version'])
    tt.recalcTimestamp=False;tt['head'].created=tt['head'].modified=3878236800
    for tag in ('DSIG','STAT','fpgm','prep','cvt ','gasp','LTSH','hdmx'):
        if tag in tt:del tt[tag]
    tt['post'].underlinePosition=-100;tt['post'].underlineThickness={'Light':50,'Regular':65,'Bold':85}[weight]
    # One safe shared vertical metric across scripts and weights.
    ascent=1250;descent=1150
    os.usWinAscent=ascent;os.usWinDescent=descent;os.sTypoAscender=1100;os.sTypoDescender=-500;os.sTypoLineGap=0
    tt['hhea'].ascent=1100;tt['hhea'].descent=-500;tt['hhea'].lineGap=0

def subset_component(tt,script):
    for tag in ('GSUB','GPOS'):
        if tag in tt:
            sl=tt[tag].table.ScriptList;sl.ScriptRecord=[r for r in sl.ScriptRecord if r.ScriptTag in TAGS[script]];sl.ScriptCount=len(sl.ScriptRecord)
    cmap=tt.getBestCmap()
    if script=='Latin':
        keep={cp for cp in cmap if cp<0x900 or cp>=0x1D00 and not 0xA8E0<=cp<0xA900}
        keep |= SHARED
    else:
        a,b=BLOCKS[script];keep=set(range(a,b))|SHARED
        if script=='Devanagari':keep|=set(range(0x1CD0,0x1D00))|set(range(0xA8E0,0xA900))
    opt=subset.Options();opt.glyph_names=True;opt.name_IDs=['*'];opt.name_languages=['*'];opt.name_legacy=True;opt.layout_features=['*'];opt.layout_scripts=list(TAGS[script]);opt.notdef_glyph=True;opt.notdef_outline=True;opt.hinting=False
    s=subset.Subsetter(options=opt);s.populate(unicodes=keep);s.subset(tt)
    return tt

def export_editable(tt,script,weight):
    base=f'AT-KPN{script}-{weight}';u=UFO();u.info.familyName='AT-KPN '+script;u.info.styleName=weight;u.info.unitsPerEm=1000;u.info.ascender=1100;u.info.descender=-500;u.info.xHeight=550;u.info.capHeight=690;u.info.copyright=COPYRIGHT;u.info.openTypeNameLicense='SIL Open Font License 1.1';u.info.openTypeOS2WeightClass=CFG['weights'][weight];u.info.versionMajor=0;u.info.versionMinor=600
    cm=tt.getBestCmap();reverse={}
    for cp,n in cm.items():reverse.setdefault(n,[]).append(cp)
    gs=tt.getGlyphSet()
    for n in tt.getGlyphOrder():
        g=u.newGlyph(n);g.width=tt['hmtx'][n][0];g.unicodes=reverse.get(n,[]);gs[n].draw(g.getPen())
    u.glyphOrder=tt.getGlyphOrder();u.lib['com.atkpn.layout']='../../layout/'+base+'.ttx';u.features.text='# Layout is retained in the accompanying TTX. Build with tools/compile_edited.py.\n'
    u.save(ROOT/'sources/editable'/f'{base}.ufo',overwrite=True)
    tt.saveXML(ROOT/'sources/layout'/f'{base}.ttx',skipTables=['glyf','loca','hmtx'])

def build_component(script,weight,latin=None):
    (ROOT/'build/components').mkdir(parents=True,exist_ok=True)
    tt=subset_component(TTFont(source_path(script,weight)),script);gs=tt.getGlyphSet();cmap=tt.getBestCmap();reverse={n:chr(cp) for cp,n in cmap.items()}
    captures={};boxes={}
    for n in tt.getGlyphOrder():
        p=ContourPen(gs);gs[n].draw(p);captures[n]=p.contours;b=BoundsPen(gs);gs[n].draw(b);boxes[n]=b.bounds
    ref=next(r['metrics'] for r in PROFILE if ('Bold' in r['reference_file'])==(weight=='Bold'))
    sx=1 if script=='Latin' else CFG['native_width_scale'][script];sy=1.14 if script=='Latin' else 1
    extra={};native_stats={};protect=None
    if script!='Latin':
        from native_refine import refine
        captures,extra,native_stats,protect=refine(tt,captures,script,weight,sx)
    default=(sx,sy,0,0);transforms={};stats={'script':script,'weight':weight,'glyphs':len(captures),'sharpened_corners':0,'custom_glyphs':[],'refinement':native_stats}
    factors={}
    if script=='Latin':
        for char,r in ref.items():
            n=cmap.get(ord(char));b=boxes.get(n)
            if b and r['bounds'] and b[2]>b[0]:
                rb=r['bounds'];xs=(rb[2]-rb[0])/(b[2]-b[0]);ys=rb[3]/b[3] if b[3]>100 and rb[3]>100 else sy
                # Below the baseline a letter gets its own vertical factor, so descenders and
                # overshoots reach the reference depth without moving the x-height.
                ysb=min(max(rb[1]/b[1],.2),ys*1.2) if b[1]<-3 else ys
                factors[char]=(xs,ys,rb[0]-b[0]*xs,0,r['advance'],ysb)
    # Light takes the Regular reference; its custom l, i and I are narrower by the stem difference.
    light_trim=44 if weight=='Light' else 0
    for n in tt.getGlyphOrder():
        char=reverse.get(n,'');decomp=unicodedata.normalize('NFD',char) if char else '';base=decomp[0] if decomp else ''
        xs,ys,dx,dy=sx,sy,0,0;advance=round(tt['hmtx'][n][0]*sx);ysb=None;box=None
        if script=='Latin' and base in factors:
            xs,ys,dx,dy,advance,ysb=factors[base]
            # marks below the baseline (cedilla, ogonek, dot below) keep their own height
            if any(unicodedata.combining(c)!=230 for c in decomp[1:]):ysb=None
        if script=='Latin' and char in 'HeloIiMWwKN' and len(char)==1:
            # K, M, N, W and w keep the box mapping for their mark anchors; their outlines are drawn in the box
            if char not in 'MWwKN':xs=ys=1;dx=dy=0
            ysb=None
            box=list(ref[char]['bounds']);advance=ref[char]['advance']
            if char in 'li':box[2]-=light_trim
            if char in 'liI':advance-=light_trim
        esx,esy,edx,edy=extra.get(n,(1,1,0,0));transforms[n]=(xs*esx,ys*esy,dx+xs*edx,dy+ys*edy)
        mapped=[([tuple((x*xs+dx,y*(ysb if ysb is not None and y<0 else ys)+dy) for x,y in seg) for seg in segs],cl) for segs,cl in captures[n]]
        if script=='Latin' and len(base)==1 and base in 'bdhk' and 'n' in factors and base in factors:
            # Ascender letters were scaled to their ascender height, which left their bowls and arches
            # below the x-height in the lighter weights. Their x-height zone now takes the x-height
            # scale (as n does) and only the ascender above it is stretched to the ascender height.
            src_top=boxes[cmap[ord(base)]][3];y1=boxes[cmap[ord('n')]][3]+25;yn=factors['n'][1]
            top=src_top*ys;stretch=(top-y1*yn)/(src_top-y1)
            def lift(y):
                if y<0:return y
                y0=y/ys
                return y0*yn if y0<=y1 else y1*yn+(y0-y1)*stretch
            own=lambda segs:all(-30*ys<pt[1]<top+30 for s in segs for pt in s)
            mapped=[([tuple((pt[0],lift(pt[1])) for pt in s) for s in segs] if own(segs) else segs,cl) for segs,cl in mapped]
        if script=='Latin' and len(base)==1 and base in 'fr':
            from english_refine import widen_stem,STEM
            mapped=widen_stem(mapped,STEM[weight],ref[base]['bounds'][3])
        if script=='Tamil':
            from native_refine import circular_dots
            mapped,count=circular_dots(mapped);native_stats['circular_dots']=native_stats.get('circular_dots',0)+count
        pen=TTGlyphPen(None);q=Cu2QuPen(pen,max_err=.55)
        if script=='Latin' and len(char)==1 and english(q,char,weight,box,ref['x']['bounds'][3]):stats['custom_glyphs'].append(char)
        else:stats['sharpened_corners']+=sculpt(mapped,q,CFG['corner_limit'][weight],620 if script=='Devanagari' else 629 if script=='Bengali' else None,protect_y=protect)
        glyph=pen.glyph();tt['glyf'][n]=glyph;glyph.recalcBounds(tt['glyf']);tt['hmtx'][n]=(round(advance),getattr(glyph,'xMin',0))
    map_layout(tt,transforms,default)
    if script=='Malayalam':
        from native_refine import append_traditional_feature
        append_traditional_feature(tt,native_stats['sa_advance']*sx)
    if script=='Latin':
        rebuild_accents(tt,weight,stats)
        from latin_marks import add_marks
        stats['positioned_latin_marks']=add_marks(tt)
    elif latin:
        lc=latin.getBestCmap()
        for cp in SHARED:
            if cp in cmap and cp in lc:
                n=cmap[cp];ln=lc[cp];tt['glyf'][n]=copy.deepcopy(latin['glyf'][ln]);tt['hmtx'][n]=latin['hmtx'][ln]
    names(tt,weight,script);out=ROOT/'build/components'/f'AT-KPN{script}-{weight}.ttf';tt.save(out);tt=TTFont(out);export_editable(tt,script,weight)
    print(f'{weight} {script}: {stats["glyphs"]} glyphs, {stats["sharpened_corners"]} cut corners',flush=True)
    return tt,stats

def rebuild_accents(tt,weight,stats):
    """Draw canonical accents over custom bases, with zero added advance.

Upstream uses spacing accent glyphs for several combining codepoints. Explicit
 placement keeps these marks centered and avoids adding their spacing widths.
    """
    cm=tt.getBestCmap();gs=tt.getGlyphSet();rebuilt=[]
    for cp,name in list(cm.items()):
        text=unicodedata.normalize('NFD',chr(cp))
        if len(text)<2 or text[0] not in 'HeloIiMWwKN' or not all(ord(c) in cm for c in text):continue
        # Preserve complex horn/ogonek constructions until their entire joining
        # outline can be edited, rather than detaching a connected accent.
        # Latvian K and N with cedilla show a comma below; on the drawn K and N it is placed as one
        if text[0] in 'KN' and '\u0327' in text and 0x326 in cm:text=text.replace('\u0327','\u0326')
        if any(unicodedata.combining(c) not in (230,220) for c in text[1:]):continue
        base=cm[ord(text[0])];pen=TTGlyphPen(gs);p=Cu2QuPen(pen,max_err=.55);basep=ContourPen(gs);gs[base].draw(basep)
        for segs,closed in basep.contours:
            if text[0]=='i' and min(pt[1] for seg in segs for pt in seg)>550:continue
            p.moveTo(segs[0][0])
            for seg in segs:draw_segment(p,seg)
            p.closePath() if closed else p.endPath()
        bound=BoundsPen(gs);gs[base].draw(bound);bb=bound.bounds
        cx=(bb[0]+bb[2])/2;top=550 if text[0]=='i' else bb[3];bottom=bb[1]
        for mark in text[1:]:
            mn=cm[ord(mark)];bound=BoundsPen(gs);gs[mn].draw(bound);mb=bound.bounds
            if not mb:continue
            dx=cx-(mb[0]+mb[2])/2
            if unicodedata.combining(mark)==220:dy=bottom-35-mb[3];bottom=mb[1]+dy
            else:dy=top+35-mb[1];top=mb[3]+dy
            gs[mn].draw(TransformPen(p,(1,0,0,1,dx,dy)))
        g=pen.glyph();g.recalcBounds(tt['glyf']);tt['glyf'][name]=g;tt['hmtx'][name]=(tt['hmtx'][base][0],getattr(g,'xMin',0));rebuilt.append(chr(cp))
    stats['rebuilt_accents']=rebuilt

def replace_refs(obj,aliases,seen=None):
    if isinstance(obj,str):return aliases.get(obj,obj)
    if obj is None or isinstance(obj,(int,float,bool,bytes)):return obj
    if seen is None:seen=set()
    if id(obj) in seen:return obj
    seen.add(id(obj))
    if isinstance(obj,list):
        for i,v in enumerate(obj):obj[i]=replace_refs(v,aliases,seen)
    elif isinstance(obj,dict):
        for k,v in list(obj.items()):
            obj.pop(k);obj[aliases.get(k,k) if isinstance(k,str) else k]=replace_refs(v,aliases,seen)
    elif hasattr(obj,'__dict__'):
        for k,v in list(vars(obj).items()):setattr(obj,k,replace_refs(v,aliases,seen))
    return obj

def merge(weight):
    paths=[ROOT/'build/components'/f'AT-KPN{s}-{weight}.ttf' for s in SCRIPTS];fonts=[TTFont(p) for p in paths];orders=[f.getGlyphOrder() for f in fonts];cmaps=[f.getBestCmap() for f in fonts]
    opt=Options();opt.drop_tables=['STAT','DSIG'];tt=Merger(opt).merge([str(p) for p in paths]);order=tt.getGlyphOrder();offset=0;maps={}
    for script,o in zip(SCRIPTS,orders):maps[script]=dict(zip(o,order[offset:offset+len(o)]));offset+=len(o)
    aliases={};cm=tt.getBestCmap()
    for script,c in zip(SCRIPTS,cmaps):
        for cp in (0x200C,0x200D,0x2060,0xFEFF,0x25CC):
            if cp in c and cp in cm:
                old=maps[script][c[cp]];new=cm[cp]
                if old!=new:aliases[old]=new
    for tag in ('GSUB','GPOS','GDEF'):
        if tag in tt:replace_refs(tt[tag].table,aliases)
    tt.reorderGlyphs(tt.getGlyphOrder());names(tt,weight);tt['OS/2'].recalcUnicodeRanges(tt);tt['OS/2'].recalcCodePageRanges(tt)
    out=ROOT/'desktop'/f'AT-KPN-{weight}.ttf';tt.save(out);tt.flavor='woff2';tt.save(ROOT/'web'/f'AT-KPN-{weight}.woff2')
    (ROOT/'build'/f'merge-map-{weight}.json').write_text(json.dumps({'maps':maps,'aliases':aliases},indent=2)+'\n')
    result={'weight':weight,'glyphs':len(order),'unicode_characters':len(cm)};print('Merged '+str(result),flush=True);return result

if __name__=='__main__':
    logging.getLogger('fontTools').setLevel(logging.ERROR)
    parser=argparse.ArgumentParser();parser.add_argument('--weights',nargs='+',default=['Bold','Regular','Light']);parser.add_argument('--merge-only',action='store_true');args=parser.parse_args();reports=[]
    for weight in args.weights:
        if not args.merge_only:
            latin,stat=build_component('Latin',weight);reports.append(stat)
            for script in SCRIPTS[1:]:_,stat=build_component(script,weight,latin);reports.append(stat)
        reports.append(merge(weight))
    (ROOT/'qa/build-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
