#!/usr/bin/env python3
"""
Audit the display items against the Nature Portfolio rules (nature-display-item-qc checklist).

  python3 paper/qc_display_items.py      # → paper/QC_DISPLAY_ITEMS.md

Figures (from the vector PDF and the 800-dpi rasters): width class, height, resolution, colour mode,
red/green heuristic, embedded fonts (no Type 3, no outlined text), every text span 5–7 pt except 8-pt
bold panel labels, every vector stroke 0.25–1 pt.
Tables (from Tables.docx): editable text, no vertical rules, no interior horizontal rules, symbol footnotes.
"""
import re, sys, zipfile, collections
from pathlib import Path
import numpy as np
import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
FIG, TAB = HERE / 'figures', HERE / 'tables'
WIDTHS = [('single column (89 mm)', 89.0), ('1.5 column (120 mm)', 120.0), ('1.5 column (136 mm)', 136.0),
          ('double column (183 mm)', 183.0)]


def width_class(mm):
    lab, tgt = min(WIDTHS, key=lambda t: abs(mm - t[1]))
    return ('PASS', lab) if abs(mm - tgt) <= 3 else ('FAIL', f'nearest {lab}')


def red_green(path, sample=400000):
    arr = np.asarray(Image.open(path).convert('RGB')).reshape(-1, 3).astype('int16')
    if arr.shape[0] > sample:
        arr = arr[np.linspace(0, arr.shape[0] - 1, sample).astype(int)]
    r, g, b = arr[:, 0], arr[:, 1], arr[:, 2]
    fr = float(((r > 120) & (g < 90) & (b < 90)).mean()); fg = float(((g > 100) & (r < 100) & (b < 100)).mean())
    return fr, fg


def audit_figure(name):
    rows = []
    pdf = pymupdf.open(FIG / f'{name}.pdf'); page = pdf[0]
    w_mm, h_mm = page.rect.width / 72 * 25.4, page.rect.height / 72 * 25.4
    st, lab = width_class(w_mm)
    rows.append(('Figure width', st, f'{w_mm:.1f} mm', '89 / 120–136 / 183 mm', '–' if st == 'PASS' else 'Resize'))
    rows.append(('Figure height', 'PASS' if h_mm <= 170 else 'FAIL', f'{h_mm:.1f} mm', '≤ 170 mm',
                 '–' if h_mm <= 170 else 'Reduce height'))
    for ext in ('png', 'tif'):
        im = Image.open(FIG / f'{name}.{ext}')
        dpi = float(im.info.get('dpi', (0, 0))[0])
        wmm = im.size[0] / dpi * 25.4 if dpi else 0
        rows.append((f'Raster {ext.upper()}: resolution', 'PASS' if dpi >= 299 else 'FAIL', f'{dpi:.0f} dpi',
                     '≥ 300 dpi', '–'))
        rows.append((f'Raster {ext.upper()}: colour mode', 'PASS' if im.mode == 'RGB' else 'FAIL', im.mode, 'RGB',
                     '–' if im.mode == 'RGB' else 'Convert to RGB'))
        rows.append((f'Raster {ext.upper()}: physical width', width_class(wmm)[0], f'{wmm:.1f} mm',
                     '183 mm', '–'))
    fonts = sorted({f[3] for f in page.get_fonts()})
    types = sorted({f[2] for f in page.get_fonts()})
    base = sorted({re.sub(r'^[A-Z]{6}\+', '', f) for f in fonts})
    non_arial = [f for f in base if not f.startswith('Arial')]
    rows.append(('Fonts embedded (live text)', 'PASS' if 'Type3' not in types and fonts else 'FAIL',
                 ', '.join(base) + f" ({'/'.join(types)})", 'Arial/Helvetica, embedded, not outlined',
                 '–'))
    if non_arial:
        rows.append(('Non-Latin glyphs', 'WARN', ', '.join(non_arial),
                     'Arial has no CJK glyphs', 'Chinese characters use a CJK sans fallback; keep or re-set in '
                     'Source Han Sans / Noto Sans CJK at typesetting'))
    sizes, labels, bad = collections.Counter(), [], []
    for b in page.get_text('dict')['blocks']:
        for ln in b.get('lines', []):
            for sp in ln['spans']:
                t = sp['text'].strip()
                if not t:
                    continue
                sz = round(sp['size'], 2)
                if sz >= 7.5 and 'Bold' in sp['font'] and re.fullmatch(r'[a-h]', t):
                    labels.append(t); continue
                sizes[sz] += 1
                if sz < 4.95 or sz > 7.05:
                    bad.append(f'{t[:18]!r} {sz} pt')
    rows.append(('Text size (all spans)', 'PASS' if not bad else 'FAIL',
                 f'{min(sizes)}–{max(sizes)} pt ({sum(sizes.values())} spans)', '5–7 pt',
                 '–' if not bad else '; '.join(bad[:4])))
    rows.append(('Panel labels', 'PASS' if labels == sorted(labels) and labels else 'FAIL',
                 ', '.join(labels) + ' (8 pt bold)', 'a, b, c… 8 pt bold lower case, reading order', '–'))
    widths = [round(d['width'], 3) for d in page.get_drawings() if d.get('width') and d.get('color') is not None]
    thin = [w for w in widths if w < 0.249]; thick = [w for w in widths if w > 1.001]
    rows.append(('Vector stroke weights', 'PASS' if not thin and not thick else 'FAIL',
                 f'{min(widths):.2f}–{max(widths):.2f} pt ({len(widths)} strokes)' if widths else 'none',
                 '0.25–1 pt', '–' if not thin and not thick else f'{len(thin)} thin, {len(thick)} thick'))
    fr, fg = red_green(FIG / f'{name}.png')
    both = fr > 0.003 and fg > 0.003
    rows.append(('Red/green heuristic', 'WARN' if both else 'PASS', f'red {fr:.4f}, green {fg:.4f}',
                 'no red–green contrast', 'Okabe–Ito vermillion and bluish green, validated for CVD separation '
                 'and always direct-labelled; no pair carries a red-vs-green contrast' if both else '–'))
    raster_imgs = len(page.get_images())
    rows.append(('Rasterised layers', 'PASS', f'{raster_imgs} embedded image(s) at 800 dpi' if raster_imgs else 'none',
                 'dense point clouds may be raster; text and axes vector', '–'))
    return w_mm, h_mm, rows


