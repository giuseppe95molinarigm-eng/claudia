# Pipeline 6×9

Ricompone l'interno 8.5×11 in 6×9 pollici (6.125×9.25 con abbondanza KDP).

1. `extract_fonts.py`, `cff2otf.py`, `otf2ttf.py` – estraggono i font incorporati nel PDF e li rendono utilizzabili.
2. `assets.py`, `assets2.py` – foto (RGB) e decorazioni (fasce floreali, loto, pennellata dei numeri, sfondi).
3. `lines2.py` → `build.py` – testo strutturato (paragrafi, titoli, corsivi, grassetti) dal PDF sorgente.
4. `render.py` + `template.html` – HTML impaginato con Paged.js (sillabazione italiana con pyphen).
5. `print.js` (Playwright/Chromium) → `finalize.py` (MediaBox 441×666, TrimBox 432×648).
6. `compare.py` – confronto parola per parola con il sorgente.

Nota: in Paged.js 0.4 va applicata la correzione dell'offset dopo il trattino morbido (vedi commento "fix: a letter right after a soft hyphen").
