import sys, glob, os
from fontTools.cffLib import CFFFontSet
from fontTools.ttLib import TTFont, newTable
from fontTools.fontBuilder import FontBuilder
from fontTools.agl import toUnicode
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.boundsPen import BoundsPen
import io
for fn in glob.glob(sys.argv[1]+'/*.cff'):
    name=os.path.basename(fn)[:-4]
    cs=CFFFontSet(); cs.decompile(io.BytesIO(open(fn,'rb').read()), None)
    top=cs[cs.fontNames[0]]; chs=top.CharStrings
    order=top.charset
    cmap={}
    for g in order:
        if g=='.notdef': continue
        u=toUnicode(g)
        if len(u)==1: cmap.setdefault(ord(u),g)
    metrics={}
    gs=chs
    for g in order:
        c=chs[g]; c.decompile()
        bp=BoundsPen(chs); c.draw(bp); b=bp.bounds or (0,0,0,0)
        w=c.width
        metrics[g]=(int(round(w)), int(b[0]))
    fam,_,sty=name.partition('-')
    fb=FontBuilder(1000,isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.font['CFF ']=newTable('CFF '); fb.font['CFF '].cff=cs
    cs.fontNames=[name]; 
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900,descent=-300)
    fb.setupNameTable({'familyName':fam+'X','styleName':sty or 'Regular','psName':name+'X'})
    fb.setupOS2(sTypoAscender=750,sTypoDescender=-250,usWinAscent=950,usWinDescent=300)
    fb.setupPost(); fb.setupMaxp() if False else None
    ligs=[g for g in order if '_' in g or g in('fi','fl','ff','ffi','ffl')]
    rules=[]
    for g in sorted(ligs,key=lambda g:-len(g.replace('_',''))):
        comps=g.split('_') if '_' in g else list(g)
        if all(c in order for c in comps) and not comps[0].isupper():
            rules.append(f"sub {' '.join(comps)} by {g};")
    if rules:
        addOpenTypeFeaturesFromString(fb.font, "feature liga {\n"+"\n".join(rules)+"\n} liga;")
    fb.save(f'{sys.argv[1]}/{name}.otf'); print(name,len(order),len(cmap),rules)
