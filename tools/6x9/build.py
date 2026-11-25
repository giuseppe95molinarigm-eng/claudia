"""Builds the semantic HTML body of the book from lines.json (+ image positions)."""
import json, sys, re, html
import pymupdf

SRC, LINES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
L = json.load(open(LINES))
doc = pymupdf.open(SRC)

PHOTOS = {191,230,242,253,260,265,270,275,278,282,286,291,294,298,304,308,312,317,328,335,339,343,347,353,355}
ORN = {202: 'orn', 203: 'orn'}
SKIP_PAGES = {1, 2, 3, 4, 92}
PART_PAGES = {8, 22, 55, 65, 79, 93}
TABLE_PAGES = {68: (269, 686, 'elements1'), 69: (67, 235, 'elements2'), 100: (67, 461, 'rituals')}

ST = {'ChaparralPro-Regular': 'R', 'ChaparralPro-Italic': 'I', 'ChaparralPro-Bold': 'B', 'Lora-Bold': 'H',
      'MinionPro-Bold': 'MB', 'MinionPro-BoldIt': 'MBI', 'Calibri-Light': 'C', 'SegoeUIEmoji': 'E',
      'TimesNewRomanPSMT': 'T'}

def esc(t): return html.escape(t, quote=False)

# ---------- per page items ----------
pages = {}
for l in L:
    pages.setdefault(l['p'], []).append(l)

def page_images(pn):
    out = []
    for im in doc[pn-1].get_image_info(xrefs=True):
        x = im['xref']; b = im['bbox']
        if x in PHOTOS: out.append(dict(kind='photo', y=b[1], file=f'photo_p{pn}.jpg', w=b[2]-b[0], h=b[3]-b[1]))
        elif x in ORN: out.append(dict(kind='orn', y=b[1]))
    return out

blocks = []      # list of dicts
para = None      # current paragraph {runs:[[style,text]], last:{x1}}
def flush():
    global para
    if para: blocks.append(para)
    para = None

def line_runs(l):
    rs = []
    for f, sz, col, t in l['runs']:
        s = ST.get(f, 'R')
        if s == 'H' and sz < 12: s = 'Q'
        rs.append([s, t])
    return rs

def style0(l):
    for f, sz, col, t in l['runs']:
        if t.strip():
            s = ST.get(f, 'R')
            return s, sz
    return 'R', 12

def add_runs(dst, rs):
    for s, t in rs:
        if s == 'Q': s = 'B'
        if dst and dst[-1][0] == s: dst[-1][1] += t
        else: dst.append([s, t])

def ends_hyphen(runs):
    t = runs[-1][1].rstrip() if runs else ''
    return len(t) > 1 and t.endswith('-') and t[-2].isalpha()

FULL = 560
prev_page_tail_full = False
cur_opener = None

