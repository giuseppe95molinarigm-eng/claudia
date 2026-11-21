"""Mini text-layout interpreter for the InDesign PDF: finds text lines as TJ/Tj ops."""
import pikepdf
from pikepdf import Name

WINANSI = bytes(range(256)).decode('cp1252', errors='replace')
try:
    from fontTools.agl import toUnicode
except Exception:
    toUnicode = None
import unicodedata

def glyph_uni(name):
    special = {'hyphen':'-','space':' ','fi':'ﬁ','fl':'ﬂ','ff':'ﬀ','ffi':'ﬃ','ffl':'ﬄ'}
    if name in special: return special[name]
    if toUnicode:
        u = toUnicode(name)
        if u: return u
    try:
        return unicodedata.lookup(name)
    except Exception:
        return '?'

class FontInfo:
    def __init__(self, fobj):
        self.obj = fobj
        self.name = str(fobj.get('/BaseFont'))
        self.subtype = str(fobj.get('/Subtype'))
        self.cid = self.subtype == '/Type0'
        self.map = {}
        self.widths = {}
        if not self.cid:
            for c in range(256):
                ch = WINANSI[c]
                self.map[c] = ch
            enc = fobj.get('/Encoding')
            if isinstance(enc, pikepdf.Dictionary) and '/Differences' in enc:
                code = 0
                for it in enc.Differences:
                    if isinstance(it, int) or (hasattr(it,'__int__') and not isinstance(it, Name)):
                        try:
                            code = int(it); continue
                        except Exception: pass
                    self.map[code] = glyph_uni(str(it)[1:]); code += 1
            fc = int(fobj.get('/FirstChar', 0))
            for i, w in enumerate(fobj.get('/Widths', [])):
                self.widths[fc+i] = float(w)
        self.inv = {}
        for c, ch in self.map.items():
            self.inv.setdefault(ch, c)
    def decode(self, b):
        return ''.join(self.map.get(c, '?') for c in b)
    def width(self, code):
        return self.widths.get(code, 0.0)

def tj_items(op, operands):
    """Return list of [bytes, kern_after] from TJ / Tj."""
    if op == 'Tj':
        return [[bytes(operands[0]), 0.0]]
    items = []
    for x in operands[0]:
        if isinstance(x, pikepdf.String):
            items.append([bytes(x), 0.0])
        else:
            if items: items[-1][1] += float(x)
            else: items.append([b'', float(x)])
    return items

def mul(a, b):
    a0,a1,a2,a3,a4,a5 = a; b0,b1,b2,b3,b4,b5 = b
    return (a0*b0+a1*b2, a0*b1+a1*b3, a2*b0+a3*b2, a2*b1+a3*b3, a4*b0+a5*b2+b4, a4*b1+a5*b3+b5)

class Seg:
    pass

def scan_page(pdf, page):
    """Return (ops, segs, fonts). segs: text-show ops with geometry."""
    res = page.obj.get('/Resources', {})
    fontdict = res.get('/Font', {}) if res else {}
    fonts = {}
    for k in fontdict.keys():
        fonts[k] = FontInfo(fontdict[k])
    ops = list(pikepdf.parse_content_stream(page))
    segs = []
    ctm = (1,0,0,1,0,0); stack = []
    Tm = Tlm = (1,0,0,1,0,0)
    font = None; size = 1; Tc = 0; Tw = 0; Tz = 100; TL = 0
    for idx, (operands, op) in enumerate(ops):
        op = str(op)
        if op == 'q': stack.append(ctm)
        elif op == 'Q': ctm = stack.pop() if stack else ctm
        elif op == 'cm': ctm = mul(tuple(float(x) for x in operands), ctm)
        elif op == 'BT': Tm = Tlm = (1,0,0,1,0,0)
        elif op == 'Tf': font = fonts.get(str(operands[0])); size = float(operands[1]); fontkey=str(operands[0])
        elif op == 'Tc': Tc = float(operands[0])
        elif op == 'Tw': Tw = float(operands[0])
        elif op == 'Tz': Tz = float(operands[0])
        elif op == 'TL': TL = float(operands[0])
        elif op == 'Tm': Tm = Tlm = tuple(float(x) for x in operands)
        elif op in ('Td','TD'):
            tx, ty = float(operands[0]), float(operands[1])
            if op == 'TD': TL = -ty
            Tlm = mul((1,0,0,1,tx,ty), Tlm); Tm = Tlm
        elif op == 'T*':
            Tlm = mul((1,0,0,1,0,-TL), Tlm); Tm = Tlm
        elif op in ('TJ','Tj',"'",'"'):
            if op in ("'", '"'):
                Tlm = mul((1,0,0,1,0,-TL), Tlm); Tm = Tlm
                if op == '"': Tw = float(operands[0]); Tc = float(operands[1]); operands = [operands[2]]
                op2 = 'Tj'
            else: op2 = op
            items = tj_items(op2, operands)
            s = Seg(); s.idx = idx; s.op = op; s.font = font; s.fontkey = fontkey; s.size = size
            s.Tc, s.Tw, s.Tz = Tc, Tw, Tz; s.items = items
            trm = mul(Tm, ctm)
            s.x0, s.y = trm[4], trm[5]; s.scale = (trm[0]**2+trm[1]**2)**0.5
            # advance in text space units (unscaled by Tm)
            adv = 0
            for b, k in items:
                for c in b:
                    w = font.width(c) if font else 0
                    adv += (w/1000*size + Tc + (Tw if c == 32 else 0)) * Tz/100
                adv -= k/1000*size*Tz/100
            s.adv = adv
            s.x1 = s.x0 + adv*s.scale
            s.text = ''.join(font.decode(b) for b,_ in items) if font else ''
            Tm = mul((1,0,0,1,adv,0), Tm)
            segs.append(s)
    return ops, segs, fonts

def group_lines(segs, tol=0.5):
    lines = []
    for s in segs:
        if lines and abs(lines[-1][-1].y - s.y) < tol and s.x0 >= lines[-1][-1].x0 - 0.5:
            lines[-1].append(s)
        else:
            lines.append([s])
    return lines
