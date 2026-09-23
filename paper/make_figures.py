#!/usr/bin/env python3
"""
Figures for the Scientific Data Data Descriptor on the Shaopai Shanghan (绍派伤寒) knowledge graph and corpus.

  python3 paper/make_figures.py          # → paper/figures/fig1–fig6 .pdf / .png / .tif (800 dpi)

Figure logic follows the Data Descriptor genre (documenting a resource, not testing a hypothesis):
  Fig. 1 construction and provenance · Fig. 2 corpus composition · Fig. 3 schema and composition of the graph
  Fig. 4 topology · Fig. 5 coverage across sources, layers and time · Fig. 6 technical validation
Every number is computed from data/ via dataset.py.
"""
import math, textwrap, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, PathPatch
from matplotlib.path import Path as MPath
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, NullFormatter, FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nature_style as ns  # noqa: E402
from nature_style import Canvas, BLUE, VERMILLION, GREY, DARK, LIGHT, INK, BLACK  # noqa: E402
import dataset  # noqa: E402

OUT = Path(__file__).resolve().parent / 'figures'
LAYER_COL = {'lineage': ns.VERMILLION, 'diagnostic': ns.SKY, 'pattern': ns.GREEN,
             'materia': ns.ORANGE, 'case': ns.BLUE, 'culture': ns.PURPLE}
L_EN = dataset.LAYER_EN
TINT = '#D9EAF5'            # flat tint of Okabe–Ito blue, for highlights only
GLOSS = {'痰壅气喘': 'phlegm obstruction, dyspnoea', '喉中漉漉有声': 'gurgling in the throat',
         '苔滑': 'slippery tongue coating', '脉沉': 'deep pulse', '消痰定喘': 'resolve phlegm, calm dyspnoea',
         '九制胆星': 'processed bile arisaema', '京川贝': 'Sichuan fritillary bulb', '真猴枣': 'monkey bezoar',
         '莱菔汁': 'radish juice'}
fmt = lambda v: f'{v:,}'
pct = lambda a, b: f'{100 * a / b:.1f}%'


def clean(ax, left=True, bottom=True):
    ax.spines['left'].set_visible(left); ax.spines['bottom'].set_visible(bottom)
    if not left:
        ax.tick_params(left=False)
    if not bottom:
        ax.tick_params(bottom=False)


def work_label(w, zh=True):
    dag = '†' if w['script'] == 'Traditional' else ''
    return f"{w['short']}{dag}\n{w['zh']}" if zh else f"{w['short']}{dag}"


