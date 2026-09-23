#!/usr/bin/env python3
"""
Every number shown in the paper's figures and tables, computed from data/ at run time.
make_figures.py and make_tables.py both read from here, so a figure and a table can never disagree.
"""
import json, re, sys, collections, statistics
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
sys.path.insert(0, str(ROOT / 'tools'))
from import_upstream import corpus_of  # noqa: E402  chapter root → source-work key (same rule as the import)

LAYERS = ['lineage', 'diagnostic', 'pattern', 'materia', 'case', 'culture']
LAYER_EN = {'lineage': 'Lineage', 'diagnostic': 'Diagnosis', 'pattern': 'Pattern',
            'materia': 'Materia medica', 'case': 'Case records', 'culture': 'Culture'}

# Bibliographic facts as recorded in the delivery (README / meta); unknown fields are left empty, never guessed.
WORKS = {
    'shaopai': dict(zh='浙派中医丛书·绍派伤寒', en='Shaopai Shanghan (Zhejiang School of Chinese Medicine series)',
                    short='Shaopai Shanghan', resp='Shen Qinrong (ed.)', year='2021', script='Simplified',
                    genre='School monograph'),
    'hlc_yian': dict(zh='何廉臣医案', en='Case records of He Lianchen', short='He Lianchen case records',
                     resp='He Lianchen', year='', script='Simplified', genre='Case records'),
    'ygc_jingyao': dict(zh='俞根初临证经验集要', en="Essentials of Yu Genchu's clinical experience",
                        short='Essentials of Yu Genchu', resp='Shen Qinrong (comp.)', year='', script='Simplified',
                        genre='Monograph on the founder'),
    'zqc_yilun': dict(zh='赵晴初医论', en='Medical essays of Zhao Qingchu', short='Zhao Qingchu essays',
                      resp='Zhao Qingchu', year='', script='Simplified', genre='Medical essays'),
    'yz_mingyi': dict(zh='越中名医传', en='Biographies of eminent physicians of Yuezhong (part 2 and supplement)',
                      short='Yuezhong physicians', resp='', year='', script='Traditional', genre='Biographies'),
    'sp_shiliao': dict(zh='绍派伤寒史料图片研究', en='Pictorial historical sources of the Shaopai school',
                       short='Pictorial history', resp='Tao Jianhua (chief reviewer); Shen Qinrong, Lin Yibing (eds.)',
                       year='', script='Simplified', genre='Illustrated catalogue'),
    'yue_wenhua': dict(zh='越医文化', en='Medical culture of Yue (10 chapters, contents and postscript)',
                       short='Yue medical culture', resp='', year='', script='Simplified', genre='Regional medical history'),
    'yy_zayong': dict(zh='越醫雜詠', en='Miscellaneous verses on Yue medicine', short='Yue medical verses',
                      resp='', year='', script='Traditional', genre='Verse'),
}
CLASS_EN = {
    'Physician': 'Physician', 'Work': 'Work', 'Doctrine': 'Doctrine', 'DiagnosticSign': 'Diagnostic sign',
    'Pattern': 'Pattern', 'Formula': 'Formula', 'Herb': 'Herb', 'TreatmentPrinciple': 'Treatment principle',
    'CaseRecord': 'Case record', 'Disease': 'Disease', 'Symptom': 'Symptom', 'HerbProperty': 'Herb property',
    'Institution': 'Institution', 'Place': 'Place', 'MedicalFamily': 'Medical family', 'Dosage': 'Dosage',
    'WesternDiagnosis': 'Western diagnosis', 'Procedure': 'Procedure', 'WesternDrug': 'Western drug',
    'Examination': 'Examination',
}
MODERN_ONLY = {'WesternDiagnosis', 'Procedure', 'WesternDrug', 'Examination'}
# Representative physicians profiled in part 2 of the Shaopai Shanghan monograph (chapter roots of corpus_shaopai.json)
REPRESENTATIVE = ['张景岳', '俞根初', '章 楠', '何廉臣', '张畹香', '周伯度', '赵晴初', '胡宝书', '邵兰荪', '曹炳章', '徐荣斋']
PINYIN = {  # checked by hand (surnames and syllable boundaries)
    '葛滂': 'Ge Pang', '张景岳': 'Zhang Jingyue', '俞根初': 'Yu Genchu', '张畹香': 'Zhang Wanxiang',
    '赵晴初': 'Zhao Qingchu', '周岩': 'Zhou Yan', '何廉臣': 'He Lianchen', '邵兰荪': 'Shao Lansun',
    '杨质安': "Yang Zhi'an", '胡宝书': 'Hu Baoshu', '汪竹安': "Wang Zhu'an", '杨厚斋': 'Yang Houzhai',
    '曹炳章': 'Cao Bingzhang', '张若霞': 'Zhang Ruoxia', '傅幼真': 'Fu Youzhen', '尹幼莲': 'Yin Youlian',
    '俞修源': 'Yu Xiuyuan', '郑惠中': 'Zheng Huizhong', '徐荣斋': 'Xu Rongzhai', '郭若定': 'Guo Ruoding',
    '方春阳': 'Fang Chunyang', '章虚谷': 'Zhang Xugu',
}


