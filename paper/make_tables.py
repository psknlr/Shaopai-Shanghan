#!/usr/bin/env python3
"""
Tables for the Scientific Data Data Descriptor, computed from data/ via dataset.py.

  python3 paper/make_tables.py        # → paper/tables/table1–5.csv, tables.tex, tables.md, tables.json
  node paper/make_tables_docx.js      # → paper/tables/Tables.docx (reads tables.json; needs `npm install docx`)

Three-line style throughout: rules above and below the header and at the foot only, units in headers,
footnotes keyed by symbols (never numerals).
"""
import csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'tools'))
import dataset  # noqa: E402
from import_upstream import REL_LAYER  # noqa: E402

OUT = HERE / 'tables'
DATA = dataset.DATA
fmt = lambda v: f'{v:,}'
pct = lambda a, b: f'{100 * a / b:.1f}%'
SYM = ['*', '†', '‡', '§', '‖', '¶']


def table1(S):
    rows = []
    for w in S['works']:
        rows.append([w['zh'] + (' ‡' if w['key'] == 'shaopai' else ''), w['en'], w['genre'], (w['resp'] or '–') + (f", {w['year']}" if w['year'] else ''),
                     w['script'], fmt(w['passages']), fmt(w['chars']), fmt(w['relations'])])
    T = S['corpus_totals']
    rows.append([{'t': 'Total §', 'b': True}, f"{len(S['works'])} works", '', '', '', fmt(T['passages']),
                 fmt(T['chars']), fmt(S['n_edges'])])
    m = S['modern']
    return dict(
        id=1, title='Source works of the corpus and the relations extracted from each.',
        columns=[('Source work', 'l', 20), ('English title', 'l', 35), ('Genre', 'l', 21),
                 ('Responsibility*', 'l', 27), ('Script', 'l', 16), ('Passages', 'r', 15),
                 ('Characters†', 'r', 19), ('Relations', 'r', 17)],
        rows=rows,
        foot=['* As recorded in the delivered sources; –, not recorded.',
              '† Unicode code points of passage text, including punctuation.',
              '‡ 浙派中医丛书·绍派伤寒 (Shaopai Shanghan): passages follow this release\'s re-segmentation of the '
              'original book (b-numbered); its relations cite the upstream p-numbered segmentation, which could not '
              'be aligned (Technical Validation).',
              f"§ A ninth source, {m['passages']} outpatient case records (2022–2026), was delivered but is withheld "
              f"from release pending consent review; its {fmt(m['edges'])} relations and {fmt(m['nodes'])} "
              'dependent entities are excluded from all counts.'])


def table2(S):
    cl = sorted(S['classes'], key=lambda x: (-x['n'], x['cls'] not in dataset.MODERN_ONLY, x['cls']))
    rows = []
    for x in cl:
        tag = ' †' if x['cls'] in dataset.MODERN_ONLY else (' ‡' if not x['n'] else '')
        rows.append([x['en'] + tag, x['zh'], ', '.join(a for a in x['attrs']) or '–', fmt(x['n']),
                     fmt(x['connected']), fmt(x['isolated'])])
    n_pop = sum(1 for x in cl if x['n'])
    rows.append([{'t': 'Total', 'b': True}, '', f'{n_pop} of {len(cl)} classes populated', fmt(S['n_nodes']),
                 fmt(sum(x['connected'] for x in cl)), fmt(sum(x['isolated'] for x in cl))])
    return dict(
        id=2, title=f"Entity classes of ontology v{S['ontology_version']} and their instances.",
        columns=[('Class', 'l', 30), ('Chinese label', 'l', 16), ('Declared attributes*', 'l', 76),
                 ('Entities', 'r', 16), ('With relations', 'r', 16), ('Without relations', 'r', 16)],
        rows=rows,
        foot=['* Attribute names as declared in the ontology specification; values are extracted text, not '
              'normalized codes.',
              '† Populated only by the withheld modern outpatient records.',
              '‡ Defined in the ontology but not populated by any released source.'])


LAYER_TITLE = {'lineage': 'Lineage', 'diagnostic': 'Diagnosis', 'pattern': 'Pattern', 'materia': 'Materia medica',
               'case': 'Case records', 'culture': 'Culture', 'modern_case': 'Modern outpatient records (withheld) ‡'}


