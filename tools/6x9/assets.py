import pymupdf, sys, os
src,S=sys.argv[1],sys.argv[2]
d=pymupdf.open(src)
# text-free copy of selected pages
pages=[1,2,5,8,9,10,11,22,92,101,102]
for pn in pages:
    p=d[pn-1]
    for b in p.get_text('dict')['blocks']:
        if b['type']==0: p.add_redact_annot(b['bbox'])
    p.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE, text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    pix=p.get_pixmap(dpi=300, colorspace=pymupdf.csRGB)
    pix.save(f'{S}/nt/p{pn}.png')
# photos
d2=pymupdf.open(src)
photos={5:191,9:230,14:242,18:253,23:260,27:265,31:270,34:275,36:278,39:282,42:286,46:291,48:294,51:298,56:304,59:308,62:312,66:317,74:328,80:335,83:339,86:343,89:347,94:353,95:355}
for pn,x in photos.items():
    pix=pymupdf.Pixmap(d2,x)
    if pix.alpha: pix=pymupdf.Pixmap(pix,0)
    pix=pymupdf.Pixmap(pymupdf.csRGB,pix)
    pix.save(f'{S}/assets/photo_p{pn}.jpg', jpg_quality=92)
    print(pn,pix.width,pix.height)
