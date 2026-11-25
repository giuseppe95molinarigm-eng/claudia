"""blocks.json -> book.html (6x9in + KDP bleed, paged with Paged.js)."""
import json, sys, re, html
import pyphen

BLOCKS, OUT = sys.argv[1], sys.argv[2]
B = json.load(open(BLOCKS))
dic = pyphen.Pyphen(lang='it_IT', left=2, right=3)

H2_FIX = {'Il ritual e thailandese': 'Il rituale thailandese'}

def esc(t): return html.escape(t, quote=False)

WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{7,}")
def hyph(t):
    return WORD.sub(lambda m: dic.inserted(m.group(0), hyphen='­'), t)

def runs_html(runs, hy=True):
    out = []
    for s, t in runs:
        if s == 'BR': out.append('<br>'); continue
        if not t: continue
        x = esc(hyph(t) if (hy and s != 'I') else t)
        if s == 'I': x = f'<em>{x}</em>'
        elif s in ('B', 'Q'): x = f'<strong>{x}</strong>'
        elif s == 'E': x = f'<span class="emoji">{x.strip()}</span> '
        elif s == 'T': x = f'<span class="sym">{x}</span>'
        out.append(x)
    h = ''.join(out)
    h = re.sub(r'\s*<br>\s*', '<br>', h)
    return h.strip()

# ---------------- tables ----------------
ELEMENTS = [
    ('🌊', 'Acqua', ['Emotiva, bisognosa di leggerezza e calma interiore',
                    'Bagno caldo o pediluvio con sale, luci soffuse e respiro lento',
                    'Lavanda o rosa', 'Olio di mandorla e oliva', 'Onde del mare, handpan lento',
                    'Ambiente caldo, luci low-fi e luce della luna']),
    ('🔥', 'Fuoco', ['Tesa, irritabile, sovraccarica, con bisogno di “spegnere” l’intensità',
                    'Doccia fredda, journaling impulsivo, respirazione lenta',
                    'Lavanda, neem, camomilla', 'Olio leggero e neutro, non troppo caldo né speziato',
                    'Musica dolce, lenta e armonica',
                    'Momento rilassante, preferibilmente serale, con luci basse e un massaggio riequilibrante']),
    ('🌿', 'Terra', ['Pesante, bloccata, fuori focus, poco motivata',
                    'Spazzolatura a secco, leggera doccia energizzante, camminata consapevole',
                    'Agrumi, rosmarino, menta leggera', 'Olio leggero con note fresche e agrumate',
                    'Ritmi morbidi ma più vitali',
                    'Durante la giornata, in un momento di riattivazione, con una fragranza fresca al bambù o agli agrumi.']),
    ('🌬️', 'Aria', ['Confusa, mentalmente affaticata, dispersa, con bisogno di chiarezza e leggerezza',
                   'Respirazione consapevole, meditazione, qualche minuto all’aria aperta o una passeggiata nella natura',
                   'Eucalipto, pino, menta delicata', 'Olio di jojoba o vinaccioli con note balsamiche leggere',
                   'Suoni del vento, campane tibetane, musica ambient',
                   'Al mattino o nei momenti in cui hai bisogno di ritrovare lucidità, in un ambiente ben arieggiato e luminoso']),
]
EL_HEAD = ['Se oggi ti senti…', 'Rituale consigliato', 'Profumo', 'Oli', 'Musica', 'Momento ideale']
RITUALS = [
    ('Stanca mentalmente', 'Spegni il telefono per 20 minuti, prepara una tisana calda e massaggia lentamente le tempie con qualche goccia di olio essenziale di lavanda.'),
    ('Senza energia', 'Fai una doccia calda alternando qualche secondo di acqua fresca sulle gambe, poi applica un olio profumato sul corpo con movimenti energici.'),
    ('Contratta e rigida', 'Appoggia un asciugamano caldo su collo e spalle e fai respiri profondi mentre rilassi lentamente la muscolatura.'),
    ('Emotivamente sovraccarica', 'Accendi una candela, metti una musica lenta e abbracciati per qualche istante respirando profondamente. Anche il corpo ha bisogno di sentirsi accolto.'),
    ('Appesantita e gonfia', 'Prepara uno scrub naturale con sale grosso e olio, massaggiando gambe e piedi con movimenti dal basso verso l’alto.'),
    ('Disconnessa da te stessa', 'Rimani in silenzio per qualche minuto con le mani appoggiate sul cuore e sull’addome, respirando lentamente senza fare altro.'),
    ('Spenta nel viso', 'Immergi un panno in acqua tiepida, appoggialo sul viso e fai un delicato automassaggio con movimenti verso l’alto.'),
    ('Stressata e agitata', 'Fai un pediluvio caldo con sale e oli essenziali, lasciando che il respiro rallenti naturalmente.'),
    ('Con bisogno di coccole', 'Avvolgiti in una coperta morbida, bevi qualcosa di caldo e applica lentamente una crema profumata su mani e corpo.'),
    ('Con difficoltà a dormire', 'Prima di dormire massaggia i piedi con olio caldo e respira lentamente a luci soffuse, evitando schermi e rumori forti.'),
]

