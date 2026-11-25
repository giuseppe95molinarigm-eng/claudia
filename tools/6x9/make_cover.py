import pymupdf, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, out_pdf, out_png = sys.argv[1:4]
PAGES = 130
SPINE = PAGES * 0.002252 * 72          # white paper
TW, TH = 6 * 72, 9 * 72
B = 9.0
W = B + TW + SPINE + TW + B            # 903.08
H = B + TH + B                          # 666
s = 0.765                               # uniform scale of the original art
DPI = 600; K = DPI / 72
R = DPI * s                             # render dpi so render px == output px
orig = pymupdf.open(src)[0]
pix = orig.get_pixmap(matrix=pymupdf.Matrix(R / 72, R / 72), colorspace=pymupdf.csRGB)
full = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
r = R / 72                              # render px per original pt
extra = H - 810 * s

def panel(x0o, x1o, bands):
    """crop original x-range, then stretch horizontal bands (orig pt y0,y1,add_pt) to reach height H"""
    im = full.crop((round(x0o * r), 0, round(x1o * r), full.height))
    parts = []; y = 0
    for (a, b, add) in bands:
        pa, pb = round(a * r), round(b * r)
        parts.append(im.crop((0, y, im.width, pa)))
        band = im.crop((0, pa, im.width, pb))
        parts.append(band.resize((im.width, round((pb - pa) + add * K)), Image.LANCZOS))
        y = pb
    parts.append(im.crop((0, y, im.width, im.height)))
    out = Image.new('RGB', (im.width, sum(p.height for p in parts)))
    yy = 0
    for p in parts: out.paste(p, (0, yy)); yy += p.height
    return out.resize((round((B + TW) * K), round(H * K)), Image.LANCZOS)

# back: window starts at the left bleed edge; all extra height into the plain wall at the top
back = panel(0, (B + TW) / s, [(0, 11, extra)])
# front: center the title block (text spans 54..582pt of the 621pt panel)
x0 = 637.5 + ((54.1 + 582.5) * s / 2 - (TW / 2)) / s
front = panel(x0, x0 + (B + TW) / s, [(0, 18, extra - 20), (729, 746, 20)])
canvas = Image.new('RGB', (round(W * K), round(H * K)), (40, 30, 19))
canvas.paste(back, (0, 0))
canvas.paste(front, (round((B + TW + SPINE) * K), 0))
canvas.save(out_png, quality=95)
doc = pymupdf.open(); pg = doc.new_page(width=W, height=H)
pg.insert_image(pg.rect, filename=out_png)
doc.set_metadata({'title': 'Rituali di benessere dal mondo - copertina 6x9', 'author': 'Claudia Bindi'})
doc.save(out_pdf, deflate=True)
print('spine in', round(SPINE / 72, 4), 'cover in', round(W / 72, 4), 'x', H / 72, 'px', canvas.size, 'front x0', round(x0, 1))
