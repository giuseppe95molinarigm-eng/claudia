import sys, re, pyphen
sys.path.insert(0, sys.path[0])
from pdftext import *
LIG = {'ﬁ':'fi','ﬂ':'fl','ﬀ':'ff','ﬃ':'ffi','ﬄ':'ffl'}
def norm(t):
    for k,v in LIG.items(): t = t.replace(k+' ', v).replace(k, v)
    return t
dic = pyphen.Pyphen(lang='it_IT', left=2, right=2)
def line_text(L): return norm(''.join(s.text for s in L))
pdf = pikepdf.open(sys.argv[1])
allL = []
for pn, page in enumerate(pdf.pages):
    ops, segs, fonts = scan_page(pdf, page)
    for L in group_lines(segs): allL.append((pn+1, L))
bad = []; ok = 0
for i in range(len(allL)-1):
    pn, L = allL[i]; t = line_text(L).rstrip()
    if not t.endswith('-') or t.endswith(' -'): continue
    pn2, L2 = allL[i+1]; t2 = line_text(L2).lstrip()
    a = re.search(r"([\w’']+)-$", t); b = re.match(r"([\w’']+)", t2)
    if not a or not b: print('??', pn, repr(t[-30:]), repr(t2[:30])); continue
    fa, fb = a.group(1), b.group(1)
    w = fa + fb
    core = re.sub(r"^.*[’']", '', fa)  # elisions like dell’
    pos = [p for p in dic.positions(core+fb)]
    if len(core) in pos: ok += 1
    else:
        bad.append((pn, fa, fb, dic.inserted(core+fb)))
for b in bad: print(*b)
print('ok', ok, 'bad', len(bad))
