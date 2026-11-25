import subprocess, re, sys, unicodedata, difflib
def words(pdf, first, last):
    t = subprocess.run(['pdftotext', '-f', str(first), '-l', str(last), pdf, '-'], capture_output=True, text=True).stdout
    t = unicodedata.normalize('NFKC', t).replace('­', '')
    t = t.replace('RITUALI DI BENESSERE DAL MONDO', ' ')
    t = re.sub(r'(\w)[-‑]\n(\w)', r'\1\2', t)
    w = re.findall(r"[\w’']+", t)
    return [x for x in w if not x.isdigit() and not set(x) <= {'_'}]
src = words(sys.argv[1], 5, 102)
out = words(sys.argv[2], int(sys.argv[3]), 999)
sm = difflib.SequenceMatcher(None, src, out, autojunk=False)
n = 0
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op != 'equal':
        n += 1
        print(op, ' '.join(src[max(a1-3,0):a2+3])[:160], ' ||| ', ' '.join(out[max(b1-3,0):b2+3])[:160])
print('src words', len(src), 'out words', len(out), 'diffs', n, 'ratio', round(sm.ratio(), 5))
