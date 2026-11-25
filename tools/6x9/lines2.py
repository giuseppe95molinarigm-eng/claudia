import pdfplumber, json, sys, unicodedata
LIG={'ﬀ':'ff','ﬁ':'fi','ﬂ':'fl','ﬃ':'ffi','ﬄ':'ffl'}
pdf=pdfplumber.open(sys.argv[1]); out=[]
for pn,p in enumerate(pdf.pages,1):
    chars=[c for c in p.chars if c['text']]
    # group by baseline (round)
    rows={}
    for c in chars:
        key=(round(c['y1'] - c['size']*0.0,0))
        base=round(c['bottom']-c['size']*0.22,0)  # approx baseline
        rows.setdefault(round(c['matrix'][5],0),[]).append(c)
    for y in sorted(rows, reverse=True):
        cs0=sorted(rows[y], key=lambda c:c['x0'])
        cs=[]; seen=set()
        for c in cs0:
            k=(c['text'],round(c['x0'],1))
            if k in seen: continue
            seen.add(k); cs.append(c)
        keep=[]
        for i,c in enumerate(cs):
            if c['text']==' ':
                prv=keep[-1] if keep else None
                nxt=next((d for d in cs[i+1:] if d['text']!=' '),None)
                if prv is not None and (len(prv['text'])>1 or prv['text'] in LIG) and c['x0']<prv['x1']-0.5: continue
                if nxt is not None and nxt['x0']<c['x0']+0.3*(c['x1']-c['x0']): continue
                if prv is not None and prv['text']==' ': continue
            keep.append(c)
        cs=keep
        runs=[]; prev=None
        for c in cs:
            f=c['fontname'].split('+')[-1]; sz=round(c['size'],1)
            col=c.get('non_stroking_color')
            t=c['text']
            t=LIG.get(t[0],t[0])+t[1:].rstrip() if t[0] in LIG else t
            if prev is not None:
                gap=c['x0']-prev['x1']
                if gap>0.45*sz and prev['text']!=' ' and t!=' ': t=' '+t
                if t==' ' and prev['text']==' ': t=''
            key=(f,sz,str(col))
            if runs and runs[-1][0]==key: runs[-1][1]+=t
            else: runs.append([key,t])
            prev=c
        txt=''.join(r[1] for r in runs)
        if not txt.strip(): continue
        out.append(dict(p=pn,y=round(p.height-y,1),x0=round(cs[0]['x0'],1),x1=round(cs[-1]['x1'],1),
            runs=[[k[0],k[1],k[2],t] for k,t in runs]))
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