def table3(S):
    exc = S['cardinality_exceptions']
    rows, groups = [], []
    order = dataset.LAYERS + ['modern_case']
    props = S['properties']
    for l in order:
        ps = sorted([p for p in props if REL_LAYER.get(p['prop']) == l], key=lambda p: (-p['n'], p['prop']))
        if not ps:
            continue
        groups.append(len(rows))
        rows.append([{'t': LAYER_TITLE[l] + ' layer' if l != 'modern_case' else LAYER_TITLE[l], 'i': True,
                      'span': True}, '', '', '', '', ''])
        for p in ps:
            e = exc.get(p['prop'])
            rows.append([p['prop'] + (' †' if not p['n'] and l != 'modern_case' else ''), p['zh'],
                         f"{dataset.CLASS_EN[p['domain']]} → {dataset.CLASS_EN[p['range']]}", p['card'],
                         fmt(e) if e else ('0' if p['card'].endswith('..1') else '–'), fmt(p['n'])])
    n_used = sum(1 for p in props if p['n'])
    rows.append([{'t': 'Total', 'b': True}, '', f'{n_used} of {len(props)} relation types populated', '',
                 fmt(sum(exc.values())), fmt(S['n_edges'])])
    return dict(
        id=3, title='Relation types: declared domain, range and cardinality, and observed counts.',
        columns=[('Relation', 'l', 36), ('Chinese label', 'l', 18), ('Domain → range', 'l', 58),
                 ('Declared cardinality', 'l', 18), ('Exceptions*', 'r', 18), ('Relations', 'r', 22)],
        rows=rows, group_rows=groups,
        foot=['* Subjects with more than one distinct object for a relation declared 0..1; reported, not corrected. '
              '–, relation declared 0..* or 1..*.',
              '† Defined in the ontology but not populated by any released source.',
              '‡ Populated only by the withheld modern outpatient records.'])


def _triples(path):
    try:
        import rdflib
        g = rdflib.Graph(); g.parse(str(path), format='turtle')
        return len(g)
    except Exception:
        return None


def table4(S):
    def size(f):
        if not (DATA / f).exists():
            return '–'
        mb = (DATA / f).stat().st_size / 1e6
        return '<0.01' if mb < 0.005 else f'{mb:.2f}'

    def csv_rows(f):
        with open(DATA / f, encoding='utf-8') as fh:
            return sum(1 for _ in csv.reader(fh)) - 1
    nq = len(re.findall(r'^// \d+\.', (DATA / 'example_queries.cypher').read_text(encoding='utf-8'), re.M))
    t_inst, t_onto = _triples(DATA / 'shaopai_instances.ttl'), _triples(DATA / 'shaopai_ontology.ttl')
    cy = json.loads((DATA / 'corpus_yueyi.json').read_text(encoding='utf-8'))
    cs = json.loads((DATA / 'corpus_shaopai.json').read_text(encoding='utf-8'))
    n_cls, n_prop = len(S['onto']['classes']), len(S['onto']['object_properties'])
    rows = [
        ['shaopai_kg.json', 'JSON', size('shaopai_kg.json'), f"{fmt(S['n_nodes'])} entities; {fmt(S['n_edges'])} relations",
         'Complete graph: ontology, controlled vocabularies, entities with attributes and provenance, relations with evidence fields'],
        ['nodes.csv', 'CSV', size('nodes.csv'), f"{fmt(csv_rows('nodes.csv'))} rows",
         'Entities in Neo4j import format, with attributes, layout coordinates and component index'],
        ['edges.csv', 'CSV', size('edges.csv'), f"{fmt(csv_rows('edges.csv'))} rows",
         'Relations with passage identifier, evidence sentence, chapter path, layer, source work, verification flags'],
        ['load_neo4j.cypher', 'Cypher', size('load_neo4j.cypher'), '–', 'Constraints, indexes and batched import script'],
        ['example_queries.cypher', 'Cypher', size('example_queries.cypher'), f'{nq} queries',
         'Worked graph queries with SPARQL equivalents'],
        ['shaopai_instances.ttl', 'RDF/Turtle', size('shaopai_instances.ttl'),
         f'{fmt(t_inst)} triples' if t_inst else '–',
         'Instance data; each relation reified as rdf:Statement carrying its provenance'],
        ['shaopai_ontology.ttl', 'OWL/Turtle', size('shaopai_ontology.ttl'),
         f'{n_cls} classes; {n_prop} relation types' + (f'; {fmt(t_onto)} triples' if t_onto else ''),
         'Ontology with bilingual labels, domains, ranges and cardinality annotations'],
        ['corpus_yueyi.json', 'JSON', size('corpus_yueyi.json'), f"{fmt(len(cy['passages']))} passages",
         'Segmented text of seven source works with passage identifiers and chapter paths'],
        ['corpus_shaopai.json', 'JSON', size('corpus_shaopai.json'), f"{fmt(len(cs['passages']))} passages",
         'Segmented text of Shaopai Shanghan (b-numbered re-segmentation)'],
        ['layout_positions.json', 'JSON', size('layout_positions.json'), f"{fmt(S['n_nodes'])} coordinates",
         'Fixed two-dimensional layout used by the web explorer'],
        ['disease_profiles.csv', 'CSV', size('disease_profiles.csv'), f"{fmt(csv_rows('disease_profiles.csv'))} rows",
         'Per-disease case counts with co-occurring herbs and symptoms (He Lianchen case records)'],
        ['modern_case_profiles.csv', 'CSV', size('modern_case_profiles.csv'),
         f"{fmt(csv_rows('modern_case_profiles.csv'))} rows",
         'Aggregate profile of the withheld outpatient records; cells with fewer than 3 cases suppressed'],
        ['qc_audit.json', 'JSON', size('qc_audit.json'), '–', 'Machine-readable quality-control figures'],
        ['QC_AUDIT.md', 'Markdown', size('QC_AUDIT.md'), '–', 'Quality-control report'],
    ]
    return dict(
        id=4, title='Data records.',
        columns=[('File*', 'l', 34), ('Format', 'l', 18), ('Size (MB)†', 'r', 14), ('Records', 'l', 34),
                 ('Content', 'l', 70)],
        rows=rows,
        foot=['* In the data/ directory of the repository; the web explorer (explorer.html) and the two-book '
              'edition (v1.html) embed the same graph.',
              '† 1 MB = 1,000,000 bytes.'])


