#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/shaopai_kg.json 重建 RDF A-Box（Turtle），保持上游的具体化出处写法。

  python3 tools/export_rdf.py

每个节点一个资源块（类型、标签、属性、别名、出边），每条关系一个 rdf:Statement 具体化块承载出处。
三元组数在生成时逐条累计（不依赖 rdflib）。发布者的 3 条 FOAF 三元组与 T-Box 文件重复断言，
使两个文件各自独立可用，合并加载时自动去重。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
kg = json.loads((ROOT / 'data/shaopai_kg.json').read_text(encoding='utf-8'))
props = kg['ontology']['object_properties']
meta = kg['meta']

PRE = """@prefix dcmitype: <http://purl.org/dc/dcmitype/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix res: <https://w3id.org/shaopai/resource/> .
@prefix sp: <https://w3id.org/shaopai/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""


def lit(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        return str(v)
    s = str(v).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
    return f'"{s}"@zh'


out, n_triples = [PRE], 0
corpora = meta.get('corpora') or [meta.get('source_book', '')]
ds = ['<https://w3id.org/shaopai/dataset> a dcmitype:Dataset ;',
      '    dcterms:creator <https://impfai.github.io/> ;',
      '    dcterms:publisher <https://impfai.github.io/> ;']
ds += [f'    dcterms:source {lit(c)} ;' for c in corpora]
ds += [f'    dcterms:title {lit("绍派伤寒 · 越医知识图谱 实例数据")} ;',
       f'    dcterms:hasVersion {lit(kg["ontology"]["version"])} .']
out.append('\n'.join(ds) + '\n'); n_triples += 5 + len(corpora)
out.append('<https://impfai.github.io/> a foaf:Organization ;\n'
           f'    foaf:name {lit(meta.get("publisher", "医哲未来人工智能研究院 (IMPFAI)"))} ;\n'
           '    foaf:homepage <https://impfai.github.io/> .\n'); n_triples += 3

# 每个节点的出边，按谓词聚合
by_subj = {}
for e in kg['edges']:
    by_subj.setdefault(e['subject_id'], {}).setdefault(e['type'], set()).add(e['object_id'])

for n in sorted(kg['nodes'], key=lambda x: x['id']):
    lines = [f'res:{n["id"]} a sp:{n["cls"]} ;', f'    rdfs:label {lit(n["name"])} ;']
    n_triples += 2
    items = []
    for p, objs in sorted(by_subj.get(n['id'], {}).items()):
        if p not in props:
            continue
        tgt = sorted(objs)
        items.append(f'sp:{p} ' + ',\n        '.join(f'res:{t}' for t in tgt))
        n_triples += len(tgt)
    for k, v in sorted((n.get('attrs') or {}).items()):
        if v not in (None, '', []):
            items.append(f'sp:{k} {lit(v)}'); n_triples += 1
    if n.get('aliases'):
        items.append('sp:aliases ' + ', '.join(lit(a) for a in n['aliases'])); n_triples += len(n['aliases'])
    items.append(f'sp:n_mentions {n.get("n_mentions", 0)}'); n_triples += 1
    for i, it in enumerate(items):
        lines.append(f'    {it}' + (' ;' if i < len(items) - 1 else ' .'))
    out.append('\n'.join(lines) + '\n')

# 具体化出处
EXTRA = [('dose', 'dose'), ('dose_note', 'doseNote'), ('role', 'ingredientRoleValue'),
         ('condition', 'modificationCondition')]
for e in sorted(kg['edges'], key=lambda x: (x['type'], x['subject_id'], x['object_id'])):
    p = (e.get('provenance') or [{}])[0]
    st = ['[] a rdf:Statement ;',
          f'    rdf:object res:{e["object_id"]} ;',
          f'    rdf:predicate sp:{e["type"]} ;',
          f'    rdf:subject res:{e["subject_id"]} ;']
    n_triples += 4
    fields = [
        ('sp:agreement', lit(e.get('agreement') or p.get('agreement', ''))),
        ('sp:chapterPath', lit(e.get('chapter_path') or p.get('chapter_path', ''))),
        ('sp:engine', lit(e.get('engine') or p.get('engine', ''))),
        ('sp:evidenceVerbatim', 'true' if e.get('evidence_verbatim', p.get('evidence_verbatim')) else 'false'),
        ('sp:nSupport', str(e.get('n_support', 1))),
        ('sp:sourceSentence', lit(e.get('source_sentence') or p.get('source_sentence', ''))),
    ]
    if e.get('layer'):
        fields.append(('sp:layer', lit(e['layer'])))
    if e.get('corpus'):
        fields.append(('sp:corpus', lit(e['corpus'])))
    pid = e.get('passage_id') or p.get('passage_id')
    if pid:
        fields.append(('sp:passageId', lit(pid)))
    for k, name in EXTRA:
        if e.get(k):
            fields.append((f'sp:{name}', lit(e[k])))
    fields.sort()
    n_triples += len(fields)
    for i, (k, v) in enumerate(fields):
        st.append(f'    {k} {v}' + (' ;' if i < len(fields) - 1 else ' .'))
    out.append('\n'.join(st) + '\n')

txt = '\n'.join(out)
(ROOT / 'data/shaopai_instances.ttl').write_text(txt, encoding='utf-8')
msg = (f'shaopai_instances.ttl 重建完成：{len(kg["nodes"]):,} 节点块 + {len(kg["edges"]):,} 具体化陈述，'
       f'{n_triples:,} 三元组（生成时累计）')
try:                              # 有 rdflib 就再报实测三元组数
    import rdflib
    g = rdflib.Graph(); g.parse(str(ROOT / 'data/shaopai_instances.ttl'), format='turtle')
    msg += f'，{len(g):,}（rdflib 实测）'
except ImportError:
    pass
print(msg)