def table_html(name):
    if name == 'elements1':
        cards = []
        for em, nm, vals in ELEMENTS:
            rows = ''.join(f'<tr><th>{esc(h)}</th><td>{esc(hyph(v))}</td></tr>' for h, v in zip(EL_HEAD, vals))
            cards.append(f'<table class="el-card"><caption><span class="emoji">{em}</span> {nm}</caption><tbody>{rows}</tbody></table>')
        return '<div class="el-cards">' + ''.join(cards) + '</div>'
    if name == 'elements2':
        return ''
    if name == 'rituals':
        rows = ''.join(f'<tr><th>{esc(a)}</th><td>{esc(hyph(b))}</td></tr>' for a, b in RITUALS)
        return f'<table class="rituals"><thead><tr><th>Oggi ti senti…</th><th>Un piccolo rituale da fare a casa</th></tr></thead><tbody>{rows}</tbody></table>'

# ---------------- body ----------------
body = []; toc = []
nid = 0
def newid(p):
    global nid; nid += 1; return f'{p}{nid}'

i = 0
in_chapter = False
while i < len(B):
    b = B[i]; t = b['t']
    if t == 'part':
        pid = newid('part')
        title = '<br>'.join(esc(x) for x in b['title'])
        body.append(f'<section class="part" id="{pid}"><div class="part-inner"><div class="part-label">{esc(b["label"])}</div><div class="part-title">{title}</div></div></section>')
        toc.append(('part', pid, b['label'].title().replace('Parte ', 'PARTE ').upper(), ' '.join(b['title'])))
    elif t == 'opener':
        oid = newid('ch')
        if body and in_chapter: body.append('</section>')
        cls = 'chapter' if b['label'] else 'chapter unnumbered'
        h = [f'<section class="{cls}"><header class="opener" id="{oid}">']
        if b['label']: h.append(f'<div class="ch-label">{esc(b["label"])}</div>')
        h.append(f'<h1 class="ch-title">{esc(b["title"])}</h1><div class="ch-rule"></div>')
        for s in b['sub']: h.append(f'<p class="ch-sub">{esc(s)}</p>')
        if b.get('photo'): h.append(f'<figure class="ch-photo"><img src="assets/{b["photo"]}"></figure>')
        h.append('</header>')
        body.append(''.join(h)); in_chapter = True
        if b['label']:
            n = b['label'].split()[-1]
            toc.append(('ch', oid, f'Capitolo {n} - {b["title"]}', None))
        else:
            toc.append(('ch', oid, b['title'], None))
        if b['title'] == 'Ringraziamenti':
            pass
    elif t == 'h2':
        hid = newid('s')
        txt = b['text']
        for k, v in H2_FIX.items(): txt = txt.replace(k, v)
        body.append(f'<h2 id="{hid}">{esc(txt)}</h2>')
        toc.append(('sec', hid, txt, None))
        if txt.startswith('Come si costruisce un rituale personale') or False:
            pass
    elif t == 'p':
        body.append(f'<p>{runs_html(b["runs"])}</p>')
    elif t == 'opt':
        body.append(f'<p class="opt">{runs_html(b["runs"], hy=False)}</p>')
    elif t == 'q':
        body.append(f'<p class="quiz-q">{esc(b["runs"][0][1])}</p>')
    elif t == 'orn':
        body.append('<div class="orn"><img src="assets/orn.png"></div>')
    elif t == 'photo':
        body.append(f'<figure class="photo"><img src="assets/{b["file"]}"></figure>')
    elif t == 'table':
        body.append(table_html(b['name']))
    i += 1
    # page 92: writing page goes right before PART SIX
    if i < len(B) and B[i]['t'] == 'part' and B[i]['label'] == 'PARTE SESTA':
        lines = ''.join('<div class="wline"></div>' for _ in range(15))
        body.append('</section><section class="writing"><h2 class="w-title"><span class="emoji">✍️</span> “Scrivi qui il tuo rituale di felicità”</h2>'
                    f'<div class="wlines">{lines}</div><div class="orn"><img src="assets/orn.png"></div>'
                    '<p class="w-quote">“A volte il vero benessere non è un luogo.<br>È un momento in cui torni a sentirti bene dentro il tuo corpo.”</p>'
                    '</section>')
        in_chapter = False
