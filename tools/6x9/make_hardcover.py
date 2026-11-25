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

def extend_v(im, top_pt, bottom_pt, bottom_strip_pt, clean=None):
    """top: mirror of the top rows; bottom: seamless flip-tiling of a floor strip"""
    t, b = px(top_pt), px(bottom_pt)
    out = Image.new('RGB', (im.width, im.height + t + b))
    out.paste(im, (0, t))
    k = px(4)                                  # thin top strip (curtains/wall), no text
    out.paste(im.crop((0, 0, im.width, k)).resize((im.width, t), Image.LANCZOS), (0, 0))
    st = wood_strip(im, bottom_strip_pt, clean); fl = ImageOps.flip(st)
    y, i = t + im.height, 0
    while y < out.height:
        out.paste(fl if i % 2 == 0 else st, (0, y)); y += st.height; i += 1
    return out

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
top_f = 45
fr = extend_v(fr, top_f, extra - top_f, 18, clean=(0.25, 0.75))
txt_c = (54.1 + 582.5) / 2 * s
place(canvas, fr, (HINGE_R + LIVE[2]) / 2 - txt_c, FOLD_R, W)
# BACK: frame line kept inside the board, text inside the live area
bk = full.crop((0, 0, round(621 * r), full.height))
top_b = 85
bk = extend_v(bk, top_b, extra - top_b, 6)
place(canvas, bk, 30, 0, FOLD_L, left_fill='stretch')
canvas.save(out_jpg, quality=95)
d = pymupdf.open(); p = d.new_page(width=W, height=H)
p.insert_image(p.rect, filename=out_jpg)
d.set_metadata({'title': 'Rituali di benessere dal mondo - copertina rigida 6x9', 'author': 'Claudia Bindi'})
d.save(out_pdf, deflate=True)
print(f'{W/72:.3f} x {H/72:.3f} in, art scale {s}, px {canvas.size}')
