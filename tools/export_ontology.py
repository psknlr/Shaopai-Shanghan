#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/shaopai_kg.json 的 ontology 段生成 OWL T-Box（Turtle）：data/shaopai_ontology.ttl。

  python3 tools/export_ontology.py

类与对象属性带中英双语标签，对象属性带定义域、值域与基数注记；
各类声明的属性导出为 owl:DatatypeProperty；出处字段导出为 owl:AnnotationProperty。
发布者的 3 条 FOAF 三元组与 A-Box 重复断言（两文件各自独立可用，合并加载时去重）。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
kg = json.loads((ROOT / 'data/shaopai_kg.json').read_text(encoding='utf-8'))
onto, meta = kg['ontology'], kg['meta']


def lit(v, lang='zh'):
    s = str(v).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{s}"@{lang}' if lang else f'"{s}"'


PROV_PROPS = {  # A-Box 具体化陈述里用到的注记属性
    'sourceSentence': ('原文', 'verbatim source sentence backing the assertion'),
    'chapterPath': ('章节路径', 'chapter path of the source passage'),
    'passageId': ('段落编号', 'passage id in the segmented corpus'),
    'evidenceVerbatim': ('证据逐字', 'whether the evidence span is a verbatim substring of the passage'),
    'engine': ('抽取引擎', 'extraction engine'),
    'agreement': ('引擎一致性', 'cross-engine agreement status'),
    'nSupport': ('支撑次数', 'number of independent supporting passages'),
    'layer': ('抽取层', 'extraction layer'),
    'n_mentions': ('提及次数', 'number of mentions of the entity in the corpora'),
    'aliases': ('别名', 'alias'),
}

out, n = [], 0
out.append('''@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sp: <https://w3id.org/shaopai/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
''')
hdr = ['<https://w3id.org/shaopai/ontology> a owl:Ontology ;',
       f'    owl:versionInfo {lit(onto["version"], None)} ;',
       f'    rdfs:label {lit("绍派伤寒 · 越医知识图谱本体")}, {lit("Shaoxing Cold-Damage & Yue-Medicine KG Ontology", "en")} ;',
       '    dcterms:creator <https://impfai.github.io/> ;',
       '    dcterms:publisher <https://impfai.github.io/> .']
out.append('\n'.join(hdr) + '\n'); n += 6
out.append('<https://impfai.github.io/> a foaf:Organization ;\n'
           f'    foaf:name {lit(meta.get("publisher", "医哲未来人工智能研究院 (IMPFAI)"))} ;\n'
           '    foaf:homepage <https://impfai.github.io/> .\n'); n += 3

out.append('# ---------- Classes ----------')
for c, spec in onto['classes'].items():
    lines = [f'sp:{c} a owl:Class ;', f'    rdfs:label {lit(c, "en")}, {lit(spec["zh"])} ;',
             '    rdfs:isDefinedBy <https://w3id.org/shaopai/ontology> .']
    out.append('\n'.join(lines) + '\n'); n += 4

out.append('# ---------- Object properties ----------')
for p, spec in onto['object_properties'].items():
    lines = [f'sp:{p} a owl:ObjectProperty ;',
             f'    rdfs:label {lit(p, "en")}, {lit(spec["zh"])} ;',
             f'    rdfs:domain sp:{spec["domain"]} ;', f'    rdfs:range sp:{spec["range"]} ;',
             f'    sp:cardinality {lit(spec["card"], None)} ;',
             '    rdfs:isDefinedBy <https://w3id.org/shaopai/ontology> .']
    if spec['card'].endswith('..1'):
        lines.insert(1, '    a owl:FunctionalProperty ;'); n += 1
    out.append('\n'.join(lines) + '\n'); n += 7

out.append('# ---------- Datatype properties (entity attributes) ----------')
dom = {}
for c, spec in onto['classes'].items():
    for a in spec.get('attrs', []):
        dom.setdefault(a, []).append(c)
for a, cs in dom.items():
    lines = [f'sp:{a} a owl:DatatypeProperty ;', f'    rdfs:label {lit(a, "en")} ;']
    if len(cs) == 1:
        lines.append(f'    rdfs:domain sp:{cs[0]} ;'); n += 1
    else:
        lines.append('    rdfs:domain [ a owl:Class ; owl:unionOf ( ' + ' '.join(f'sp:{c}' for c in cs) + ' ) ] ;')
        n += 3 + len(cs) * 2
    lines.append('    rdfs:range xsd:string .')
    out.append('\n'.join(lines) + '\n'); n += 3
mod = onto['classes'].get('DiagnosticSign', {}).get('modalities')
if mod:
    out.append('sp:modality rdfs:comment ' + lit('受控值：' + ' / '.join(mod)) + ' .\n'); n += 1

out.append('# ---------- Annotation properties (provenance, on rdf:Statement) ----------')
out.append('sp:cardinality a owl:AnnotationProperty ; rdfs:label ' + lit("cardinality", "en") + ' .\n'); n += 2
for p, (zh, en) in PROV_PROPS.items():
    out.append(f'sp:{p} a owl:AnnotationProperty ;\n    rdfs:label {lit(p, "en")}, {lit(zh)} ;\n'
               f'    rdfs:comment {lit(en, "en")} .\n'); n += 4

(ROOT / 'data/shaopai_ontology.ttl').write_text('\n'.join(out), encoding='utf-8')
print(f'shaopai_ontology.ttl：{len(onto["classes"])} 类 · {len(onto["object_properties"])} 对象属性 · '
      f'{len(dom)} 数据属性 · 约 {n:,} 三元组')