# ============================================================ Fig. 1 construction and provenance
def fig1(S):
    c = Canvas(ns.DOUBLE, 98)
    ax = c.ax(0, 0, c.w, c.h); ax.set_xlim(0, c.w); ax.set_ylim(c.h, 0); ax.axis('off')
    T = S['corpus_totals']; im = S['identity_merge']; ex = S['example']
    n_cls = sum(1 for x in S['classes'] if x['n']); n_prop = sum(1 for p in S['properties'] if p['n'])
    resolvable = sum(v for (w, k), v in S['evidence_by_work'].items() if k != 'unresolved')
    found = sum(v for (w, k), v in S['evidence_by_work'].items() if k == 'found')
    stages = [
        ('Source texts', [f"{len(S['works'])} published works", f"{fmt(T['passages'])} passages",
                          f"{fmt(T['chars'])} characters", 'Simplified and traditional', 'Chinese script']),
        ('Segmentation', ['Chapter-path segmentation', 'Stable passage identifiers',
                          'Passages routed to', f"{len(dataset.LAYERS)} knowledge layers"]),
        ('Extraction', [f"Ontology-guided (v{S['ontology_version']})",
                        f"{len(S['onto']['classes'])} classes, {len(S['onto']['object_properties'])} relation types",
                        'Evidence sentence and', 'passage ID per relation']),
        ('Entity resolution', ['Traditional/simplified', f"variants ({im.get('script_variant_groups', 0)} groups)",
                               f"Name variants ({im.get('name_variant_pairs', 0)} pairs)",
                               f"{im.get('nodes_merged', 0)} entities merged"]),
        ('Validation', [f"Schema violations: {S['domain_range_violations']}",
                                  'Evidence found in cited', f"passage ({pct(found, resolvable)})",
                                  f"Cardinality exceptions: {sum(S['cardinality_exceptions'].values())}",
                                  'Privacy screening']),
        ('Release', [f"{fmt(S['n_nodes'])} entities ({n_cls} classes)",
                     f"{fmt(S['n_edges'])} relations ({n_prop} types)", 'JSON, CSV (Neo4j),', 'RDF/OWL, web explorer']),
    ]
    c.label(0, 0.5, 'a')
    x0, bw, gap, y0, bh = 1.2, 27.6, 3.04, 5.0, 27.0
    for i, (title, lines) in enumerate(stages):
        x = x0 + i * (bw + gap)
        ax.add_patch(FancyBboxPatch((x, y0), bw, bh, boxstyle='round,pad=0,rounding_size=1.4',
                                    fc='white', ec=BLUE, lw=0.75))
        ax.add_patch(Rectangle((x + 0.35, y0 + 0.35), bw - 0.7, 6.0, fc=TINT, ec='none'))
        ax.text(x + 1.6, y0 + 3.4, f'{i + 1}', fontsize=6.5, fontweight='bold', va='center')
        ax.text(x + 4.2, y0 + 3.4, title, fontsize=6, fontweight='bold', va='center')
        for j, t in enumerate(lines):
            ax.text(x + 1.6, y0 + 9.6 + j * 3.4, t, fontsize=5.5, va='center')
        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((x + bw + 0.25, y0 + bh / 2), (x + bw + gap - 0.25, y0 + bh / 2),
                                         arrowstyle='-|>', mutation_scale=5, lw=0.75, color=BLUE))
    m = S['modern']
    ax.add_patch(FancyBboxPatch((x0, y0 + bh + 2.6), 2 * bw + gap, 7.0, boxstyle='round,pad=0,rounding_size=1.0',
                                fc='white', ec=GREY, lw=0.5, ls=(0, (3, 2))))
    ax.text(x0 + 1.6, y0 + bh + 4.6, f"Modern outpatient records ({m['passages']} passages, "
            f"{fmt(m['edges'])} relations)", fontsize=5.5, va='center')
    ax.text(x0 + 1.6, y0 + bh + 7.8, 'withheld from release pending consent review', fontsize=5.5,
            va='center', style='italic')

    # ---- b: one passage, the relations extracted from it, and one relation record
    c.label(0, 44.5, 'b')
    ex = S['example']; p, rels, feat = ex['passage'], ex['edges'], ex['featured']
    order = ['caseDiagnosedAs', 'caseShowsSymptom', 'caseShowsSign', 'caseAppliesPrinciple', 'caseUsesHerb']
    rels = sorted(rels, key=lambda r: (order.index(r['type']) if r['type'] in order else 9, p['text'].find(r['source_sentence'])))
    top, ph = 49.0, 46.5
    # passage card
    px, pw = 1.2, 55.0
    ax.add_patch(FancyBboxPatch((px, top), pw, ph, boxstyle='round,pad=0,rounding_size=1.2',
                                fc='white', ec=DARK, lw=0.5))
    ax.text(px + 1.8, top + 3.2, f"Passage {p['pid']}", fontsize=6, fontweight='bold', va='center')
    ax.text(px + 1.8, top + 7.0, 'Source work: 何廉臣医案 (He Lianchen case records)', fontsize=5.5, va='center')
    ax.text(px + 1.8, top + 10.4, f"Chapter path: {p['section']} › {p.get('subsection') or ''}",
            fontsize=5.5, va='center')
    yend = _highlighted_passage(ax, px + 1.8, top + 15.4, pw - 3.6, p['text'], [r['source_sentence'] for r in rels])
    ax.text(px + 1.8, yend + 4.4, f'Tinted: evidence spans of the {len(rels)} relations', fontsize=5.5,
            va='center', style='italic')
    ax.text(px + 1.8, yend + 7.8, 'extracted from this passage', fontsize=5.5, va='center', style='italic')
    # subject and its relations
    ys = [top + 3.4 + i * 4.95 for i in range(len(rels))]
    ymid = (ys[0] + ys[-1]) / 2
    sx, sw, sh = 62.0, 14.0, 13.0
    ax.add_patch(FancyBboxPatch((sx, ymid - sh / 2), sw, sh, boxstyle='round,pad=0,rounding_size=1.2',
                                fc='white', ec=BLUE, lw=0.75))
    subj = rels[0]['subject_name'].split(' ', 1)
    ax.text(sx + sw / 2, ymid - 3.4, subj[0].replace('案', 'Case '), fontsize=5.5, ha='center', va='center')
    ax.text(sx + sw / 2, ymid, subj[1] if len(subj) > 1 else '', fontsize=6, ha='center', va='center',
            fontweight='bold')
    ax.text(sx + sw / 2, ymid + 3.4, '(Case record)', fontsize=5.5, ha='center', va='center', style='italic')
    ax.add_patch(FancyArrowPatch((px + pw + 0.4, ymid), (sx - 0.5, ymid), arrowstyle='-|>', mutation_scale=5,
                                 lw=0.75, color=BLUE))
    trunk = sx + sw + 2.6
    ax.plot([sx + sw, trunk], [ymid, ymid], color=BLUE, lw=0.75, solid_capstyle='butt')
    ax.plot([trunk, trunk], [ys[0], ys[-1]], color=BLUE, lw=0.75, solid_capstyle='butt')
    leaf = 100.0
    for r, yy in zip(rels, ys):
        ax.add_patch(FancyArrowPatch((trunk, yy), (leaf - 0.2, yy), arrowstyle='-|>', mutation_scale=4,
                                     lw=0.75, color=BLUE, shrinkA=0, shrinkB=0))
        ax.text((trunk + leaf) / 2, yy - 0.55, r['type'], fontsize=5, ha='center', va='bottom')
        if r is feat:
            ax.add_patch(Rectangle((leaf + 0.6, yy - 2.25), 26.6, 4.5, fc=TINT, ec='none', zorder=0.5))
        ax.text(leaf + 1.4, yy - 0.95, r['object_name'], fontsize=5.5, va='center')
        ax.text(leaf + 1.4, yy + 1.1, GLOSS.get(r['object_name'], ''), fontsize=5, va='center')
    # the featured relation record
    rx, rw = 130.0, 52.0
    ax.add_patch(FancyBboxPatch((rx, top), rw, ph, boxstyle='round,pad=0,rounding_size=1.2',
                                fc='white', ec=DARK, lw=0.5))
    fy = ys[rels.index(feat)]
    ax.add_patch(FancyArrowPatch((leaf + 27.4, fy), (rx - 0.5, fy), arrowstyle='-|>', mutation_scale=5,
                                 lw=0.75, color=BLUE))
    ax.text(rx + 1.8, top + 3.2, 'Relation record', fontsize=6, fontweight='bold', va='center')
    fields = [('type', feat['type']), ('subject', feat['subject_name']), ('object', feat['object_name']),
              ('source_sentence', feat['source_sentence']), ('passage_id', feat['passage_id']),
              ('chapter_path', feat['chapter_path'].replace(' / ', ' › ')), ('corpus', feat['corpus']),
              ('layer', feat['layer']), ('n_support', str(feat['n_support'])),
              ('evidence_verbatim', f"{str(feat['evidence_verbatim']).lower()} (upstream flag)"),
              ('evidence_in_passage', f"{str(feat['evidence_in_passage']).lower()} (independent check)")]
    for j, (k, v) in enumerate(fields):
        yy = top + 7.6 + j * 3.6
        ax.text(rx + 1.8, yy, k, fontsize=5.5, va='center', fontweight='bold')
        ax.text(rx + 22.6, yy, v, fontsize=5.5, va='center')
    return ns.save(c, 'fig1', OUT)


