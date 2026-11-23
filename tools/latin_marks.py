"""Explicit Latin mark attachment, including marks without precomposed forms."""
from copy import deepcopy
import unicodedata
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.boundsPen import BoundsPen

def add_marks(tt):
    cmap=tt.getBestCmap();gs=tt.getGlyphSet();marks={};bases={};boxes={}
    def bounds(name):
        if name not in boxes:
            p=BoundsPen(gs);gs[name].draw(p);boxes[name]=p.bounds
        return boxes[name]
    for cp,n in cmap.items():
        if 0x300<=cp<0x370 and bounds(n):
            cc=unicodedata.combining(chr(cp))
            marks[n]='BOTTOM' if cc in (202,220) else 'TOP'
            tt['hmtx'][n]=(0,tt['hmtx'][n][1])
        elif unicodedata.category(chr(cp)).startswith('L') and cp<0x2000 and bounds(n):bases[n]=cp
    fea=['languagesystem DFLT dflt;','languagesystem latn dflt;']
    for n,cl in marks.items():
        a,b,c,d=bounds(n);cy=d if cl=='BOTTOM' else b
        fea.append(f'markClass {n} <anchor {round((a+c)/2)} {round(cy)}> @MC_{cl};')
    fea.append('feature mark {')
    for n,cp in bases.items():
        a,b,c,d=bounds(n);cx=round((a+c)/2)
        if cp==ord('i'):d=550
        fea.append(f'pos base {n} <anchor {cx} {round(d+35)}> mark @MC_TOP <anchor {cx} {round(b-35)}> mark @MC_BOTTOM;')
    fea.append('} mark;');fea.append('feature mkmk {')
    for n,cl in marks.items():
        a,b,c,d=bounds(n);cy=b-35 if cl=='BOTTOM' else d+35
        fea.append(f'pos mark {n} <anchor {round((a+c)/2)} {round(cy)}> mark @MC_{cl};')
    fea.append('} mkmk;')
    temp=deepcopy(tt)
    for tag in ['GSUB','GPOS','GDEF']:
        if tag in temp:del temp[tag]
    addOpenTypeFeaturesFromString(temp,'\n'.join(fea))
    if 'GPOS' not in tt:tt['GPOS']=temp['GPOS']
    else:
        old=tt['GPOS'].table;new=temp['GPOS'].table;lookup_offset=len(old.LookupList.Lookup);feature_offset=len(old.FeatureList.FeatureRecord)
        for record in new.FeatureList.FeatureRecord:
            record.Feature.LookupListIndex=[i+lookup_offset for i in record.Feature.LookupListIndex]
        old.LookupList.Lookup.extend(new.LookupList.Lookup);old.LookupList.LookupCount=len(old.LookupList.Lookup)
        old.FeatureList.FeatureRecord.extend(new.FeatureList.FeatureRecord);old.FeatureList.FeatureCount=len(old.FeatureList.FeatureRecord)
        for nr in new.ScriptList.ScriptRecord:
            additions=[i+feature_offset for i in nr.Script.DefaultLangSys.FeatureIndex]
            matches=[r for r in old.ScriptList.ScriptRecord if r.ScriptTag==nr.ScriptTag]
            if matches:
                lang=matches[0].Script.DefaultLangSys
                if lang is None:
                    matches[0].Script.DefaultLangSys=nr.Script.DefaultLangSys;lang=matches[0].Script.DefaultLangSys;lang.FeatureIndex=additions
                else:lang.FeatureIndex.extend(additions)
                lang.FeatureCount=len(lang.FeatureIndex)
            else:
                nr.Script.DefaultLangSys.FeatureIndex=additions;old.ScriptList.ScriptRecord.append(nr)
        old.ScriptList.ScriptRecord.sort(key=lambda r:r.ScriptTag);old.ScriptList.ScriptCount=len(old.ScriptList.ScriptRecord)
        # Feature records must be sorted by tag, with every LangSys remapped.
        indexed=sorted(enumerate(old.FeatureList.FeatureRecord),key=lambda p:p[1].FeatureTag);mapping={old_i:new_i for new_i,(old_i,_) in enumerate(indexed)};old.FeatureList.FeatureRecord=[r for _,r in indexed]
        for sr in old.ScriptList.ScriptRecord:
            for lang in [sr.Script.DefaultLangSys]+[r.LangSys for r in sr.Script.LangSysRecord]:
                if lang:
                    lang.FeatureIndex=sorted(mapping[i] for i in lang.FeatureIndex)
                    if lang.ReqFeatureIndex!=0xFFFF:lang.ReqFeatureIndex=mapping[lang.ReqFeatureIndex]
    if 'GDEF' not in tt:tt['GDEF']=temp['GDEF']
    else:
        for n,cl in temp['GDEF'].table.GlyphClassDef.classDefs.items():tt['GDEF'].table.GlyphClassDef.classDefs[n]=cl
    return len(marks)
