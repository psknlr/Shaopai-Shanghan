#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/shaopai_kg.json 重建 Neo4j 导入用的 nodes.csv / edges.csv。"""
import json, csv, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_payload import components, load, layout_new

ROOT = Path(__file__).resolve().parent.parent
kg, pos, _ = load()
pos, _ = layout_new(kg, pos)
comp = components(kg)

NATTR = ['statement_zh', 'courtesy_name', 'birth_year', 'death_year', 'native_place',
         'author', 'year', 'topic', 'proposed_by', 'modality', 'descriptor',
         'channel', 'triple_burner', 'nature', 'source_work', 'attributed_to',
         'preparation', 'indication', 'physician', 'prescription', 'presentation',
         'action_type', 'note']
head = [':ID', 'name:string', 'aliases:string[]', ':LABEL', 'n_mentions:int',
        'x:float', 'y:float', 'component:int'] + [f'{a}:string' for a in NATTR]
with (ROOT / 'data/nodes.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(head)
    for n in kg['nodes']:
        xy = pos.get(n['id'], (None, None))
        at = n.get('attrs') or {}
        w.writerow([n['id'], n['name'], ';'.join(n.get('aliases') or []), n['cls'],
                    n.get('n_mentions', 0),
                    '' if xy[0] is None else round(xy[0], 5),
                    '' if xy[1] is None else round(xy[1], 5),
                    comp.get(n['id'], -1)] + [at.get(a, '') for a in NATTR])

EATTR = ['dose', 'dose_note', 'role', 'condition']
ehead = [':START_ID', ':END_ID', ':TYPE', 'n_support:int', 'source_sentence:string',
         'chapter_path:string', 'passage_id:string', 'evidence_verbatim:boolean',
         'engine:string', 'agreement:string'] + [f'{a}:string' for a in EATTR]
with (ROOT / 'data/edges.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(ehead)
    for e in kg['edges']:
        p = (e.get('provenance') or [{}])[0]
        w.writerow([e['subject_id'], e['object_id'], e['type'], e.get('n_support', 1),
                    p.get('source_sentence', ''), p.get('chapter_path', ''),
                    p.get('passage_id', ''),
                    'true' if p.get('evidence_verbatim') else 'false',
                    e.get('engine') or p.get('engine', ''),
                    e.get('agreement') or p.get('agreement', '')] +
                   [e.get(a, '') for a in EATTR])
print(f'nodes.csv {len(kg["nodes"])} 行   edges.csv {len(kg["edges"])} 行')