for pn in sorted(pages):
    if pn in SKIP_PAGES: continue
    items = []
    for l in pages[pn]:
        s, sz = style0(l)
        if s == 'C' or l['y'] > 755: continue
        if pn == 102 and l['y'] > 250: continue
        if pn in TABLE_PAGES:
            a, b, name = TABLE_PAGES[pn]
            if a - 5 <= l['y'] <= b + 5: continue
        items.append(dict(kind='line', y=l['y'], l=l, s=s, sz=sz))
    items += page_images(pn)
    if pn in TABLE_PAGES:
        a, b, name = TABLE_PAGES[pn]
        items.append(dict(kind='table', y=a, name=name))
    items.sort(key=lambda it: it['y'])

    if pn in PART_PAGES:
        flush()
        lab = ' '.join(''.join(r[3] for r in it['l']['runs']).strip() for it in items if it['kind']=='line' and it['s']=='MB')
        tit = [''.join(r[3] for r in it['l']['runs']).strip() for it in items if it['kind']=='line' and it['s']=='MBI']
        blocks.append(dict(t='part', label=lab, title=tit))
        prev_page_tail_full = False
        continue

    prev = None  # previous item on this page
    first_text = True
    for it in items:
        k = it['kind']
        if k == 'photo':
            flush()
            if blocks and blocks[-1]['t'] == 'opener' and not blocks[-1].get('photo') and pn == blocks[-1]['page']:
                blocks[-1]['photo'] = it['file']
            else:
                blocks.append(dict(t='photo', file=it['file']))
            prev = it; continue
        if k == 'orn':
            flush(); blocks.append(dict(t='orn')); prev = it; continue
        if k == 'table':
            flush(); blocks.append(dict(t='table', name=it['name'])); prev = it; continue
        l = it['l']; s = it['s']; sz = it['sz']
        txt = ''.join(r[3] for r in l['runs'])
        if s == 'MB' and sz > 20:
            flush(); blocks.append(dict(t='opener', label=txt.strip(), title='', sub=[], page=pn)); prev = it; continue
        if s == 'MBI' and sz > 20:
            flush()
            if blocks and blocks[-1]['t'] == 'opener' and blocks[-1]['page'] == pn and not blocks[-1].get('photo') and not blocks[-1]['sub']:
                blocks[-1]['title'] = (blocks[-1]['title'] + ' ' + txt.strip()).strip()
            else:
                blocks.append(dict(t='opener', label='', title=txt.strip(), sub=[], page=pn))
            prev = it; continue
        if s == 'I' and blocks and blocks[-1]['t'] == 'opener' and blocks[-1]['page'] == pn and not blocks[-1].get('photo') and para is None:
            blocks[-1]['sub'].append(txt.strip()); prev = it; continue
        if s == 'H' and sz > 13:
            if para and para.get('t') == 'h2' and prev and prev['kind']=='line' and it['y'] - prev['y'] < 26:
                para['text'] += ' ' + txt.strip()
            else:
                flush(); para = dict(t='h2', text=txt.strip())
            prev = it; continue
        if s == 'H' and sz < 13:  # quiz question
            flush(); blocks.append(dict(t='q', runs=[['B', txt.strip()]])); prev = it; continue
        if s in ('I', 'R') and sz >= 13.5:  # closing quote (p92) - handled in template
            prev = it; continue
        # body text line
        rs = line_runs(l)
        opt = l['x0'] > 65 and re.match(r'^[A-E]\.\s', txt)
        cont = False
        if para is not None and para.get('t') == 'p' and prev is not None and prev['kind'] == 'line' and not opt:
            gap = it['y'] - prev['y']
            cont = gap < 21
        if first_text and prev is None and para is not None and para.get('t') == 'p' and prev_page_tail_full:
            cont = True
        if cont:
            r = para['runs']
            if ends_hyphen(r) and txt[:1].islower():
                r[-1][1] = r[-1][1].rstrip()[:-1]
            elif para['last_x1'] < FULL:
                r.append(['BR', ''])
            else:
                if not r[-1][1].endswith(' '): r[-1][1] += ' '
                rs[0][1] = rs[0][1].lstrip()
            add_runs(r, rs)
            para['last_x1'] = l['x1']
        else:
            flush()
            para = dict(t='opt' if opt else 'p', runs=[], last_x1=l['x1'])
            add_runs(para['runs'], rs)
        first_text = False
        prev = it
    # page tail
    prev_page_tail_full = bool(para is not None and para.get('t') == 'p' and para['last_x1'] >= FULL)
    if not prev_page_tail_full:
        flush()
flush()

# ---------- fix-ups ----------
import subprocess
import unicodedata
ref = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', SRC, '-'], capture_output=True, text=True).stdout)
VOC = set(w.lower() for w in re.findall(r'\w+', ref))
REAL1 = {'e','a','i','o','è','é','ed','ad','od'}
def fixlig(t, aggressive=False):
    def rep(m):
        a, b = m.group(1), m.group(2)
        j = (a + b).lower()
        if j in VOC and (a.lower() not in VOC or b.lower() not in VOC or a.lower().endswith(('fi','fl','ff'))):
            if a.lower() in REAL1 or b.lower() in REAL1:
                if not aggressive: return m.group(0)
            return a + b
        return m.group(0)
    pat = r'(\w*(?:fi|fl|ff|ffi|ffl)) (\w+)' if not aggressive else r'(\w+) (\w+)'
    prev = None
    while prev != t:
        prev = t; t = re.sub(pat, rep, t)
    return re.sub(r'  +', ' ', t)
for b in blocks:
    if 'runs' in b:
        for r in b['runs']: r[1] = fixlig(r[1])
        b.pop('last_x1', None)
    if b['t'] == 'h2': b['text'] = fixlig(fixlig(b['text']), True)
    if b['t'] == 'opener':
        b['title'] = fixlig(b['title']); b['sub'] = [fixlig(x) for x in b['sub']]
json.dump(blocks, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('blocks', len(blocks))
from collections import Counter
print(Counter(b['t'] for b in blocks))
