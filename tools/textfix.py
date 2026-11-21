import sys, json
sys.path.insert(0, sys.path[0])
from pdftext import *
from fixhyph import chars_of, to_tj, width, trim_w, compress, LIMIT, is_glue

EDITS = [
 (21, "la calore", "il calore"),
 (24, "duale e qualsiasi", "duale, e qualsiasi"),
 (26, "riguardo i fondamenti", "riguardo ai fondamenti"),
 (32, "una via nel mezzo", "una via di mezzo"),
 (38, "’, e è proprio", "’, ed è proprio"),
 (53, "da chi, e il modo in cui, la dice.", "da chi la dice e da come la dice."),
 (57, "sopraccigliare", "sopracciliare"),
 (57, "disteso ringiovanito ricompattato", "disteso, ringiovanito, ricompattato"),
 (67, "to e esperienza", "to ed esperienza"),
 (4, "trattamento e esperienza", "trattamento ed esperienza"),
 (68, "Nei rituali benessere", "Nei rituali di benessere"),
 (68, " Anche il profumo", "Anche il profumo"),
 (68, " Coinvolge memoria", "Coinvolge memoria"),
 (68, " Ci sono giorni", "Ci sono giorni"),
 (70, "riconosce e a", "riconosce e"),
 (70, "cui comincia ad anticipare", "che comincia ad anticipare"),
 (77, "Una enorme", "Un’enorme"),
 (85, "di una educazione", "di un’educazione"),
 (87, "e emotivo.", "ed emotivo."),
 (87, "di se stessi", "di sé stessi"),
 (95, "mi aveva convinto con", "mi aveva convinta con"),
 (95, "in me stesso.", "in me stessa."),
 (100, "una donna che non conosco il", "una donna di cui non conosco il"),
 (43, " E poi ci sono", "E poi ci sono"),
 (67, " Un aroma", "Un aroma"),
 (67, " Ogni essenza", "Ogni essenza"),
 (95, "calde  del", "calde del"),
]

def seg_text_map(chars):
    """text and list mapping text index -> char index"""
    txt = ''; idx = []
    for i, c in enumerate(chars):
        if is_glue(chars, i): continue
        for ch in c['u']:
            txt += ch; idx.append(i)
    return txt, idx

def run(src, dst, edits=EDITS, report=None):
    pdf = pikepdf.open(src)
    used = {}
    cache = {}
    def page_data(pn):
        if pn not in cache:
            ops, segs, fonts = scan_page(pdf, pdf.pages[pn])
            cache[pn] = (ops, segs, group_lines(segs))
        return cache[pn]
    for pn in range(len(pdf.pages)):
        ops, segs, lines = page_data(pn)
        for s in segs:
            if s.font:
                for b, _ in s.items: used.setdefault(s.font.name, set()).update(b)
    log = []
    dirty = set()
    for page, old, new in edits:
        ops, segs, lines = page_data(page-1)
        hits = []
        for li, L in enumerate(lines):
            for s in L:
                ch = getattr(s, '_chars', None) or chars_of(s)
                txt, idx = seg_text_map(ch)
                k = txt.find(old)
                if k >= 0: hits.append((li, s, ch, txt, idx, k))
        if len(hits) != 1:
            log.append({'page': page, 'old': old, 'status': f'MANUAL ({len(hits)} matches)'}); continue
        li, s, ch, txt, idx, k = hits[0]
        L = lines[li]
        a = idx[k]; b = idx[k+len(old)-1] + 1
        # new chars
        newc = []
        ok = True
        for u in new:
            code = s.font.inv.get(u)
            if code is None or code not in used.get(s.font.name, ()):
                ok = False; break
            newc.append({'code': code, 'u': u, 'k': 0.0})
        if not ok:
            log.append({'page': page, 'old': old, 'status': f'MANUAL (glyph {u!r} missing)'}); continue
        keep_k = ch[b-1]['k'] if b-1 < len(ch) else 0
        if newc: newc[-1]['k'] = 0.0
        nch = [dict(c) for c in ch[:a]] + newc + [dict(c) for c in ch[b:]]
        # geometry
        last = L[-1]
        orig_x1 = last.x0 + trim_w(last, chars_of(last)) if last is not s else s.x0 + trim_w(s, ch)
        is_last_seg = last is s
        delta = width(s, nch) - width(s, ch)
        new_x1 = orig_x1 + delta
        # paragraph continues? -> next line on page starts right below and line was full
        justified = orig_x1 >= LIMIT - 1.5 and abs(L[0].x0 - 54) < 1
        need = (new_x1 - LIMIT) if justified else max(0, new_x1 - LIMIT) if abs(L[0].x0-54) < 1 else 0
        if not is_last_seg: need = max(0.0, delta)   # keep following segment (e.g. TOC leader) clear
        r = compress(s, nch, need)
        if r is None:
            log.append({'page': page, 'old': old, 'status': 'MANUAL (does not fit)'}); continue
        nch, tight = r
        if not is_last_seg:
            between = [str(o[1]) for o in ops[s.idx+1:L[L.index(s)+1].idx]]
            if any(x in ('Td','TD','Tm','T*') for x in between) and abs(width(s, nch) - width(s, ch)) > 0.05:
                log.append({'page': page, 'old': old, 'status': 'MANUAL (repositioned segment)'}); continue
        s._chars = nch
        ops[s.idx] = pikepdf.ContentStreamInstruction([to_tj(nch)], pikepdf.Operator('TJ'))
        dirty.add(page-1)
        log.append({'page': page, 'old': old, 'new': new, 'status': 'fixed', 'justified': justified, 'adj_pt_per_space': round(tight, 2), 'x1': round(new_x1 - need, 1)})
    for pn in dirty:
        pdf.pages[pn].obj.Contents = pdf.make_stream(pikepdf.unparse_content_stream(cache[pn][0]))
    pdf.save(dst)
    for e in log: print(e)
    if report: json.dump(log, open(report, 'w'), ensure_ascii=False, indent=1)
    return log

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], report=sys.argv[3] if len(sys.argv) > 3 else None)