def _highlighted_passage(ax, x, y, width, text, spans, fs=5.5, lh=3.7):
    """Lay out a CJK passage (keeping its own line breaks) and tint the evidence spans behind the glyphs.
    Returns the y of the last line."""
    from matplotlib.textpath import text_to_path
    from matplotlib.font_manager import FontProperties
    prop = FontProperties(family=plt.rcParams['font.family'], size=fs)

    def w_mm(s):      # unhinted advance widths: identical at every output resolution
        return text_to_path.get_text_width_height_descent(s, prop, ismath=False)[0] * 25.4 / 72
    tint = [False] * len(text)
    for sp in spans:
        i = text.find(sp)
        if i >= 0:
            for k in range(i, i + len(sp)):
                tint[k] = True
    no_start = set('，。、；：！？）」』》')     # CJK line-breaking rule: these never begin a line
    lines, cur, start = [], '', 0            # (line text, offset of its first character)
    for i, ch in enumerate(text):
        if ch == '\n':
            lines.append((cur, start)); cur, start = '', i + 1
        elif cur and w_mm(cur + ch) > width and ch not in no_start:
            lines.append((cur, start)); cur, start = ch, i
        else:
            cur += ch
    lines.append((cur, start))
    for li, (line, off) in enumerate(lines):
        yy = y + li * lh
        k = 0
        while k < len(line):
            if tint[off + k]:
                j = k
                while j < len(line) and tint[off + j]:
                    j += 1
                xa, xb = x + w_mm(line[:k]), x + w_mm(line[:j])
                ax.add_patch(Rectangle((xa, yy - lh / 2 + 0.3), xb - xa, lh - 0.6, fc=TINT, ec='none', zorder=3))
                k = j
            else:
                k += 1
        ax.text(x, yy, line, fontsize=fs, va='center', zorder=4)
    return y + (len(lines) - 1) * lh


# ============================================================ Fig. 2 corpus composition
def fig2(S):
    W = S['works']
    c = Canvas(ns.DOUBLE, 74)
    y = np.arange(len(W))[::-1]
    top, h = 7.0, 60.0
    axa = c.ax(44, top, 40, h); axb = c.ax(92, top, 30, h); axc = c.ax(129, top, 52, h)
    for ax in (axa, axb, axc):
        ax.set_ylim(-0.6, len(W) - 0.4)
    # a characters
    vals = [w['chars'] / 1000 for w in W]
    axa.barh(y, vals, height=0.62, color=DARK, lw=0)
    for yi, v in zip(y, vals):
        axa.text(v + 3, yi, f'{v:,.1f}', fontsize=5, va='center')
    axa.set_xlim(0, 260); axa.set_xlabel('Characters (thousands)')
    axa.set_yticks(y); axa.set_yticklabels([work_label(w) for w in W], fontsize=5.5, linespacing=1.15)
    axa.tick_params(axis='y', length=0)
    # b passages
    vals = [w['passages'] for w in W]
    axb.barh(y, vals, height=0.62, color=DARK, lw=0)
    for yi, v in zip(y, vals):
        axb.text(v + 25, yi, fmt(v), fontsize=5, va='center')
    axb.set_xlim(0, 2000); axb.set_xticks([0, 500, 1000, 1500, 2000]); axb.set_xlabel('Passages')
    axb.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    axb.set_yticks([]); clean(axb, left=False)
    # c passage length
    rng = np.random.default_rng(7)
    for yi, w in zip(y, W):
        L = np.array(w['lengths'], dtype=float); L = L[L > 0]
        jit = rng.uniform(-0.22, 0.22, len(L))
        axc.scatter(L, yi + jit, s=0.35, c='#9A9A9A', lw=0, alpha=0.55, rasterized=True, zorder=1)
        q1, med, q3 = np.percentile(L, [25, 50, 75])
        axc.add_patch(Rectangle((q1, yi - 0.3), q3 - q1, 0.6, fc='none', ec=BLACK, lw=0.6, zorder=3))
        axc.plot([med, med], [yi - 0.3, yi + 0.3], color=BLACK, lw=1.0, solid_capstyle='butt', zorder=4)
        lo, hi = np.percentile(L, [5, 95])
        axc.plot([lo, q1], [yi, yi], color=BLACK, lw=0.6, zorder=3)
        axc.plot([q3, hi], [yi, yi], color=BLACK, lw=0.6, zorder=3)
    axc.set_xscale('log'); axc.set_xlim(1, 5000)
    axc.xaxis.set_major_locator(LogLocator(base=10, numticks=6))
    axc.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    axc.set_xlabel('Passage length (characters)')
    axc.set_yticks([]); clean(axc, left=False)
    c.label(0, 0.5, 'a'); c.label(88, 0.5, 'b'); c.label(125, 0.5, 'c')
    return ns.save(c, 'fig2', OUT)


