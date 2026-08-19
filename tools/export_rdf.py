#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/shaopai_kg.json 重建 RDF A-Box（Turtle），保持上游的具体化出处写法。"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
kg = json.loads((ROOT / 'data/shaopai_kg.json').read_text(encoding='utf-8'))
props = kg['ontology']['object_properties']

PRE = """@prefix dcmitype: <http://purl.org/dc/dcmitype/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix res: <https://w3id.org/shaopai/resource/> .
@prefix sp: <https://w3id.org/shaopai/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://w3id.org/shaopai/dataset> a dcmitype:Dataset ;
    dcterms:creator <https://impfai.github.io/> ;
    dcterms:publisher <https://impfai.github.io/> ;
    dcterms:source "《浙派中医丛书》专题系列·绍派伤寒（沈钦荣主编，2021）"@zh ;
    dcterms:title "绍派伤寒 知识图谱 实例数据"@zh .
"""

def lit(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        return str(v)
    s = str(v).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
    return f'"{s}"@zh'

out = [PRE]

# 每个节点的出边，按谓词聚合
by_subj = {}
for e in kg['edges']:
    by_subj.setdefault(e['subject_id'], {}).setdefault(e['type'], set()).add(e['object_id'])

for n in sorted(kg['nodes'], key=lambda x: x['id']):
    lines = [f'res:{n["id"]} a sp:{n["cls"]} ;', f'    rdfs:label {lit(n["name"])} ;']
    items = []
    for p, objs in sorted(by_subj.get(n['id'], {}).items()):
        if p not in props:
            continue
        tgt = sorted(objs)
        val = (',\n        '.join(f'res:{t}' for t in tgt))
        items.append(f'sp:{p} {val}')
    for k, v in sorted((n.get('attrs') or {}).items()):
        if v not in (None, '', []):
            items.append(f'sp:{k} {lit(v)}')
    if n.get('aliases'):
        items.append('sp:aliases ' + ', '.join(lit(a) for a in n['aliases']))
    items.append(f'sp:n_mentions {n.get("n_mentions", 0)}')
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
    fields = [
        ('sp:agreement', lit(e.get('agreement') or p.get('agreement', ''))),
        ('sp:chapterPath', lit(p.get('chapter_path', ''))),
        ('sp:engine', lit(e.get('engine') or p.get('engine', ''))),
        ('sp:evidenceVerbatim', 'true' if p.get('evidence_verbatim') else 'false'),
        ('sp:nSupport', str(e.get('n_support', 1))),
        ('sp:passageId', lit(p.get('passage_id', ''))),
        ('sp:sourceSentence', lit(p.get('source_sentence', ''))),
    ]
    for k, name in EXTRA:
        if e.get(k):
            fields.append((f'sp:{name}', lit(e[k])))
    fields.sort()
    for i, (k, v) in enumerate(fields):
        st.append(f'    {k} {v}' + (' ;' if i < len(fields) - 1 else ' .'))
    out.append('\n'.join(st) + '\n')

txt = '\n'.join(out)
(ROOT / 'data/shaopai_instances.ttl').write_text(txt, encoding='utf-8')
n_trip = txt.count(' ;') + txt.count(' .')
print(f'shaopai_instances.ttl 重建完成：{len(kg["nodes"])} 节点块 + {len(kg["edges"])} 具体化陈述，约 {n_trip:,} 三元组')