if in_chapter: body.append('</section>')
body.append('<div class="contact"><div class="orn"><img src="assets/orn.png"></div>'
            '<p class="c1">Per informazioni su corsi, trattamenti e collaborazioni:</p>'
            '<p class="c2">massaggierituali@gmail.com</p></div>')

# Ringraziamenti tail text from page 102 is in blocks already (pages skip 102!) -> handled by build (SKIP_PAGES)

# ---------------- TOC ----------------
tl = []
for kind, ident, text, extra in toc:
    if kind == 'part':
        tl.append(f'<li class="t-part"><a href="#{ident}"><span class="t-txt"><em>{esc(text)}:</em> {esc(extra)}</span></a></li>')
    elif kind == 'ch':
        tl.append(f'<li class="t-ch"><a href="#{ident}"><span class="t-txt">{esc(text)}</span></a></li>')
    else:
        tl.append(f'<li class="t-sec"><a href="#{ident}"><span class="t-txt">{esc(text)}</span></a></li>')
toc_html = '<section class="toc"><h1 class="toc-title">Sommario</h1><div class="toc-rule"></div><ul>' + ''.join(tl) + '</ul></section>'

front = '''
<section class="titlepage"></section>
<section class="copyright"><div class="cp">
<p><strong>© 2026 Claudia Bindi. Tutti i diritti riservati.</strong></p>
<p>Nessuna parte di questa pubblicazione può essere riprodotta, distribuita o trasmessa in qualsiasi forma o con qualsiasi mezzo, inclusi fotocopiatura, registrazione o altri metodi elettronici o meccanici, senza il preventivo consenso scritto dell’autrice, eccetto nei casi di brevi citazioni incorporate in recensioni critiche e altri usi non commerciali consentiti dalla legge sul diritto d’autore.</p>
<p>Prima edizione: 2026</p>
<p>Stampato in Italia</p>
</div></section>
'''

tpl = open(sys.argv[3]).read()
out = tpl.replace('<!--FRONT-->', front).replace('<!--TOC-->', toc_html).replace('<!--BODY-->', '\n'.join(body))
open(OUT, 'w').write(out)
print('ok', len(body), 'toc', len(toc))