# ============================================================ Fig. 3 schema and composition
# Node slots chosen by minimising weighted edge crossings and edge–node overlaps (simulated annealing over a
# 4 × 3 grid, lineage/culture block fixed on the left); see paper/README.md.
NODE_XY = {
    'Place': (0.55, 5.0), 'Institution': (0.55, 3.2), 'MedicalFamily': (0.55, 1.35),
    'Physician': (1.95, 3.2), 'Doctrine': (3.55, 4.95), 'Work': (3.55, 1.45),
    'HerbProperty': (5.3, 5.05), 'Herb': (7.3, 5.05), 'CaseRecord': (9.3, 5.05),
    'TreatmentPrinciple': (5.3, 3.2), 'Formula': (7.3, 3.2), 'Disease': (9.3, 3.2), 'Symptom': (11.3, 3.2),
    'Pattern': (11.3, 1.35), 'DiagnosticSign': (12.42, 4.8),
}
EDGE_RAD = {  # arc3 curvature where a straight line would clip a node or share a path
    ('Physician', 'Work', 'authored'): 0.14, ('Physician', 'Work', 'editedRevised'): -0.14,
    ('DiagnosticSign', 'Pattern', 'signIndicates'): 0.16, ('DiagnosticSign', 'Pattern', 'signExcludes'): -0.16,
    ('MedicalFamily', 'Disease', 'familySpecializesIn'): 0.1, ('Formula', 'Work', 'derivesFrom'): 0.12,
    ('Pattern', 'TreatmentPrinciple', 'treatedByPrinciple'): -0.06, ('Formula', 'Pattern', 'formulaTreats'): 0.1,
    ('CaseRecord', 'Pattern', 'caseShowsPattern'): -0.1, ('Disease', 'Symptom', 'diseaseManifestsAs'): 0.25,
    ('CaseRecord', 'TreatmentPrinciple', 'caseAppliesPrinciple'): 0.08,
    ('Formula', 'Disease', 'diseaseTreatedByFormula'): 0.3,
}
EDGE_RAD[('Disease', 'Symptom', 'diseaseManifestsAs')] = 0.38
LOOP_ANG = {'influencedBy': 90, 'studiedUnder': 270, 'subPatternOf': 305, 'belongsToChannel': 235}
R_MAX = 0.42


def _quad(p0, c, p1, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1])


class _Labels:
    """Greedy placement of edge labels: sample points along each label, avoid nodes and earlier labels."""
    def __init__(self, nodes, rad, unit_mm):
        self.nodes, self.rad, self.pts, self.paths = nodes, rad, [], []
        self.cw = 0.92 / unit_mm           # 5 pt Arial: ~0.92 mm per character
        self.h = 1.9 / unit_mm

    def _samples(self, x, y, ang, n):
        L = n * self.cw; ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        out = []
        for f in np.linspace(-0.5, 0.5, max(6, 2 * n)):
            for g in (-0.5, 0.0, 0.5):
                out.append((x + f * L * ca - g * self.h * sa, y + f * L * sa + g * self.h * ca))
        return out

    def add_path(self, key, pts):
        self.paths.append((key, pts))

    def score(self, x, y, ang, n, own=None):
        sc = 0.0
        smp = self._samples(x, y, ang, n)
        for key, pts in self.paths:
            if key == own:
                continue
            for (px, py) in smp[::3]:
                if any(abs(px - qx) < self.cw * 0.8 and abs(py - qy) < self.h * 0.6 for qx, qy in pts):
                    sc += 1.0
        for (px, py) in smp:
            for k, (nx, ny) in self.nodes.items():
                if math.hypot(px - nx, py - ny) < self.rad[k] + 0.04:
                    sc += 3
            for (qx, qy) in self.pts:
                if abs(px - qx) < self.cw * 0.9 and abs(py - qy) < self.h * 0.9:
                    sc += 2
        return sc

    def add(self, x, y, ang, n):
        self.pts += self._samples(x, y, ang, n)