def table5(S):
    E = S['n_edges']
    ev = S['evidence_by_work']
    found = sum(v for (w, k), v in ev.items() if k == 'found')
    nf = sum(v for (w, k), v in ev.items() if k == 'not_found')
    unres = sum(v for (w, k), v in ev.items() if k == 'unresolved')
    mat = S['verbatim_x_check']
    vb_res = mat[('verbatim', 'found')] + mat[('verbatim', 'not_found')]
    cov = S['layer_coverage']
    lo = min(cov.values(), key=lambda v: v['extracted'] / v['routed'])
    lo_l = next(l for l, v in cov.items() if v is lo)
    im = S['identity_merge']
    exc = S['cardinality_exceptions']
    one = S['support'].get(1, 0)
    rows = [
        ['Schema conformance (domain and range)', f'All relations ({fmt(E)})', f"{S['domain_range_violations']} violations"],
        ['Referential integrity', f'All relations ({fmt(E)})', f"{S['dangling']} dangling endpoints"],
        ['Self-loops', f'All relations ({fmt(E)})', str(S['self_loops'])],
        ['Duplicate (subject, relation, object) triples', f'All relations ({fmt(E)})', str(S['duplicates'])],
        ['Passage identifier present', f'All relations ({fmt(E)})', f"{fmt(S['with_pid'])} ({pct(S['with_pid'], E)})"],
        ['Evidence sentence present', f'All relations ({fmt(E)})', f"{fmt(S['with_sentence'])} ({pct(S['with_sentence'], E)})"],
        ['Evidence sentence located in cited passage*', f'Relations with resolvable passage ({fmt(found + nf)})',
         f'{fmt(found)} ({pct(found, found + nf)})'],
        ['Upstream verbatim flag not confirmed*', f'Flagged verbatim, passage resolvable ({fmt(vb_res)})',
         f"{fmt(mat[('verbatim', 'not_found')])} ({pct(mat[('verbatim', 'not_found')], vb_res)})"],
        ['Cited passage not resolvable†', f'All relations ({fmt(E)})', f'{fmt(unres)} ({pct(unres, E)})'],
        ['Declared 0..1 cardinality', f'{len(exc)} relation types', f'{sum(exc.values())} subjects with >1 object'],
        ['Identity resolution', 'Entities', f"{im.get('nodes_merged', 0)} merged ({im.get('script_variant_groups', 0)} "
         f"script-variant groups; {im.get('name_variant_pairs', 0)} name-variant pairs)"],
        ['Extraction coverage‡', 'Routed passages per layer',
         f"{min(100 * v['extracted'] / v['routed'] for v in cov.values()):.1f}–"
         f"{max(100 * v['extracted'] / v['routed'] for v in cov.values()):.1f}% (lowest: {dataset.LAYER_EN[lo_l]})"],
        ['Evidence redundancy', f'All relations ({fmt(E)})', f'{fmt(one)} ({pct(one, E)}) supported by one mention'],
        ['Privacy screening§', 'All released files', '0 matches; modern outpatient layer withheld'],
        ['Cross-model agreement', f'All relations ({fmt(E)})', 'Not assessed (single extraction model)'],
    ]
    return dict(
        id=5, title='Summary of technical validation.',
        columns=[('Check', 'l', 62), ('Scope', 'l', 56), ('Result', 'l', 52)],
        rows=rows,
        foot=['* After Unicode NFKC normalization and removal of white space; multi-part evidence joined by '
              '“ / ” counts as located when every part is found.',
              '† Relations from Shaopai Shanghan cite an upstream passage segmentation that could not be aligned '
              'with the released text.',
              '‡ Share of passages routed to a layer from which relations were extracted; shortfalls arise from '
              'per-frame output limits, so counts from those layers are lower bounds.',
              '§ Patient-header patterns (name, sex, age and record number), national identity and telephone '
              'numbers, and patient names derived at run time from the withheld records.'])