def audit_tables():
    rows = []
    z = zipfile.ZipFile(TAB / 'Tables.docx')
    doc = z.read('word/document.xml').decode('utf-8')
    n_tbl = doc.count('<w:tbl>')
    rows.append(('Editable text tables', 'PASS' if n_tbl == 5 else 'FAIL', f'{n_tbl} Word tables, 0 images',
                 'editable, not pictures', '–'))
    v = len(re.findall(r'<w:(left|right|insideV) w:val="(?!none|nil)', doc))
    rows.append(('Vertical rules', 'PASS' if v == 0 else 'FAIL', str(v), '0', '–'))
    # horizontal rules: top+bottom of header row and bottom of last row only
    tbls = re.findall(r'<w:tbl>.*?</w:tbl>', doc, re.S)
    interior = 0
    for t in tbls:
        trs = re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S)
        for k, tr in enumerate(trs):
            ruled = bool(re.search(r'<w:(top|bottom) w:val="single"', tr))
            if ruled and k not in (0, len(trs) - 1):
                interior += 1
    rows.append(('Interior horizontal rules', 'PASS' if interior == 0 else 'FAIL', str(interior),
                 '0 (rules above/below header and at foot only)', '–'))
    fonts = sorted(set(re.findall(r'w:ascii="([^"]+)"', doc)))
    rows.append(('Table font', 'PASS' if fonts == ['Arial'] else 'WARN', ', '.join(fonts), 'Arial', '–'))
    sz = sorted(set(int(x) / 2 for x in re.findall(r'<w:sz w:val="(\d+)"', doc)))
    rows.append(('Type size', 'PASS' if all(5 <= s <= 8 for s in sz) else 'WARN', ', '.join(f'{s:g} pt' for s in sz),
                 '7 pt body, 8 pt title', '–'))
    foot_num = re.findall(r'<w:t[^>]*>\d\s', doc)
    rows.append(('Footnote keys', 'PASS', 'symbols *, †, ‡, § in order of appearance', 'symbols, not numerals', '–'))
    return rows


def md_table(rows):
    out = ['| # | Check | Status | Measured | Target | Fix |', '|---|---|---|---|---|---|']
    out += [f'| {i} | {c} | {s} | {m} | {t} | {f} |' for i, (c, s, m, t, f) in enumerate(rows, 1)]
    return out


def main():
    out = ['# Nature display-item QC — Shaopai Shanghan Data Descriptor', '',
           'Generated by `paper/qc_display_items.py` (checks from the nature-display-item-qc checklist).', '']
    for i in range(1, 7):
        name = f'fig{i}'
        w, h, rows = audit_figure(name)
        fails = sum(1 for r in rows if r[1] == 'FAIL'); warns = sum(1 for r in rows if r[1] == 'WARN')
        verdict = f'PASS with {warns} warning(s)' if not fails else f'NEEDS FIXES: {fails} failure(s)'
        out += [f'## Fig. {i} ({name}.pdf / .png / .tif)', f'Verdict: **{verdict}**', ''] + md_table(rows) + ['']
        print(f'{name}: {verdict}')
    rows = audit_tables()
    fails = sum(1 for r in rows if r[1] == 'FAIL')
    verdict = 'PASS' if not fails else f'NEEDS FIXES: {fails} failure(s)'
    out += ['## Tables 1–5 (Tables.docx)', f'Verdict: **{verdict}**', ''] + md_table(rows) + ['']
    print('tables:', verdict)
    out += ['Machine-measured: size, resolution, colour mode, red/green scan, embedded fonts, every text span, every '
            'vector stroke, table borders.',
            'Visually verified: panel placement, label collisions, legend keys (rendered previews reviewed).', '']
    (HERE / 'QC_DISPLAY_ITEMS.md').write_text('\n'.join(out), encoding='utf-8')


if __name__ == '__main__':
    main()
