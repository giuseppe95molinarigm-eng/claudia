import pymupdf, sys
from PIL import Image
src,S=sys.argv[1],sys.argv[2]
Image.MAX_IMAGE_PIXELS=None
d=pymupdf.open(src)
# text-free p3 (toc bg)
p=d[2]
for b in p.get_text('dict')['blocks']:
    if b['type']==0: p.add_redact_annot(b['bbox'])
p.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED, text=pymupdf.PDF_REDACT_TEXT_REMOVE)
p.get_pixmap(dpi=300, colorspace=pymupdf.csRGB).save(f'{S}/nt/p3.png')
# original p1 with text
d2=pymupdf.open(src)
d2[0].get_pixmap(dpi=300, colorspace=pymupdf.csRGB).save(f'{S}/nt/p1_full.png')
K=300/72
def crop(f, box, out, q=None):
    im=Image.open(f'{S}/nt/{f}').convert('RGB')
    im=im.crop(tuple(int(round(v*K)) for v in box))
    if out.endswith('.jpg'): im.save(f'{S}/assets/{out}', quality=90)
    else: im.save(f'{S}/assets/{out}')
    print(out, im.size)
crop('p10.png',(0,0,621.36,106),'band_left.jpg')
crop('p11.png',(0,0,621.36,106),'band_right.jpg')
crop('p9.png',(0,0,621.36,216),'opener_band.jpg')
crop('p10.png',(38,757,92,781),'brush_left.png')
crop('p11.png',(529,757,583,781),'brush_right.png')
crop('p8.png',(0,0,621.36,810),'part_bg.jpg')
crop('p3.png',(0,0,621.36,810),'toc_bg.jpg')
crop('p2.png',(0,0,621.36,810),'copyright_bg.jpg')
# title page: scale to 441pt width, stretch a white band to reach 666pt height
W,H=int(441*K),int(666*K)
im=Image.open(f'{S}/nt/p1_full.png').convert('RGB')
sc=W/im.width
im=im.resize((W,int(im.height*sc)),Image.LANCZOS)
need=H-im.height
y0,y1=int(372*K*sc),int(388*K*sc)   # white band between subtitle and photo
top=im.crop((0,0,W,y0)); band=im.crop((0,y0,W,y1)); bot=im.crop((0,y1,W,im.height))
band=band.resize((W,band.height+need),Image.BILINEAR)
out=Image.new('RGB',(W,H),'white'); out.paste(top,(0,0)); out.paste(band,(0,y0)); out.paste(bot,(0,y0+band.height))
out.save(f'{S}/assets/title_page.jpg',quality=92); print('title',out.size)
