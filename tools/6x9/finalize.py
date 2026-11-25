import pikepdf, sys
pdf = pikepdf.open(sys.argv[1])
for i, p in enumerate(pdf.pages):
    right = (i % 2 == 0)            # page 1 is a recto
    p.MediaBox = [0, 0, 441, 666]
    p.CropBox = [0, 0, 441, 666]
    p.BleedBox = [0, 0, 441, 666]
    p.TrimBox = [0, 9, 432, 657] if right else [9, 9, 441, 657]
with pdf.open_metadata() as m:
    m['dc:title'] = 'Rituali di benessere dal mondo'
    m['dc:creator'] = ['Claudia Bindi']
pdf.docinfo['/Title'] = 'Rituali di benessere dal mondo'
pdf.docinfo['/Author'] = 'Claudia Bindi'
pdf.save(sys.argv[2])
print('saved', len(pdf.pages))
