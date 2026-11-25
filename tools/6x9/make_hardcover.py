"""KDP case-laminate hardcover cover, 6x9 trim, from the 8.5x11 paperback cover art."""
import pymupdf, sys
from PIL import Image, ImageOps
Image.MAX_IMAGE_PIXELS = None
src, out_pdf, out_jpg, PAGES = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
I = 72
WRAP = 0.591 * I              # wraps around the board (15 mm)
OVW, OVH = 0.197 * I, 0.118 * I   # board overhang beyond trim (width, top/bottom)
TW, TH = 6 * I, 9 * I
SPINE = (PAGES * 0.002252 + 0.189) * I
PW = WRAP + TW + OVW          # one panel: wrap + board
H = 2 * WRAP + TH + 2 * OVH
W = 2 * PW + SPINE
s = 0.74
DPI = 600; K = DPI / I
r = DPI * s / I               # render px per original pt (== output px per scaled pt)
pg = pymupdf.open(src)[0]
pix = pg.get_pixmap(matrix=pymupdf.Matrix(r, r), colorspace=pymupdf.csRGB)
full = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)

def stretch(im, bands):
    parts, y = [], 0
    for a, b, add in bands:
        pa, pb = round(a * r), round(b * r)
        parts.append(im.crop((0, y, im.width, pa)))
        parts.append(im.crop((0, pa, im.width, pb)).resize((im.width, pb - pa + round(add * K)), Image.LANCZOS))
        y = pb
    parts.append(im.crop((0, y, im.width, im.height)))
    out = Image.new('RGB', (im.width, sum(p.height for p in parts))); yy = 0
    for p in parts: out.paste(p, (0, yy)); yy += p.height
    return out

def mirror_pad(im, left=0, right=0, top=0, bottom=0):
    l, rr, t, b = (round(v * K) for v in (left, right, top, bottom))
    out = Image.new('RGB', (im.width + l + rr, im.height + t + b))
    out.paste(im, (l, t))
    if t: out.paste(ImageOps.flip(im.crop((0, 0, im.width, t))), (l, 0))
    if b: out.paste(ImageOps.flip(im.crop((0, im.height - b, im.width, im.height))), (l, t + im.height))
    if l: out.paste(ImageOps.mirror(out.crop((l, 0, 2 * l, out.height))), (0, 0))
    if rr: out.paste(ImageOps.mirror(out.crop((l + im.width - rr, 0, l + im.width, out.height))), (l + im.width, 0))
    return out

def edge_pad(im, side, pad_pt, strip_pt=6):
    """extend an edge by stretching a thin strip of the edge itself (no mirrored content)"""
    n = round(pad_pt * K); k = max(2, round(strip_pt * K))
    if n <= 0: return im
    if side in ('top', 'bottom'):
        st = im.crop((0, 0, im.width, k)) if side == 'top' else im.crop((0, im.height - k, im.width, im.height))
        st = st.resize((im.width, k + n), Image.LANCZOS)
        out = Image.new('RGB', (im.width, im.height + n))
        if side == 'top': out.paste(st, (0, 0)); out.paste(im.crop((0, k, im.width, im.height)), (0, k + n))
        else: out.paste(im.crop((0, 0, im.width, im.height - k)), (0, 0)); out.paste(st, (0, im.height - k))
    else:
        st = im.crop((0, 0, k, im.height)) if side == 'left' else im.crop((im.width - k, 0, im.width, im.height))
        st = st.resize((k + n, im.height), Image.LANCZOS)
        out = Image.new('RGB', (im.width + n, im.height))
        if side == 'left': out.paste(st, (0, 0)); out.paste(im.crop((k, 0, im.width, im.height)), (k + n, 0))
        else: out.paste(im.crop((0, 0, im.width - k, im.height)), (0, 0)); out.paste(st, (im.width - k, 0))
    return out