def fig3(S):
    c = Canvas(ns.DOUBLE, 168)
    counts = {x['cls']: x['n'] for x in S['classes'] if x['n']}
    props = [p for p in S['properties'] if p['n']]
    # ---- a schema
    c.label(0, 0.5, 'a')
    aw, ah = 181.0, 88.0
    ax = c.ax(1, 3, aw, ah); ax.axis('off')
    ux = 12.9; uy = ux * ah / aw
    ax.set_xlim(0, ux); ax.set_ylim(0, uy); ax.set_aspect('equal')
    unit_mm = aw / ux; pt_per_unit = unit_mm * 72 / 25.4
    vmax = max(counts.values())
    rad = {k: R_MAX * math.sqrt(v / vmax) for k, v in counts.items()}
    nmax = max(p['n'] for p in props)
    lw_of = lambda n: 0.3 + 0.7 * math.sqrt(n / nmax)      # 0.3–1.0 pt: Nature's stroke range
    lab = _Labels(NODE_XY, rad, unit_mm)
    for p in props:                              # every edge path, so labels avoid sitting across other edges
        a, b = p['domain'], p['range']
        if a == b:
            continue
        r_ = EDGE_RAD.get((a, b, p['prop']), 0.0)
        (x1, y1), (x2, y2) = NODE_XY[a], NODE_XY[b]
        cc = ((x1 + x2) / 2 + r_ * (y2 - y1), (y1 + y2) / 2 - r_ * (x2 - x1))
        lab.add_path(p['prop'], [_quad((x1, y1), cc, (x2, y2), t) for t in np.linspace(0.05, 0.95, 60)])
    for k, (x, y) in NODE_XY.items():          # reserve the small-node labels drawn later
        if rad[k] < 0.28:
            n_ = len(dataset.CLASS_EN[k])
            if k == 'Physician':
                lab.add(x + rad[k] + 0.08 + n_ * lab.cw / 2, y, 0, n_)
            elif k in ('Institution', 'MedicalFamily', 'HerbProperty', 'Work'):
                lab.add(x, y - rad[k] - 0.2, 0, n_)
            else:
                lab.add(x, y + rad[k] + 0.2, 0, n_)
    for p in sorted(props, key=lambda p: -p['n']):
        a, b = p['domain'], p['range']
        col = LAYER_COL[p['layer']]
        if a == b:
            _self_loop(ax, NODE_XY[a], rad[a], p, col, lw_of(p['n']), lab)
            continue
        r_ = EDGE_RAD.get((a, b, p['prop']), 0.0)
        (x1, y1), (x2, y2) = NODE_XY[a], NODE_XY[b]
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), connectionstyle=f'arc3,rad={r_}', arrowstyle='-|>',
                                     mutation_scale=3.5 + 2.5 * lw_of(p['n']), lw=lw_of(p['n']), color=col,
                                     shrinkA=rad[a] * pt_per_unit + 1.2, shrinkB=rad[b] * pt_per_unit + 1.5,
                                     zorder=2))
        dx, dy = x2 - x1, y2 - y1
        cc = ((x1 + x2) / 2 + r_ * dy, (y1 + y2) / 2 - r_ * dx)
        best = None
        for t in (0.5, 0.42, 0.58, 0.34, 0.66, 0.27, 0.73):
            ex_, ey_ = _quad((x1, y1), cc, (x2, y2), t)
            tx_, ty_ = (_quad((x1, y1), cc, (x2, y2), t + 0.01)[0] - ex_, _quad((x1, y1), cc, (x2, y2), t + 0.01)[1] - ey_)
            ang = math.degrees(math.atan2(ty_, tx_))
            ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
            nx_, ny_ = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
            for off in (0.0, 0.11, -0.11):          # on the line, or just beside it
                lx, ly = ex_ + off * nx_, ey_ + off * ny_
                sc = lab.score(lx, ly, ang, len(p['prop']), own=p['prop']) + abs(t - 0.5) + 0.6 * abs(off) / 0.11
                if best is None or sc < best[0]:
                    best = (sc, lx, ly, ang)
        _, lx, ly, ang = best
        lab.add(lx, ly, ang, len(p['prop']))
        ax.text(lx, ly, p['prop'], fontsize=5, ha='center', va='center', rotation=ang, rotation_mode='anchor',
                zorder=4, bbox=dict(boxstyle='square,pad=0.06', fc='white', ec='none'))
    below = {'Institution', 'MedicalFamily', 'HerbProperty', 'Work'}
    right = {'Physician'}
    for k, (x, y) in NODE_XY.items():
        r = rad[k]
        ax.add_patch(plt.Circle((x, y), r, fc='white', ec=BLACK, lw=0.6, zorder=5))
        name = dataset.CLASS_EN[k]
        if r >= 0.28:
            ax.text(x, y + 0.05, name.replace(' ', '\n') if len(name) > 12 else name, fontsize=5.5,
                    ha='center', va='bottom', zorder=6, linespacing=1.0)
            ax.text(x, y - 0.04, fmt(counts[k]), fontsize=5, ha='center', va='top', zorder=6)
        elif k in right:
            ax.text(x + r + 0.08, y, f'{name}\n{fmt(counts[k])}', fontsize=5, ha='left', va='center', zorder=6,
                    linespacing=1.0, bbox=dict(boxstyle='square,pad=0.05', fc='white', ec='none'))
        elif k in below:
            ax.text(x, y - r - 0.06, f'{name}\n{fmt(counts[k])}', fontsize=5, ha='center', va='top', zorder=6,
                    linespacing=1.0, bbox=dict(boxstyle='square,pad=0.05', fc='white', ec='none'))
        else:
            ax.text(x, y + r + 0.06, f'{name}\n{fmt(counts[k])}', fontsize=5, ha='center', va='bottom', zorder=6,
                    linespacing=1.0, bbox=dict(boxstyle='square,pad=0.05', fc='white', ec='none'))
    # layer key
    for i, l in enumerate(dataset.LAYERS):
        xx = 0.2 + i * 1.55
        ax.plot([xx, xx + 0.35], [uy - 0.12, uy - 0.12], color=LAYER_COL[l], lw=1.0, solid_capstyle='butt')
        ax.text(xx + 0.45, uy - 0.12, L_EN[l], fontsize=5.5, va='center')
    ax.text(ux - 0.05, uy - 0.12, 'Circle area ∝ entities; line width scales with √relations', fontsize=5.5,
            ha='right', va='center', style='italic')

    # ---- b entities per class
    c.label(0, 94.5, 'b')
    cl = sorted([x for x in S['classes'] if x['n']], key=lambda x: x['n'])
    axb = c.ax(27, 98, 56, 64)
    yy = np.arange(len(cl))
    axb.barh(yy, [x['connected'] for x in cl], height=0.64, color=DARK, lw=0, label='With relations')
    axb.barh(yy, [x['isolated'] for x in cl], left=[x['connected'] for x in cl], height=0.64, color=LIGHT,
             lw=0, label='Without relations')
    for yi, x in zip(yy, cl):
        axb.text(x['n'] + 40, yi, fmt(x['n']), fontsize=5, va='center')
    axb.set_yticks(yy); axb.set_yticklabels([x['en'] for x in cl]); axb.tick_params(axis='y', length=0)
    axb.set_ylim(-0.6, len(cl) - 0.4); axb.set_xlim(0, 3100); axb.set_xlabel('Entities')
    axb.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    axb.legend(loc='lower right', bbox_to_anchor=(1.0, 0.02), handlelength=0.9)

    # ---- c relations per type
    c.label(90, 94.5, 'c')
    rows, ypos, yv = [], [], 0.0
    for l in dataset.LAYERS:
        ps = sorted([p for p in props if p['layer'] == l], key=lambda p: -p['n'])
        for p in ps:
            rows.append(p); ypos.append(yv); yv += 1
        yv += 0.7
    ypos = np.array(ypos)
    axc = c.ax(128, 97, 53, 64)
    for p, yi in zip(rows, ypos):
        axc.plot([1, p['n']], [yi, yi], color='#BDBDBD', lw=0.5, zorder=1)
        axc.scatter([p['n']], [yi], s=7, color=LAYER_COL[p['layer']], lw=0, zorder=3)
        axc.text(p['n'] * 1.35, yi, fmt(p['n']), fontsize=5, va='center')
    axc.set_xscale('log'); axc.set_xlim(1, 60000)
    axc.xaxis.set_major_locator(LogLocator(base=10, numticks=6))
    axc.xaxis.set_minor_formatter(NullFormatter())
    axc.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    axc.set_yticks(ypos); axc.set_yticklabels([p['prop'] for p in rows], fontsize=5)
    axc.tick_params(axis='y', length=0)
    axc.set_ylim(ypos[-1] + 0.8, -0.8); axc.set_xlabel('Relations (log scale)')
    return ns.save(c, 'fig3', OUT)


