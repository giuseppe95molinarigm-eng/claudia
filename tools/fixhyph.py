import sys, re, json, pyphen
sys.path.insert(0, sys.path[0])
from pdftext import *

def islig(u): return isinstance(u, str) and len(u) > 1
ACCEPT = {('le','altà'), ('oce','anico')}
LIMIT = 567.40
SP_CAP = 1.0     # max tightening per word space (pt)
CH_CAP = 0.06    # max tightening per glyph (pt)
dic = pyphen.Pyphen(lang='it_IT', left=2, right=2)

OVR = {}
def chars_of(seg):
    if id(seg) in OVR: return [dict(c) for c in OVR[id(seg)]]
    out = []
    for b, k in seg.items:
        for c in b:
            out.append({'code': c, 'u': seg.font.decode(bytes([c])), 'k': 0.0})
        if out: out[-1]['k'] += k
    return out

def to_tj(chars):
    arr = []; cur = bytearray()
    for ch in chars:
        cur.append(ch['code'])
        if abs(ch['k']) > 1e-6:
            arr.append(pikepdf.String(bytes(cur))); arr.append(round(ch['k'], 2)); cur = bytearray()
    if cur: arr.append(pikepdf.String(bytes(cur)))
    return pikepdf.Array(arr)

def unit(seg):  # pt per 1 kern unit
    return seg.size*seg.Tz/100*seg.scale/1000

def width(seg, chars):
    adv = 0
    for ch in chars:
        c = ch['code']
        adv += (seg.font.width(c)/1000*seg.size + seg.Tc + (seg.Tw if c == 32 else 0)) * seg.Tz/100
        adv -= ch['k']/1000*seg.size*seg.Tz/100
    return adv * seg.scale

def trim_w(seg, chars):
    k = len(chars)
    while k and chars[k-1]['u'] == ' ': k -= 1
    return width(seg, chars[:k])

def letters(chars): return ''.join(c['u'] for c in chars)

def is_glue(chars, j):  # space right after a ligature glyph (InDesign artefact)
    return chars[j]['u'] == ' ' and j > 0 and islig(chars[j-1]['u'])

def word_tail(chars):
    j = len(chars) - 1
    while j > 0:
        u = chars[j-1]['u']
        if u == ' ' and is_glue(chars, j-1): j -= 1; continue
        if not (u.isalpha() or islig(u)): break
        j -= 1
    return j

def word_head(chars):
    j = 0
    while j < len(chars):
        u = chars[j]['u']
        if is_glue(chars, j): j += 1; continue
        if not (u.isalpha() or islig(u)): break
        j += 1
    return j

def expand(chars, font):
    out = []
    for i, c in enumerate(chars):
        if is_glue(chars, i):
            continue  # drop glue space and its kerning
            continue
        if islig(c['u']) and all(l in font.inv for l in c['u']):
            for n, l in enumerate(c['u']):
                out.append({'code': font.inv[l], 'u': l, 'k': 0.0})
            continue
        out.append(dict(c, k=0.0))
    return out

def remap(c, font):
    if c['u'] not in font.inv: return None
    return dict(c, code=font.inv[c['u']])

def compress(seg, chars, need):
    """need>0: tighten by need pt; need<0: loosen. Returns (chars, |per-space pt|) or None"""
    chars = [dict(c) for c in chars]
    if abs(need) < 0.01: return chars, 0.0
    k = len(chars)
    while k and chars[k-1]['u'] == ' ': k -= 1
    spaces = [i for i in range(k) if chars[i]['u'] == ' ' and not is_glue(chars, i)]
    u = unit(seg)
    if need > 0:
        per_sp = min(SP_CAP, need/len(spaces)) if spaces else 0
    else:
        per_sp = need/len(spaces) if spaces else 0
    rest = need - per_sp*len(spaces)
    per_ch = 0
    if abs(rest) > 1e-6:
        if k < 2: return None
        per_ch = rest/(k-1)
        if abs(per_ch) > CH_CAP: return None
    for i in spaces: chars[i]['k'] += per_sp/u
    if per_ch:
        for i in range(k-1): chars[i]['k'] += per_ch/u
    return chars, abs(per_sp) + abs(per_ch)*5