def tile_pad_bottom(im, pad_pt, strip_pt=6, clean=None):
    """extend the bottom by repeating the last strip, flipping every other copy (seamless planks).
    clean=(x1,x2) fraction of width: replace that span of the strip with wood copied sideways."""
    n = round(pad_pt * K); k = round(strip_pt * K)
    st = im.crop((0, im.height - k, im.width, im.height))
    if clean:   # inpaint the gold ornament/lines out of the wood strip
        import numpy as np, cv2
        a = np.asarray(st).copy(); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.int16)
        bg = cv2.blur(g, (61, 61)).astype(np.int16)
        m = ((g - bg) > 14).astype(np.uint8) * 255
        x1, x2 = int(clean[0] * im.width), int(clean[1] * im.width)
        m[:, :x1] = 0; m[:, x2:] = 0
        m = cv2.dilate(m, np.ones((9, 9), np.uint8))
        a = cv2.inpaint(a, m, 9, cv2.INPAINT_TELEA)
        st = Image.fromarray(a)
    fl = ImageOps.flip(st)
    out = Image.new('RGB', (im.width, im.height + n)); out.paste(im, (0, 0))
    y, i = im.height, 0
    while y < out.height:
        out.paste(fl if i % 2 == 0 else st, (0, y)); y += k; i += 1
    return out

def fit(im, x_off_pt, total_w_pt):
    """place im at x offset (pt, may be negative) in a strip total_w wide; mirror-fill gaps"""
    x = round(x_off_pt * K); Wpx = round(total_w_pt * K)
    if x < 0: im = im.crop((-x, 0, im.width, im.height)); x = 0
    if x + im.width > Wpx: im = im.crop((0, 0, Wpx - x, im.height))
    return mirror_pad(im, left=x / K, right=(Wpx - x - im.width) / K)

CUT = 805                                   # drop the last rows (outside the art)
full = full.crop((0, 0, full.width, round(CUT * r)))
extra = H - CUT * s
# FRONT (spine on the left, wrap on the right)
fr = full.crop((round(637.5 * r), 0, round(1258.5 * r), full.height))
a, b, top = 25, 25, 30
fr = stretch(fr, [(0, 18, a), (729, 746, b)])
fr = edge_pad(fr, 'top', top, 10)
fr = tile_pad_bottom(fr, extra - a - b - top, 18, clean=(0.25, 0.75))
safe_l, safe_r = 0.5 * I, TW + OVW - 0.25 * I            # hinge side / board edge side
txt_c = (54.1 + 582.5) / 2 * s
front = fit(fr, (safe_l + safe_r) / 2 - txt_c, PW)
# BACK (wrap on the left, spine on the right)
bk = full.crop((0, 0, round(621 * r), full.height))
a2 = 50
bk = stretch(bk, [(0, 11, a2)])
bk = edge_pad(bk, 'top', WRAP, 8)
bk = tile_pad_bottom(bk, extra - a2 - WRAP, 10)
off = WRAP + 12
bk = edge_pad(bk, 'left', off, 12 * s)       # plain wall/rug strip left of the frame line
back = fit(bk, 0, PW)
canvas = Image.new('RGB', (round(W * K), round(H * K)), (40, 30, 19))
canvas.paste(back.resize((round(PW * K), round(H * K))), (0, 0))
canvas.paste(front.resize((round(PW * K), round(H * K))), (round((PW + SPINE) * K), 0))
canvas.save(out_jpg, quality=95)
d = pymupdf.open(); p = d.new_page(width=W, height=H)
p.insert_image(p.rect, filename=out_jpg)
d.set_metadata({'title': 'Rituali di benessere dal mondo - copertina rigida 6x9', 'author': 'Claudia Bindi'})
d.save(out_pdf, deflate=True)
print(f'cover {W/I:.3f} x {H/I:.3f} in, spine {SPINE/I:.4f} in, px {canvas.size}')
geom = dict(W=W, H=H, PW=PW, SPINE=SPINE, WRAP=WRAP, OVW=OVW, OVH=OVH)
print(geom)
