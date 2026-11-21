import sys; sys.path.insert(0, sys.path[0])
from textfix import run, seg_text_map
from pdftext import *
from fixhyph import chars_of, to_tj, width
E = [
 (34, "le Thailandese", "le thailandese"),
 (84, "senza che l’abbiate deciso", "senza che l’abbia deciso"),
 (84, "voi. La mascella", "tu. La mascella"),
]
run('v3.pdf', 'v4.pdf', edits=E, report='r2b.json')
# --- TOC page 4: fix 69->70 and redo "ed esperienza" without squeezing
pdf = pikepdf.open('v4.pdf'); ref = pikepdf.open('work1.pdf')
page = pdf.pages[3]
ops, segs, _ = scan_page(pdf, page)
rops, rsegs, _ = scan_page(ref, ref.pages[3])
by = {s.idx: s for s in segs}; rby = {s.idx: s for s in rsegs}
# 69 -> 70
s = by[409]; assert s.text == ' 69'
f = s.font
ops[409] = pikepdf.ContentStreamInstruction([pikepdf.Array([pikepdf.String(bytes([32, f.inv['7'], f.inv['0']]))])], pikepdf.Operator('TJ'))
# entry: original chars with "e esperienza" -> "ed esperienza", natural spacing
r = rby[350]; ch = chars_of(r)
txt, idx = seg_text_map(ch); k = txt.find('to e esperienza') + 3
i = idx[k]
d = {'code': r.font.inv['d'], 'u': 'd', 'k': 0.0}
nch = [dict(c) for c in ch[:i+1]]; nch[-1]['k'] = 0.0
nch += [d] + [dict(c) for c in ch[i+1:]]
delta = width(r, nch) - width(r, ch)
ops[350] = pikepdf.ContentStreamInstruction([to_tj(nch)], pikepdf.Operator('TJ'))
# leader: drop dot pairs from the start, keep its right end fixed
L = by[352]; lead = bytes(L.items[0][0]); u = L.size*L.Tz/100*L.scale/1000
pair = width(L, [{'code': c, 'u': '', 'k': 0} for c in lead[:2]])
n = 1
while n*pair < delta + 1.0: n += 1
newlead = lead[2*n:]
shift = n*pair
ops[352] = pikepdf.ContentStreamInstruction([pikepdf.Array([-shift/u, pikepdf.String(newlead)])], pikepdf.Operator('TJ'))
page.obj.Contents = pdf.make_stream(pikepdf.unparse_content_stream(ops))
pdf.save('v5.pdf')
print('delta', round(delta,2), 'dropped pairs', n)
