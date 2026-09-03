#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/shaopai_kg.json 重建 Neo4j 导入用的 nodes.csv / edges.csv，以及 load_neo4j.cypher。

  python3 tools/export_csv.py
"""
import csv, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_payload import components, load, layout_new

ROOT = Path(__file__).resolve().parent.parent
kg, pos, _ = load()
pos, _ = layout_new(kg, pos)
comp = components(kg)
onto = kg['ontology']

# 节点属性列：本体声明的属性中在数据里实际出现过的，按类的顺序去重
observed = collections.defaultdict(set)
for n in kg['nodes']:
    for k, v in (n.get('attrs') or {}).items():
        if v not in (None, '', []):
            observed[n['cls']].add(k)
NATTR = []
for c, spec in onto['classes'].items():
    for a in spec.get('attrs', []):
        if a in observed[c] and a not in NATTR:
            NATTR.append(a)
for c in observed:                       # 未声明却出现的属性也不丢
    for a in sorted(observed[c]):
        if a not in NATTR:
            NATTR.append(a)

head = [':ID', 'name:string', 'aliases:string[]', ':LABEL', 'n_mentions:int', 'n_provenance:int',
        'x:float', 'y:float', 'component:int'] + [f'{a}:string' for a in NATTR]
with (ROOT / 'data/nodes.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(head)
    for n in kg['nodes']:
        xy = pos.get(n['id'], (None, None))
        at = n.get('attrs') or {}
        w.writerow([n['id'], n['name'], ';'.join(n.get('aliases') or []), n['cls'],
                    n.get('n_mentions', 0), n.get('n_provenance', len(n.get('provenance') or [])),
                    '' if xy[0] is None else round(xy[0], 5),
                    '' if xy[1] is None else round(xy[1], 5),
                    comp.get(n['id'], -1)] + [at.get(a, '') for a in NATTR])

EATTR = ['dose', 'dose_note', 'role', 'condition']
ehead = [':START_ID', ':END_ID', ':TYPE', 'n_support:int', 'layer:string', 'source_sentence:string',
         'chapter_path:string', 'passage_id:string', 'evidence_verbatim:boolean',
         'engine:string', 'agreement:string'] + [f'{a}:string' for a in EATTR]
with (ROOT / 'data/edges.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(ehead)
    for e in kg['edges']:
        p = (e.get('provenance') or [{}])[0]
        w.writerow([e['subject_id'], e['object_id'], e['type'], e.get('n_support', 1), e.get('layer', ''),
                    e.get('source_sentence') or p.get('source_sentence', ''),
                    e.get('chapter_path') or p.get('chapter_path', ''),
                    e.get('passage_id') or p.get('passage_id', ''),
                    'true' if e.get('evidence_verbatim', p.get('evidence_verbatim')) else 'false',
                    e.get('engine') or p.get('engine', ''),
                    e.get('agreement') or p.get('agreement', '')] +
                   [e.get(a, '') for a in EATTR])

# ---------------------------------------------------------------- load_neo4j.cypher
populated = collections.Counter(n['cls'] for n in kg['nodes'])
used_types = [t for t, _ in collections.Counter(e['type'] for e in kg['edges']).most_common()]
L = ['// 绍派伤寒 · 越医知识图谱 — Neo4j loader（由 tools/export_csv.py 生成）',
     '// 用法：把 nodes.csv 与 edges.csv 放入 DBMS 的 import/ 目录，然后运行本文件。',
     f'// 节点 {len(kg["nodes"]):,} · 关系 {len(kg["edges"]):,} · 本体 {onto["version"]}',
     '', '// ---------- 约束与索引 ----------']
for c in onto['classes']:
    L.append(f'CREATE CONSTRAINT {c.lower()}_id IF NOT EXISTS FOR (n:{c}) REQUIRE n.id IS UNIQUE;')
for c in populated:
    L.append(f'CREATE INDEX {c.lower()}_name IF NOT EXISTS FOR (n:{c}) ON (n.name);')
L += ['CREATE INDEX diagnosticsign_modality IF NOT EXISTS FOR (n:DiagnosticSign) ON (n.modality);',
      'CREATE INDEX doctrine_topic IF NOT EXISTS FOR (n:Doctrine) ON (n.topic);',
      'CREATE INDEX caserecord_physician IF NOT EXISTS FOR (n:CaseRecord) ON (n.physician);',
      '', '// ---------- 节点（按标签分批）----------']
for c in populated:
    attrs = [a for a in onto['classes'][c].get('attrs', []) if a in observed[c]]
    attrs += sorted(a for a in observed[c] if a not in attrs)
    sets = ["n.name = row['name:string']",
            "n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END",
            "n.n_mentions = toInteger(row['n_mentions:int'])",
            "n.component = toInteger(row['component:int'])",
            "n.x = toFloat(row['x:float'])", "n.y = toFloat(row['y:float'])"]
    sets += [f"n.{a} = CASE WHEN row['{a}:string'] = '' THEN null ELSE row['{a}:string'] END" for a in attrs]
    L += ["LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row",
          'CALL {', '  WITH row', f"  WITH row WHERE row[':LABEL'] = '{c}'",
          f"  MERGE (n:{c} {{id: row[':ID']}})",
          '  SET ' + ',\n      '.join(sets),
          '} IN TRANSACTIONS OF 1000 ROWS;', '']
L += ['// ---------- 关系（APOC）----------',
      "LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row", 'CALL {', '  WITH row',
      "  MATCH (s {id: row[':START_ID']}), (o {id: row[':END_ID']})",
      "  CALL apoc.merge.relationship(s, row[':TYPE'], {}, {",
      "    n_support: toInteger(row['n_support:int']),",
      "    layer: row['layer:string'],",
      "    source_sentence: row['source_sentence:string'],",
      "    chapter_path: row['chapter_path:string'],",
      "    passage_id: row['passage_id:string'],",
      "    evidence_verbatim: row['evidence_verbatim:boolean'] = 'true',",
      "    engine: row['engine:string'],",
      "    agreement: row['agreement:string']",
      '  }, o) YIELD rel', '  RETURN rel', '} IN TRANSACTIONS OF 1000 ROWS;', '',
      '// ---------- 关系（无 APOC 时的逐类型替代：去掉每行开头的 "// " 后运行）----------']
for t in used_types:
    d, r = onto['object_properties'][t]['domain'], onto['object_properties'][t]['range']
    L += [f"// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = '{t}'",
          f"// MATCH (s:{d} {{id: row[':START_ID']}}), (o:{r} {{id: row[':END_ID']}}) MERGE (s)-[rel:{t}]->(o)",
          "// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], "
          "rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], "
          "rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', "
          "rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];"]
(ROOT / 'data/load_neo4j.cypher').write_text('\n'.join(L) + '\n', encoding='utf-8')

print(f'nodes.csv {len(kg["nodes"]):,} 行（{len(head)} 列）  edges.csv {len(kg["edges"]):,} 行  '
      f'load_neo4j.cypher {len(populated)} 类 / {len(used_types)} 种关系')
