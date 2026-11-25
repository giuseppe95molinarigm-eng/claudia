import pikepdf, sys, io, os
from fontTools.ttLib import TTFont
from fontTools.cffLib import CFFFontSet
from fontTools.fontBuilder import FontBuilder
from fontTools.agl import toUnicode
pdf=pikepdf.open(sys.argv[1]); out=sys.argv[2]
seen={}
for page in pdf.pages:
    fonts=page.Resources.get('/Font',{})
    for k,f in fonts.items():
        bf=str(f.BaseFont).split('+')[-1]
        if bf in seen: continue
        st=str(f.Subtype)
        d=f.DescendantFonts[0] if st=='/Type0' else f
        fd=d.get('/FontDescriptor')
        if fd is None: continue
        for key in ('/FontFile3','/FontFile2','/FontFile'):
            if key in fd:
                seen[bf]=(key, fd[key].read_bytes(), st, f); break
for bf,(key,data,st,f) in seen.items():
    print(bf,key,st,len(data), f.get('/Encoding'))
    open(f'{out}/{bf}.{"cff" if key=="/FontFile3" else "ttf"}','wb').write(data)
