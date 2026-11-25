import sys, glob, os
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
for fn in glob.glob(sys.argv[1] + '/*Pro-*.otf'):
    f = TTFont(fn)
    gs = f.getGlyphSet(); order = f.getGlyphOrder()
    glyf = newTable('glyf'); glyf.glyphOrder = order; glyf.glyphs = {}
    for g in order:
        pen = TTGlyphPen(gs)
        gs[g].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyf.glyphs[g] = pen.glyph()
    del f['CFF ']
    f['glyf'] = glyf; f['loca'] = newTable('loca')
    f['maxp'] = newTable('maxp'); m = f['maxp']; m.tableVersion = 0x00010000
    for a in ('maxZones','maxTwilightPoints','maxStorage','maxFunctionDefs','maxInstructionDefs','maxStackElements','maxSizeOfInstructions','maxComponentElements','maxPoints','maxContours','maxCompositePoints','maxCompositeContours','maxComponentDepth'):
        setattr(m, a, 0)
    m.maxZones = 1; m.numGlyphs = len(order)
    f['head'].glyphDataFormat = 0
    f['head'].indexToLocFormat = 0
    f['post'].formatType = 2.0; f['post'].extraNames = []; f['post'].mapping = {}
    f['post'].glyphOrder = order
    f['OS/2'].fsType = 0
    f.sfntVersion = '\x00\x01\x00\x00'
    out = fn[:-4] + '.ttf'
    f.save(out); print(out)
