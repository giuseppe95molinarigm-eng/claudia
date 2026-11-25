"""KDP case-laminate hardcover 6x9, 126 pages, geometry taken from the official KDP template.
The art is scaled uniformly (no stretching); extra height only fills the wrap/board margins."""
import pymupdf, sys
import numpy as np, cv2
from PIL import Image, ImageOps
Image.MAX_IMAGE_PIXELS = None
src, out_pdf, out_jpg = sys.argv[1:4]
# --- official template (pt) ---
W, H = 1012.28, 750.0
BOARD = (42.52, 42.47, 969.76, 707.48)        # board/trim edge (inside = visible cover)
FOLD_L, FOLD_R = 488.69, 523.59               # spine folds
HINGE_L, HINGE_R = 460.35, 551.94
LIVE = (51.52, 51.47, 960.76, 698.48)
s = 0.755
DPI = 600; K = DPI / 72; r = DPI * s / 72
pg = pymupdf.open(src)[0]
pix = pg.get_pixmap(matrix=pymupdf.Matrix(r, r), colorspace=pymupdf.csRGB)
full = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
full = full.crop((0, 0, full.width, round(805 * r)))      # drop the last rows outside the art
ART_H = 805 * s

def px(v): return round(v * K)

def wood_strip(im, k_pt, clean=None):
    k = px(k_pt); st = np.asarray(im.crop((0, im.height - k, im.width, im.height))).copy()
    if clean:
        g = cv2.cvtColor(st, cv2.COLOR_RGB2GRAY).astype(np.int16)
        m = ((g - cv2.blur(g, (61, 61)).astype(np.int16)) > 14).astype(np.uint8) * 255
        x1, x2 = int(clean[0] * im.width), int(clean[1] * im.width)
        m[:, :x1] = 0; m[:, x2:] = 0
        m = cv2.dilate(m, np.ones((9, 9), np.uint8))
        st = cv2.inpaint(st, m, 9, cv2.INPAINT_TELEA)
    return Image.fromarray(st)

def pingpong(band, length, first_flip=True):
    """fill `length` px by alternately reflected copies of band (seamless continuation)"""
    out = np.zeros((length, band.shape[1], 3), np.float32); y = 0; flip = first_flip
    while y < length:
        b = band[::-1] if flip else band
        n = min(len(b), length - y); out[y:y + n] = b[:n]; y += n; flip = not flip
    return out

def clean_wood_band(arr, y0, y1, xl, xr):
    """rebuild arr[y0:y1, xl:xr] (name/ornament) from the clean wood on both sides:
    fine texture from the sides (mirrored), lighting interpolated across"""
    B = arr[y0:y1].copy(); h, w, _ = B.shape
    lf = cv2.GaussianBlur(B, (0, 0), px(10)); hf = B - lf
    left_l = lf[:, max(0, xl - px(4)):xl].mean(axis=1); right_l = lf[:, xr:xr + px(4)].mean(axis=1)
    n = xr - xl
    t = np.linspace(0, 1, n, dtype=np.float32)[None, :, None]
    low = left_l[:, None, :] * (1 - t) + right_l[:, None, :] * t
    # planks run horizontally: the grain of each row is taken from the clean sides
    grain = np.concatenate([hf[:, :xl], hf[:, xr:]], axis=1).mean(axis=1)          # h x 3
    C = low + grain[:, None, :]
    fe = px(30); a = np.linspace(0, 1, fe, dtype=np.float32)[None, :, None]
    C[:, :fe] = B[:, xl:xl + fe] * (1 - a) + C[:, :fe] * a
    C[:, -fe:] = C[:, -fe:] * (1 - a[:, ::-1]) + B[:, xr - fe:xr] * a[:, ::-1]
    B[:, xl:xr] = C
    return B

def extend_v(im, top_pt, bottom_pt, top_band_pt, bottom_band=None):
    """top: ping-pong reflection of the top band (no text there);
    bottom: ping-pong reflection of a clean bottom band (optionally rebuilt wood)"""
    arr = np.asarray(im).astype(np.float32); h = arr.shape[0]
    t, b = px(top_pt), px(bottom_pt)
    out = np.zeros((h + t + b, arr.shape[1], 3), np.float32)
    out[t:t + h] = arr
    if t:
        out[:t] = pingpong(arr[:px(top_band_pt)], t)[::-1]
    if b:
        band = bottom_band if bottom_band is not None else arr[h - px(12):]
        f = pingpong(band, b)
        f = cv2.GaussianBlur(f, (0, 0), sigmaX=px(5), sigmaY=px(2))
        bl = min(px(4), b); a = np.linspace(0, 1, bl, dtype=np.float32)[:, None, None]
        f[:bl] = f[:bl] * a + band[-1:][::-1][:1] * (1 - a)
        out[t + h:] = f
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def place(canvas, im, x_pt, x_min, x_max, left_fill='mirror', right_fill='mirror'):
    """paste im at x_pt, clip to [x_min,x_max]; fill gaps by mirroring the edge columns"""
    x0, a, b = px(x_pt), px(x_min), px(x_max)
    if x0 < a: im = im.crop((a - x0, 0, im.width, im.height)); x0 = a
    if x0 + im.width > b: im = im.crop((0, 0, b - x0, im.height))
    strip = Image.new('RGB', (b - a, im.height)); strip.paste(im, (x0 - a, 0))
    gl = x0 - a; gr = b - (x0 + im.width)
    if gl > 0:
        k = px(6) if left_fill == 'stretch' else gl
        src_ = im.crop((0, 0, k, im.height))
        strip.paste(src_.resize((gl, im.height), Image.LANCZOS) if left_fill == 'stretch' else ImageOps.mirror(src_), (0, 0))
    if gr > 0: strip.paste(ImageOps.mirror(im.crop((im.width - gr, 0, im.width, im.height))), (x0 - a + im.width, 0))
    canvas.paste(strip, (a, 0))

extra = H - ART_H
canvas = Image.new('RGB', (px(W), px(H)), (40, 30, 19))
# FRONT: text block (54..582pt of the panel) centred in the front live area
fr = full.crop((round(637.5 * r), 0, round(1258.5 * r), full.height))
top_f = extra - 42.52                        # art bottom on the board edge: bottom fill only in the wrap
fa = np.asarray(fr).astype(np.float32)
wood = fa[round(798 * r):]                     # clean planks below the gold ornament
fr = extend_v(fr, top_f, extra - top_f, 17, bottom_band=wood)
txt_c = (54.1 + 582.5) / 2 * s
place(canvas, fr, (HINGE_R + LIVE[2]) / 2 - txt_c, FOLD_R, W)
# BACK: frame line kept inside the board, text inside the live area
bk = full.crop((0, 0, round(621 * r), full.height))
top_b = extra - 42.52                       # art bottom exactly on the board edge
bk = extend_v(bk, top_b, extra - top_b, 8)
place(canvas, bk, 30, 0, FOLD_L, left_fill='stretch')
canvas.save(out_jpg, quality=95)
d = pymupdf.open(); p = d.new_page(width=W, height=H)
p.insert_image(p.rect, filename=out_jpg)
d.set_metadata({'title': 'Rituali di benessere dal mondo - copertina rigida 6x9', 'author': 'Claudia Bindi'})
d.save(out_pdf, deflate=True)
print(f'{W/72:.3f} x {H/72:.3f} in, art scale {s}, px {canvas.size}')