def _self_loop(ax, xy, r, p, col, lw, lab):
    x, y = xy
    ang = LOOP_ANG[p['prop']]
    a0, a1 = math.radians(ang - 24), math.radians(ang + 24)
    s = (x + r * math.cos(a0), y + r * math.sin(a0)); e = (x + r * math.cos(a1), y + r * math.sin(a1))
    k = r + 0.5
    c1 = (x + k * math.cos(a0 - 0.12), y + k * math.sin(a0 - 0.12))
    c2 = (x + k * math.cos(a1 + 0.12), y + k * math.sin(a1 + 0.12))
    ax.add_patch(FancyArrowPatch(path=MPath([s, c1, c2, e], [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4]),
                                 arrowstyle='-|>', mutation_scale=3.5 + 2.5 * lw, lw=lw, color=col, zorder=2))
    apex = ((s[0] + 3 * c1[0] + 3 * c2[0] + e[0]) / 8, (s[1] + 3 * c1[1] + 3 * c2[1] + e[1]) / 8)
    mid = math.radians(ang)
    lx, ly = apex[0] + 0.06 * math.cos(mid), apex[1] + 0.06 * math.sin(mid)
    ha = 'right' if math.cos(mid) < -0.3 else 'left' if math.cos(mid) > 0.3 else 'center'
    va = 'bottom' if math.sin(mid) > 0.3 else 'top' if math.sin(mid) < -0.3 else 'center'
    ax.text(lx, ly, p['prop'], fontsize=5, ha=ha, va=va, zorder=4)
    lab.add(lx, ly, 0, len(p['prop']))


# ============================================================ Fig. 4 topology
HUBS = [  # (name, class, label, label position in layout coordinates)
    ('俞根初', 'Physician', 'Yu Genchu 俞根初', (-0.72, -0.22)),
    ('何廉臣', 'Physician', 'He Lianchen 何廉臣', (-0.40, -0.86)),
    ('滑石', 'Herb', 'Huashi 滑石', (0.66, 0.27)),
    ('竹茹', 'Herb', 'Zhuru 竹茹', (0.66, -0.12)),
]


