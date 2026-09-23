#!/usr/bin/env python3
"""
Figure legends for the Scientific Data Data Descriptor, with every number taken from dataset.py.

  python3 paper/make_legends.py      # → paper/LEGENDS.md (and a word count per legend; cap 300 words)
"""
import re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dataset  # noqa: E402

fmt = lambda v: f'{v:,}'
pct = lambda a, b: f'{100 * a / b:.1f}%'
_W = 'zero one two three four five six seven eight nine'.split()


def num(n, cap=False):
    """Nature style: spell out whole numbers below 10."""
    s = _W[n] if 0 <= n < 10 else fmt(n)
    return s[0].upper() + s[1:] if cap else s


def legends(S):
    T, m, im = S['corpus_totals'], S['modern'], S['identity_merge']
    ev = S['evidence_by_work']
    found = sum(v for (w, k), v in ev.items() if k == 'found')
    res = sum(v for (w, k), v in ev.items() if k != 'unresolved')
    n_cls = sum(1 for x in S['classes'] if x['n']); n_prop = sum(1 for p in S['properties'] if p['n'])
    ex = S['example']
    life = S['lifespans']
    con = sum(1 for n in S['nodes'] if S['deg'][n['id']])
    one = S['support'].get(1, 0)
    cov = S['layer_coverage']
    low = [dataset.LAYER_EN[l] for l, v in sorted(cov.items(), key=lambda kv: kv[1]['extracted'] / kv[1]['routed'])[:2]]
    return [
        ('Fig. 1', 'Construction and provenance of the Shaopai Shanghan knowledge graph and corpus.',
         f"a, Construction workflow. {num(len(S['works']), True)} published works ({fmt(T['passages'])} passages; "
         f"{fmt(T['chars'])} characters) were segmented along their chapter structure, each passage receiving a "
         f"stable identifier. Passages were routed to {num(len(dataset.LAYERS))} knowledge layers, and entities and "
         f"relations were extracted under ontology v{S['ontology_version']} ({len(S['onto']['classes'])} classes, "
         f"{len(S['onto']['object_properties'])} relation types), each relation carrying its evidence sentence and "
         f"passage identifier. Script variants and physician name variants were merged "
         f"({im.get('nodes_merged', 0)} entities); schema conformance, evidence location and declared "
         f"cardinalities were then checked, and all outputs were screened for personal identifiers. The release "
         f"contains {fmt(S['n_nodes'])} entities and {fmt(S['n_edges'])} relations. A ninth delivered source, "
         f"{m['passages']} modern outpatient records ({fmt(m['edges'])} relations), is withheld pending consent "
         f"review (dashed box). b, Record structure, shown for one passage of the He Lianchen case records "
         f"({ex['passage']['pid']}). {num(len(ex['edges']), True)} relations of "
         f"{num(len({e['type'] for e in ex['edges']}))} types were extracted from it; tinted spans mark the evidence "
         f"of each relation in the passage text. The relation record lists the provenance fields of one relation "
         f"({ex['featured']['type']} → {ex['featured']['object_name']}, Sichuan fritillary bulb). "
         f"evidence_verbatim is the upstream extraction flag; evidence_in_passage is the independent check "
         f"described in Technical Validation. English glosses are the authors' translations."),
        ('Fig. 2', 'Composition of the text corpus.',
         f"a, Characters per source work (Unicode code points, including punctuation). b, Passages per source "
         f"work. c, Passage length per source work: each dot is one passage (n = {fmt(T['passages'])} passages in "
         f"total; per-work n as in b); boxes show the median and interquartile range, and whiskers the 5th and "
         f"95th percentiles. Works are ordered by size; Chinese titles are given under the English short titles "
         f"and full bibliographic details in Table 1. †, traditional-script source text. Passages of Shaopai "
         f"Shanghan follow this release's re-segmentation of the original book."),
        ('Fig. 3', 'Schema and composition of the knowledge graph.',
         f"a, Class-level schema. Circles are the {n_cls} populated entity classes (area proportional to the "
         f"number of entities); arrows are the {n_prop} populated relation types, drawn from domain to range, "
         f"coloured by knowledge layer, with line width increasing with the square root of the number of "
         f"relations. Loops are relations whose domain and range are the same class. "
         f"{num(len(S['onto']['classes']) - n_cls, True)} classes and {num(len(S['onto']['object_properties']) - n_prop)} relation "
         f"types defined in the ontology have no released instances (Tables 2 and 3). b, Entities per class, "
         f"split into entities with at least one relation and entities without relations. c, Relations per type "
         f"(log scale), grouped by layer and coloured as in a. Colours follow the Okabe–Ito colour-blind-safe "
         f"palette."),
        ('Fig. 4', 'Topology of the knowledge graph.',
         f"a, The complete graph ({fmt(S['n_nodes'])} entities, {fmt(S['n_edges'])} relations) drawn with the "
         f"fixed layout released with the data. Lines are relations, coloured by knowledge layer; dark dots are "
         f"entities with at least one relation (dot area increases with degree); light grey dots in the outer ring "
         f"are the {fmt(S['components']['isolated'])} entities without relations. Case-record relations dominate "
         f"the central component; the cluster at lower left joins physicians, works and doctrines. Labelled hubs: "
         f"Yu Genchu 俞根初, founder of the school; He Lianchen 何廉臣, author of the case records; Huashi 滑石 "
         f"(talc) and Zhuru 竹茹 (bamboo shavings), the two most-connected herbs. b, Complementary cumulative "
         f"degree distribution for the {fmt(con)} entities with at least one relation (log–log axes). c, Size "
         f"distribution of connected components (log–log axes); entities without relations are counted as "
         f"components of size 1. The largest component holds {fmt(S['components']['giant'])} entities "
         f"({pct(S['components']['giant'], S['n_nodes'])})."),
        ('Fig. 5', 'Coverage across source works, knowledge layers and time.',
         f"a, Relations per source work and knowledge layer (colour on a logarithmic scale; –, none). "
         f"b, Extraction coverage per layer: passages from which relations were extracted as a share of the "
         f"passages routed to that layer; shortfalls reflect per-frame output limits of the extraction, so counts "
         f"from the {low[0]} and {low[1]} layers are lower bounds. c, Lifespans of the {len(life)} physicians with "
         f"recorded birth and death years, from {life[0]['py']} ({life[0]['birth']}–{life[0]['death']}) to "
         f"{life[-1]['py']} ({life[-1]['birth']}–{life[-1]['death']}); vermillion marks the representative "
         f"physicians profiled in Shaopai Shanghan. Vertical lines mark the dynastic transitions of 1644, 1912 and "
         f"1949. d. c., died circa."),
        ('Fig. 6', 'Technical validation of relation provenance and schema conformance.',
         f"a, Outcome of the independent evidence check per source work: whether the evidence sentence of each "
         f"relation was found in its cited passage after Unicode normalization and removal of white space. "
         f"Relations from Shaopai Shanghan cite an upstream passage segmentation that could not be aligned with "
         f"the released text. n, relations per work. Of the {fmt(res)} relations with a resolvable passage, "
         f"{fmt(found)} ({pct(found, res)}) were found. b, Agreement between the upstream verbatim flag (rows) and "
         f"the independent check (columns); cells give counts and row percentages. c, Supporting mentions per "
         f"relation (log–log axes); {fmt(one)} relations ({pct(one, S['n_edges'])}) rest on a single mention. "
         f"d, Relation types declared 0..1 whose subjects nonetheless have more than one object, with the number "
         f"of such subjects ({sum(S['cardinality_exceptions'].values())} in total); these are reported, not "
         f"corrected. No domain or range violations, dangling endpoints, self-loops or duplicate triples were "
         f"found (Table 5). Descriptive statistics only; no statistical tests were performed."),
    ]


def main():
    S = dataset.load()
    out = ['# Figure legends', '',
           'Scientific Data style: bold title sentence, then panel descriptions; ≤ 300 words each. '
           'Generated by `paper/make_legends.py` from the released data.', '']
    for fid, title, body in legends(S):
        words = len(re.findall(r"[A-Za-z0-9'’.–-]+|[一-鿿]+", title + ' ' + body))
        assert words <= 300, f'{fid}: {words} words'
        out += [f'**{fid} | {title}** {body}', '', f'<sub>{words} words</sub>', '']
        print(f'{fid}: {words} words')
    out += ['# Table titles', '',
            'Titles, column headers and footnotes are in `tables/Tables.docx` (editable, three-line) and '
            '`tables/tables.tex` (booktabs).', '']
    import json
    for t in json.loads((HERE / 'tables' / 'tables.json').read_text(encoding='utf-8')):
        out.append(f"**Table {t['id']} | {t['title']}**")
    (HERE / 'LEGENDS.md').write_text('\n'.join(out) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