# ------------------------------------------------------------------ writers
def cell_text(c):
    return c['t'] if isinstance(c, dict) else str(c)


def write_csv(t):
    with open(OUT / f"table{t['id']}.csv", 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow([h for h, _, _ in t['columns']])
        for r in t['rows']:
            w.writerow([cell_text(c) for c in r])
        for fn in t['foot']:
            w.writerow([fn])


def tex_escape(s):
    rep = {'&': r'\&', '%': r'\%', '_': r'\_', '#': r'\#', '$': r'\$', '~': r'\textasciitilde{}',
           '^': r'\^{}', '→': r'$\rightarrow$', '†': r'\textdagger{}', '‡': r'\textdaggerdbl{}', '§': r'\S{}',
           '‖': r'\textbardbl{}', '¶': r'\P{}', '≥': r'$\geq$', '–': '--', '“': '``', '”': "''", '×': r'$\times$'}
    return ''.join(rep.get(ch, ch) for ch in s)


def write_tex(tables):
    out = [r'% Tables for the Scientific Data Data Descriptor. Compile with XeLaTeX:',
           r'% \usepackage{booktabs,tabularx,xeCJK,threeparttable} and \setCJKmainfont{Noto Serif CJK SC}.', '']
    for t in tables:
        spec = ''.join('X' if w >= 40 and a == 'l' else ('r' if a == 'r' else 'l') for _, a, w in t['columns'])
        out += [r'\begin{table}[p]', r'\footnotesize', r'\begin{threeparttable}',
                rf"\caption{{\textbf{{Table {t['id']} $|$}} {tex_escape(t['title'])}}}",
                rf'\begin{{tabularx}}{{\linewidth}}{{{spec}}}', r'\toprule',
                ' & '.join(tex_escape(h) for h, _, _ in t['columns']) + r' \\', r'\midrule']
        n = len(t['columns'])
        for r in t['rows']:
            c0 = r[0]
            if isinstance(c0, dict) and c0.get('span'):
                out.append(rf"\multicolumn{{{n}}}{{l}}{{\textit{{{tex_escape(c0['t'])}}}}} \\")
                continue
            cells = []
            for c in r:
                s = tex_escape(cell_text(c))
                if isinstance(c, dict) and c.get('b'):
                    s = rf'\textbf{{{s}}}'
                cells.append(s)
            out.append(' & '.join(cells) + r' \\')
        out += [r'\bottomrule', r'\end{tabularx}', r'\begin{tablenotes}\footnotesize']
        out += [rf'\item {tex_escape(fn)}' for fn in t['foot']]
        out += [r'\end{tablenotes}', r'\end{threeparttable}', r'\end{table}', '']
    (OUT / 'tables.tex').write_text('\n'.join(out), encoding='utf-8')


def write_md(tables):
    out = []
    for t in tables:
        out += [f"**Table {t['id']} | {t['title']}**", '',
                '| ' + ' | '.join(h for h, _, _ in t['columns']) + ' |',
                '| ' + ' | '.join('---:' if a == 'r' else '---' for _, a, _ in t['columns']) + ' |']
        for r in t['rows']:
            c0 = r[0]
            if isinstance(c0, dict) and c0.get('span'):
                out.append(f"| *{c0['t']}* |" + ' |' * (len(t['columns']) - 1))
                continue
            out.append('| ' + ' | '.join((f"**{cell_text(c)}**" if isinstance(c, dict) and c.get('b') else cell_text(c))
                                         for c in r) + ' |')
        out += [''] + [f'{fn}  ' for fn in t['foot']] + ['']
    (OUT / 'tables.md').write_text('\n'.join(out), encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    S = dataset.load()
    tables = [table1(S), table2(S), table3(S), table4(S), table5(S)]
    for t in tables:
        write_csv(t)
    write_tex(tables)
    write_md(tables)
    (OUT / 'tables.json').write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding='utf-8')
    for t in tables:
        print(f"Table {t['id']}: {len(t['rows'])} rows × {len(t['columns'])} columns — {t['title']}")


if __name__ == '__main__':
    main()