def fig4(S):
    c = Canvas(ns.DOUBLE, 122)
    N, pos, deg = S['N'], S['pos'], S['deg']
    # ---- a map
    c.label(0, 0.5, 'a')
    ax = c.ax(6, 3, 108, 108); ax.axis('off'); ax.set_aspect('equal')
    lim = 1.53; ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    order = sorted(dataset.LAYERS, key=lambda l: -S['layer_n'][l])
    for l in order:
        segs = [(pos[e['subject_id']], pos[e['object_id']]) for e in S['edges'] if e['layer'] == l]
        ax.add_collection(LineCollection(segs, colors=LAYER_COL[l], linewidths=0.25,
                                         alpha=0.28 if l == 'case' else 0.5, rasterized=True, zorder=1))
    con = [n for n in S['nodes'] if deg[n['id']]]
    iso = [n for n in S['nodes'] if not deg[n['id']]]
    ax.scatter([pos[n['id']][0] for n in iso], [pos[n['id']][1] for n in iso], s=0.25, c='#B5B5B5', lw=0,
               rasterized=True, zorder=2)
    size = lambda d: (0.55 + 0.2 * math.sqrt(d)) ** 2
    ax.scatter([pos[n['id']][0] for n in con], [pos[n['id']][1] for n in con],
               s=[size(deg[n['id']]) for n in con], c='#262626', lw=0, alpha=0.85, rasterized=True, zorder=3)
    for name, cls, text, (lx, ly) in HUBS:
        n = max((n for n in con if n['name'] == name and n['cls'] == cls), key=lambda n: deg[n['id']])
        x, y = pos[n['id']]
        ax.annotate(text, (x, y), (lx, ly), fontsize=5.5, ha='center', va='center',
                    arrowprops=dict(arrowstyle='-', lw=0.4, color=BLACK, shrinkA=1.0, shrinkB=1.2), zorder=6,
                    bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))
    # key below the map
    for i, l in enumerate(dataset.LAYERS):
        x0 = 8 + (i % 3) * 36; y0 = 113.5 + (i // 3) * 3.6
        c.fig.add_artist(Line2D([x0 / c.w, (x0 + 4) / c.w], [1 - y0 / c.h] * 2, color=LAYER_COL[l], lw=1.0,
                                solid_capstyle='butt'))
        c.text(x0 + 5, y0, f"{L_EN[l]} ({fmt(S['layer_n'][l])} relations)", fontsize=5.5, va='center')
    c.text(8, 120.4, 'Dots: entities (area increases with degree); light grey: entities without relations. '
           'Huashi, talc; Zhuru, bamboo shavings.', fontsize=5.5, va='center')

    # ---- b degree distribution
    c.label(122, 0.5, 'b')
    d = np.array(sorted(deg[n['id']] for n in con))
    ks = np.unique(d); ccdf = np.array([(d >= k).mean() for k in ks])
    axb = c.ax(135, 5, 46, 46)
    axb.plot(ks, ccdf, color=BLACK, lw=0.9, drawstyle='steps-post')
    axb.set_xscale('log'); axb.set_yscale('log')
    axb.set_xlabel('Degree, k'); axb.set_ylabel('Fraction of entities with degree ≥ k')
    axb.set_xlim(0.9, 400); axb.set_ylim(1.5e-4, 1.4)
    axb.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
    axb.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
    med = int(np.median(d)); mx = int(d.max())
    axb.text(0.97, 0.97, f'n = {fmt(len(d))} entities with ≥1 relation\nMedian degree {med}; maximum {mx}',
             transform=axb.transAxes, fontsize=5.5, ha='right', va='top')

    # ---- c component sizes
    c.label(122, 61.5, 'c')
    comp = S['components']
    sizes = comp['sizes'] + [1] * comp['isolated']
    u, cnt = np.unique(sizes, return_counts=True)
    axc = c.ax(135, 66, 46, 46)
    axc.scatter(u, cnt, s=6, color=BLACK, lw=0, zorder=3)
    axc.set_xscale('log'); axc.set_yscale('log')
    axc.set_xlabel('Connected-component size (entities)'); axc.set_ylabel('Components')
    axc.set_xlim(0.7, 30000); axc.set_ylim(0.6, 20000)
    axc.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    axc.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    g = comp['giant']
    axc.annotate(f'Largest component\n{fmt(g)} entities ({pct(g, S["n_nodes"])})', (g, 1), (g * 0.9, 18),
                 fontsize=5.5, ha='right', va='bottom',
                 arrowprops=dict(arrowstyle='-', lw=0.4, color=BLACK, shrinkA=0.5, shrinkB=2))
    axc.annotate(f'Entities without relations\n{fmt(comp["isolated"])} ({pct(comp["isolated"], S["n_nodes"])})',
                 (1, comp['isolated']), (2.2, comp['isolated'] * 0.8), fontsize=5.5, ha='left', va='top',
                 arrowprops=dict(arrowstyle='-', lw=0.4, color=BLACK, shrinkA=0.5, shrinkB=2))
    return ns.save(c, 'fig4', OUT)


# ============================================================ Fig. 5 coverage
def fig5(S):
    c = Canvas(ns.DOUBLE, 134)
    W = S['works']
    # ---- a works × layers
    c.label(0, 0.5, 'a')
    M = np.array([[S['corpus_layer'].get((w['key'], l), 0) for l in dataset.LAYERS] for w in W], dtype=float)
    ax = c.ax(42, 4, 52, 50)
    cmap = LinearSegmentedColormap.from_list('blues', ['#F2F7FB', '#8CC0E3', BLUE, '#003A5C'])
    Mm = np.ma.masked_equal(M, 0)
    im = ax.imshow(Mm, cmap=cmap, norm=LogNorm(vmin=1, vmax=M.max()), aspect='auto')
    ax.set_facecolor('white')
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = int(M[i, j])
            if v:
                ax.text(j, i, fmt(v), fontsize=5, ha='center', va='center',
                        color='white' if v >= 400 else BLACK)
            else:
                ax.text(j, i, '–', fontsize=5, ha='center', va='center', color=BLACK)
    ax.set_xticks(range(len(dataset.LAYERS))); ax.set_xticklabels([L_EN[l] for l in dataset.LAYERS],
                                                                     rotation=40, ha='right', rotation_mode='anchor')
    ax.set_yticks(range(len(W))); ax.set_yticklabels([work_label(w, zh=False) for w in W])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(dataset.LAYERS)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(W)), minor=True)
    ax.grid(which='minor', color='white', lw=0.8); ax.tick_params(which='minor', length=0)
    cax = c.ax(96, 4, 2.2, 50)
    cb = plt.colorbar(im, cax=cax); cb.set_label('Relations'); cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(width=0.5, length=2)
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))

    # ---- b extraction coverage per layer
    c.label(112, 0.5, 'b')
    cov = S['layer_coverage']
    axb = c.ax(137, 4, 22, 40)
    yy = np.arange(len(dataset.LAYERS))[::-1]
    for yi, l in zip(yy, dataset.LAYERS):
        v = cov[l]
        frac = 100 * v['extracted'] / v['routed']
        axb.barh(yi, frac, height=0.6, color=LAYER_COL[l], lw=0)
        axb.text(103, yi, f"{fmt(v['extracted'])}/{fmt(v['routed'])} ({frac:.1f}%)", fontsize=5, va='center')
    axb.set_yticks(yy); axb.set_yticklabels([L_EN[l] for l in dataset.LAYERS]); axb.tick_params(axis='y', length=0)
    axb.set_xlim(0, 100); axb.set_xticks([0, 50, 100]); axb.set_ylim(-0.6, len(yy) - 0.4)
    axb.set_xlabel('Routed passages extracted (%)')

    # ---- c temporal coverage
    c.label(0, 66.5, 'c')
    life = S['lifespans']
    axc = c.ax(34, 71, 147, 55)
    yy = np.arange(len(life))[::-1]
    for (x0, x1, lab) in ((1368, 1644, 'Ming'), (1644, 1912, 'Qing'), (1912, 1949, 'Republic'),
                          (1949, 2035, "People's Republic")):
        axc.text((max(x0, 1440) + min(x1, 2030)) / 2, len(life) + 0.1, lab, fontsize=5.5, ha='center', va='bottom')
    for xb in (1644, 1912, 1949):
        axc.axvline(xb, color='#BDBDBD', lw=0.5, zorder=0)
    for yi, r in zip(yy, life):
        col = VERMILLION if r['rep'] else '#8C8C8C'
        axc.barh(yi, r['death'] - r['birth'], left=r['birth'], height=0.5, color=col, lw=0, zorder=2)
    labels = [f"{r['py']} {r['zh']}" + (f" (d. c. {r['death']})" if r['circa'] else '') for r in life]
    axc.set_yticks(yy); axc.set_yticklabels(labels, fontsize=5); axc.tick_params(axis='y', length=0)
    axc.set_ylim(-0.7, len(life) + 1.2); axc.set_xlim(1440, 2030)
    axc.set_xticks(range(1450, 2001, 50)); axc.set_xlabel('Year (CE)')
    clean(axc, left=False)
    h1 = Rectangle((0, 0), 1, 1, fc=VERMILLION, lw=0)
    h2 = Rectangle((0, 0), 1, 1, fc='#8C8C8C', lw=0)
    axc.legend([h1, h2], ['Representative physician of the school', 'Other dated physician'],
               loc='lower left', bbox_to_anchor=(0.0, 0.02))
    return ns.save(c, 'fig5', OUT)