def _year(v):
    """'1860' → (1860, False); '约1905' → (1905, True); anything else → (None, False)."""
    m = re.fullmatch(r'(约)?\s*(\d{4})', str(v or '').strip())
    return (int(m.group(2)), bool(m.group(1))) if m else (None, False)


@lru_cache(maxsize=1)
def load():
    kg = json.loads((DATA / 'shaopai_kg.json').read_text(encoding='utf-8'))
    cy = json.loads((DATA / 'corpus_yueyi.json').read_text(encoding='utf-8'))
    cs = json.loads((DATA / 'corpus_shaopai.json').read_text(encoding='utf-8'))
    qc = json.loads((DATA / 'qc_audit.json').read_text(encoding='utf-8'))
    pos = json.loads((DATA / 'layout_positions.json').read_text(encoding='utf-8'))
    nodes, edges, onto, meta = kg['nodes'], kg['edges'], kg['ontology'], kg['meta']
    N = {n['id']: n for n in nodes}
    S = {}

    # ---------------------------------------------------------------- corpus
    lengths = collections.defaultdict(list)
    for p in cy['passages']:
        lengths[corpus_of(p['source'])].append(len(p.get('text') or ''))
    for p in cs['passages']:
        lengths['shaopai'].append(len(p.get('text') or ''))
    assert '' not in lengths, 'unmapped corpus source'
    work_rel = collections.Counter(e['corpus'] for e in edges)
    works = []
    for k, L in lengths.items():
        q = statistics.quantiles(L, n=4)
        works.append(dict(key=k, **WORKS[k], passages=len(L), chars=sum(L), lengths=L,
                          median=statistics.median(L), q1=q[0], q3=q[2], relations=work_rel.get(k, 0),
                          layers=collections.Counter(e['layer'] for e in edges if e['corpus'] == k)))
    works.sort(key=lambda w: -w['chars'])
    S['works'] = works
    S['corpus_totals'] = dict(passages=sum(w['passages'] for w in works), chars=sum(w['chars'] for w in works))
    S['pid_scheme_shaopai'] = cs['meta'].get('note', '')
    rel = meta.get('modern_case_release') or {}
    S['modern'] = dict(status=rel.get('status'), edges=rel.get('edges_withheld', 0),
                       nodes=rel.get('nodes_withheld', 0), passages=131)

    # ---------------------------------------------------------------- graph composition
    deg = collections.Counter()
    for e in edges:
        deg[e['subject_id']] += 1; deg[e['object_id']] += 1
    S['deg'] = deg
    cls_n = collections.Counter(n['cls'] for n in nodes)
    cls_iso = collections.Counter(n['cls'] for n in nodes if not deg[n['id']])
    S['classes'] = [dict(cls=c, en=CLASS_EN.get(c, c), zh=v['zh'], attrs=v.get('attrs', []),
                         n=cls_n.get(c, 0), isolated=cls_iso.get(c, 0), connected=cls_n.get(c, 0) - cls_iso.get(c, 0))
                    for c, v in onto['classes'].items()]
    ptype = collections.Counter(e['type'] for e in edges)
    play = {t: collections.Counter(e['layer'] for e in edges if e['type'] == t).most_common(1)[0][0] for t in ptype}
    S['properties'] = [dict(prop=p, zh=v['zh'], domain=v['domain'], range=v['range'], card=v['card'],
                            n=ptype.get(p, 0), layer=play.get(p, ''))
                       for p, v in onto['object_properties'].items()]
    S['n_nodes'], S['n_edges'] = len(nodes), len(edges)
    S['ontology_version'] = onto.get('version') or meta.get('ontology_version')
    S['corpus_layer'] = collections.Counter((e['corpus'], e['layer']) for e in edges)
    S['layer_n'] = collections.Counter(e['layer'] for e in edges)
    S['layer_coverage'] = {l: v for l, v in (meta.get('layer_coverage') or {}).items() if l in LAYERS}
    S['identity_merge'] = meta.get('identity_merge') or {}
    S['engines'] = collections.Counter(e['engine'] for e in edges)

    # ---------------------------------------------------------------- topology
    comp = collections.Counter(n.get('component') for n in nodes if deg[n['id']])
    sizes = sorted(comp.values(), reverse=True)
    S['components'] = dict(sizes=sizes, giant=sizes[0], n_nonsingleton=len(sizes),
                           isolated=sum(1 for n in nodes if not deg[n['id']]))
    S['pos'] = {k: tuple(v) for k, v in pos.items()}
    S['nodes'], S['edges'], S['N'] = nodes, edges, N

    # ---------------------------------------------------------------- validation
    ev = collections.Counter()
    for e in edges:
        ip = e.get('evidence_in_passage')
        ev[(e['corpus'], 'found' if ip is True else 'not_found' if ip is False else 'unresolved')] += 1
    S['evidence_by_work'] = ev
    mat = collections.Counter()
    for e in edges:
        ip = e.get('evidence_in_passage')
        mat[('verbatim' if e.get('evidence_verbatim') else 'non_verbatim',
             'found' if ip is True else 'not_found' if ip is False else 'unresolved')] += 1
    S['verbatim_x_check'] = mat
    S['support'] = collections.Counter(e.get('n_support', 1) for e in edges)
    card = {p: v['card'] for p, v in onto['object_properties'].items()}
    outs = collections.defaultdict(set)
    for e in edges:
        if card.get(e['type'], '').endswith('..1'):
            outs[(e['type'], e['subject_id'])].add(e['object_id'])
    exc = collections.Counter(t for (t, _), objs in outs.items() if len(objs) > 1)
    S['cardinality_exceptions'] = exc
    S['integrity'] = qc.get('integrity', {})
    viol = 0
    for e in edges:
        p = onto['object_properties'][e['type']]
        if N[e['subject_id']]['cls'] != p['domain'] or N[e['object_id']]['cls'] != p['range']:
            viol += 1
    S['domain_range_violations'] = viol
    S['dangling'] = sum(1 for e in edges if e['subject_id'] not in N or e['object_id'] not in N)
    S['self_loops'] = sum(1 for e in edges if e['subject_id'] == e['object_id'])
    S['duplicates'] = len(edges) - len({(e['subject_id'], e['type'], e['object_id']) for e in edges})
    S['with_sentence'] = sum(1 for e in edges if e.get('source_sentence'))
    S['with_pid'] = sum(1 for e in edges if e.get('passage_id'))

    # ---------------------------------------------------------------- temporal coverage (dated physicians)
    life = []
    for n in nodes:
        if n['cls'] != 'Physician' or n['name'] not in PINYIN:
            continue
        a = n.get('attrs') or {}
        b, bc = _year(a.get('birth_year')); d, dc = _year(a.get('death_year'))
        if b and d:
            life.append(dict(zh=n['name'], py=PINYIN[n['name']], birth=b, death=d, circa=bc or dc,
                             rep=n['name'] in REPRESENTATIVE, deg=deg[n['id']]))
    S['lifespans'] = sorted(life, key=lambda r: (r['birth'], r['death']))

    # ---------------------------------------------------------------- example record (Fig. 1b)
    # A short case passage whose relations span five relation types and are all located verbatim.
    EX_PID, EX_OBJ = 'hlc0642c032', '京川贝'
    passage = next(p for p in cy['passages'] if p['pid'] == EX_PID)
    rels = [e for e in edges if e.get('passage_id') == EX_PID]
    S['example'] = dict(passage=passage, edges=rels, featured=next(e for e in rels if e['object_name'] == EX_OBJ),
                        cls={e['object_id']: N[e['object_id']]['cls'] for e in rels})
    S['meta'] = meta
    S['onto'] = onto
    return S


if __name__ == '__main__':
    S = load()
    print('works', [(w['short'], w['passages'], w['chars'], w['relations']) for w in S['works']])
    print('totals', S['corpus_totals'], 'nodes', S['n_nodes'], 'edges', S['n_edges'])
    print('cardinality exceptions', dict(S['cardinality_exceptions']), sum(S['cardinality_exceptions'].values()))
    print('violations', S['domain_range_violations'], 'dangling', S['dangling'], 'self', S['self_loops'],
          'dup', S['duplicates'])
    print('verbatim x check', dict(S['verbatim_x_check']))
    print('lifespans', len(S['lifespans']), [(r['py'], r['birth'], r['death'], r['rep']) for r in S['lifespans']])
    print('components', {k: v for k, v in S['components'].items() if k != 'sizes'})