def process(path, out, report):
    pdf = pikepdf.open(path)
    pages, allL = [], []
    for pn, page in enumerate(pdf.pages):
        ops, segs, fonts = scan_page(pdf, page)
        pages.append(ops)
        for L in group_lines(segs):
            if L[0].y < 55: continue
            allL.append((pn, L))
    log, dirty = [], set()
    for i in range(len(allL)-1):
        pn, L = allL[i]; pn2, L2 = allL[i+1]
        A = L[-1]; B = L2[0]
        ca = chars_of(A)
        if not ca or ca[-1]['u'] != '-': continue
        cb = chars_of(B)
        ja = word_tail(ca); jb = word_head(cb)
        fa = letters([c for n, c in enumerate(ca[ja:-1]) if not is_glue(ca, ja+n)])
        fb = letters([c for n, c in enumerate(cb[:jb]) if not is_glue(cb, n)])
        if not fa or not fb or (fb.isupper() and len(fb) > 1): continue
        word = fa + fb
        if (fa, fb) in ACCEPT: continue
        pos = dic.positions(word.lower())
        if len(fa) in pos: continue
        entry = {'page': pn+1, 'page2': pn2+1, 'old': f'{fa}-{fb}'}
        if A.font.name != B.font.name or abs(L[0].x0-54) > 1 or abs(L2[0].x0-54) > 1:
            entry['status'] = 'MANUAL (font/frame differs)'; log.append(entry); continue
        # B line: segments after B must be chained (no repositioning) to shift correctly
        opsB = pages[pn2]
        if len(L2) > 1:
            between = [str(o[1]) for o in opsB[B.idx+1:L2[1].idx]]
            if any(x in ('Td','TD','Tm','T*') for x in between):
                entry['status'] = 'MANUAL (repositioned line B)'; log.append(entry); continue
        hy = dict(ca[-1], k=0.0)
        frontA = ca[:ja]
        wchars = expand(ca[ja:-1], A.font) + expand(cb[:jb], B.font)
        if letters(wchars) != word:
            entry['status'] = 'MANUAL (glyphs)'; log.append(entry); continue
        restB = cb[jb:]
        xb_orig = B.x0 + (trim_w(B, cb) if len(L2) == 1 else 0)
        if len(L2) > 1: xb_orig = L2[-1].x0 + trim_w(L2[-1], chars_of(L2[-1]))
        justB = xb_orig >= LIMIT - 1.5
        entry['justB'] = justB
        lineB_extra = L2[-1].x1 - B.x1   # width of trailing segs
        cands = []
        options = [p for p in pos if p >= 2 and len(word)-p >= 2]
        options.append(0)
        if restB and restB[0]['u'] == ' ': options.append(len(word))
        for p in options:
            na = [dict(c) for c in wchars[:p]]; nb = [dict(c) for c in wchars[p:]]
            na = [remap(c, A.font) for c in na]; nb = [remap(c, B.font) for c in nb]
            if None in na or None in nb: continue
            if p == 0:
                newA = frontA; newB = nb + restB
            elif p == len(word):
                newA = frontA + na; newB = restB[1:]
            else:
                newA = frontA + na + [hy]; newB = nb + restB
            xa = A.x0 + trim_w(A, newA)
            xb = B.x0 + (trim_w(B, newB) if len(L2) == 1 else width(B, newB) + lineB_extra)
            if len(L2) > 1:  # trailing spaces of last seg
                xb = L2[-1].x0 + (width(B, newB) - width(B, cb)) + trim_w(L2[-1], chars_of(L2[-1])) if L2[-1] is not B else xb
            ra = compress(A, newA, xa - LIMIT)
            rb = compress(B, newB, (xb - LIMIT) if (justB or xb > LIMIT) else 0)
            if ra is None or rb is None: continue
            cost = max(ra[1], rb[1]) + (0.3 if p in (0, len(word)) else 0) + 0.02*abs(p-len(fa)) + (0.2 if len(word)-p == 2 else 0)
            cands.append((cost, p, ra[0], rb[0], round(xa,1), round(xb,1), round(ra[1],2), round(rb[1],2)))
        if not cands:
            entry['status'] = 'MANUAL (no fitting split)'; log.append(entry); continue
        cands.sort(key=lambda c: c[0])
        cost, p, newA, newB, xa, xb, sa, sb = cands[0]
        opsA = pages[pn]
        if str(opsA[A.idx][1]) != 'TJ' or str(opsB[B.idx][1]) != 'TJ':
            entry['status'] = 'MANUAL (op)'; log.append(entry); continue
        OVR[id(A)] = newA; OVR[id(B)] = newB
        opsA[A.idx] = pikepdf.ContentStreamInstruction([to_tj(newA)], pikepdf.Operator('TJ'))
        opsB[B.idx] = pikepdf.ContentStreamInstruction([to_tj(newB)], pikepdf.Operator('TJ'))
        dirty |= {pn, pn2}
        entry['new'] = word if p in (0, len(word)) else word[:p] + '-' + word[p:]
        if p == 0: entry['new'] = '(a capo) ' + word
        if p == len(word): entry['new'] = word + ' (riga sopra)'
        entry.update(status='fixed', xA=xa, xB=xb, tightA=sa, tightB=sb, yA=round(L[0].y,1), yB=round(L2[0].y,1))
        log.append(entry)
    for pn in dirty:
        pdf.pages[pn].obj.Contents = pdf.make_stream(pikepdf.unparse_content_stream(pages[pn]))
    pdf.save(out)
    json.dump(log, open(report, 'w'), ensure_ascii=False, indent=1)
    for e in log: print(e['page'], e['old'], '->', e.get('new'), e['status'], e.get('xA',''), e.get('xB',''), e.get('tightA',''), e.get('tightB',''))
    print(sum(e['status']=='fixed' for e in log), 'fixed of', len(log))

if __name__ == '__main__':
    process(*sys.argv[1:4])