# ============================================================ Fig. 6 technical validation
def fig6(S):
    c = Canvas(ns.DOUBLE, 104)
    W = S['works']; ev = S['evidence_by_work']
    # ---- a evidence located per work
    c.label(0, 0.5, 'a')
    ax = c.ax(33, 4, 56, 44)
    yy = np.arange(len(W))[::-1]
    cats = [('found', DARK, 'Found in cited passage'), ('not_found', VERMILLION, 'Not found'),
            ('unresolved', LIGHT, 'Passage not resolvable')]
    for yi, w in zip(yy, W):
        tot = sum(ev[(w['key'], k)] for k, _, _ in cats); left = 0
        for k, col, _ in cats:
            v = 100 * ev[(w['key'], k)] / tot
            ax.barh(yi, v, left=left, height=0.62, color=col, lw=0); left += v
        ax.text(101.5, yi, f'n = {fmt(tot)}', fontsize=5, va='center')
    ax.set_yticks(yy); ax.set_yticklabels([work_label(w, zh=False) for w in W]); ax.tick_params(axis='y', length=0)
    ax.set_xlim(0, 100); ax.set_ylim(-0.6, len(W) - 0.4); ax.set_xlabel('Relations (%)')
    ax.legend([Rectangle((0, 0), 1, 1, fc=col, lw=0) for _, col, _ in cats], [t for _, _, t in cats],
              loc='lower left', bbox_to_anchor=(0.0, 1.0), ncol=3, handlelength=0.9, columnspacing=0.9)

    # ---- b upstream verbatim flag × independent check
    c.label(112, 0.5, 'b')
    mat = S['verbatim_x_check']
    rows = [('verbatim', 'Marked verbatim'), ('non_verbatim', 'Marked non-verbatim')]
    cols = [('found', 'Found'), ('not_found', 'Not found'), ('unresolved', 'Not\nresolvable')]
    A = np.array([[mat[(r, k)] for k, _ in cols] for r, _ in rows], dtype=float)
    share = A / A.sum(axis=1, keepdims=True)
    axb = c.ax(142, 11, 39, 26)
    greys = LinearSegmentedColormap.from_list('g', ['#FFFFFF', '#6E6E6E'])
    axb.imshow(share, cmap=greys, vmin=0, vmax=1, aspect='auto')
    for i in range(2):
        for j in range(3):
            axb.text(j, i, f'{fmt(int(A[i, j]))}\n({100 * share[i, j]:.1f}%)', fontsize=5, ha='center',
                     va='center', color='white' if share[i, j] > 0.55 else BLACK, linespacing=1.0)
    axb.set_xticks(range(3)); axb.set_xticklabels([t for _, t in cols], fontsize=5.5, linespacing=1.0)
    axb.xaxis.tick_top(); axb.xaxis.set_label_position('top')
    axb.set_yticks(range(2)); axb.set_yticklabels([f'{t}\n(n = {fmt(int(A[i].sum()))})' for i, (_, t) in enumerate(rows)],
                                                  fontsize=5.5, linespacing=1.0)
    axb.tick_params(length=0)
    for s in axb.spines.values():
        s.set_visible(False)
    axb.set_xlabel('Independent check against cited passage', labelpad=3)
    axb.set_ylabel('Upstream flag', labelpad=3)

    # ---- c support per relation
    c.label(0, 57.5, 'c')
    sup = S['support']; ks = sorted(sup); vs = [sup[k] for k in ks]
    axc = c.ax(14, 61, 70, 33)
    axc.vlines(ks, 0.8, vs, color=DARK, lw=1.0)
    axc.scatter(ks, vs, s=5, color=BLACK, lw=0, zorder=3)
    axc.set_xscale('log'); axc.set_yscale('log'); axc.set_xlim(0.8, 250); axc.set_ylim(0.8, 60000)
    axc.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
    axc.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    axc.set_xlabel('Supporting mentions per relation'); axc.set_ylabel('Relations')
    one = sup.get(1, 0)
    axc.text(1.25, one, f'{fmt(one)} ({pct(one, S["n_edges"])}) single mention', fontsize=5.5, va='center')

    # ---- d cardinality exceptions
    c.label(112, 57.5, 'd')
    exc = S['cardinality_exceptions']
    items = sorted(exc.items(), key=lambda kv: kv[1])
    axd = c.ax(141, 61, 38, 33)
    yy = np.arange(len(items))
    axd.barh(yy, [v for _, v in items], height=0.6, color=DARK, lw=0)
    for yi, (_, v) in zip(yy, items):
        axd.text(v + 0.4, yi, str(v), fontsize=5, va='center')
    axd.set_yticks(yy); axd.set_yticklabels([k for k, _ in items], fontsize=5.5); axd.tick_params(axis='y', length=0)
    axd.set_xlim(0, 24); axd.set_ylim(-0.6, len(items) - 0.4)
    axd.set_xlabel('Subjects with >1 object for a 0..1 relation')
    return ns.save(c, 'fig6', OUT)


def main():
    ns.apply()
    S = dataset.load()
    wanted = sys.argv[1:] or ['fig1', 'fig2', 'fig3', 'fig4', 'fig5', 'fig6']
    for name in wanted:
        r = globals()[name](S)
        print(f"{r['name']}: {r['mm'][0]}×{r['mm'][1]} mm, {r['px'][0]}×{r['px'][1]} px @800 dpi"
              + (f"  ISSUES: {r['issues']}" if r['issues'] else '  ok'))


if __name__ == '__main__':
    main()
