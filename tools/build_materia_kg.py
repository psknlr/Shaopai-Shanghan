#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把抽取到的本草方剂层并入 data/shaopai_kg.json。

与谱系层、诊法层不同，本层由**确定性解析器**产出（engine=rule-parser-v1）：
同样的原书输入必然得到同样的图谱，不依赖模型采样。
"""
import json, re, hashlib, collections, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SC = Path('/tmp/claude-0/-home-user-Shaopai-Shanghan/33fc25dd-a3aa-5e47-893c-d2c888848230/scratchpad')
ENGINE, AGREE = 'rule-parser-v1', 'deterministic_parse'

kg = json.loads((ROOT / 'data/shaopai_kg.json').read_text(encoding='utf-8'))
raw = json.loads((SC / 'book/materia_raw.json').read_text(encoding='utf-8'))
onto = kg['ontology']

by_cls = collections.defaultdict(dict)          # cls -> name -> node
for n in kg['nodes']:
    by_cls[n['cls']].setdefault(n['name'], n)
existing_ids = {n['id'] for n in kg['nodes']}

def nid(cls, name):
    h = hashlib.md5(f'{cls}|{name}|materia'.encode()).hexdigest()[:10]
    i = f'{cls}_{h}'
    assert i not in existing_ids or by_cls[cls].get(name, {}).get('id') == i, f'ID 冲突 {i}'
    return i

new_nodes, new_edges = {}, []

def node(cls, name, attrs, prov):
    """新建或合并节点；已存在于原图谱者直接复用，不覆盖其属性。"""
    if name in by_cls[cls]:
        return by_cls[cls][name]['id']
    if (cls, name) in new_nodes:
        n = new_nodes[(cls, name)]
        n['n_mentions'] += 1
        if prov and not any(p['passage_id'] == prov['passage_id'] for p in n['provenance']):
            n['provenance'].append(prov)
        for k, v in attrs.items():
            n['attrs'].setdefault(k, v)
        return n['id']
    n = {'id': nid(cls, name), 'cls': cls, 'name': name, 'aliases': [],
         'attrs': {k: v for k, v in attrs.items() if v},
         'provenance': [prov] if prov else [], 'n_mentions': 1}
    new_nodes[(cls, name)] = n
    return n['id']

def prov_of(pid, cp, sent, verbatim=True):
    return {'passage_id': pid, 'chapter_path': cp, 'source_sentence': sent[:400],
            'evidence_verbatim': bool(verbatim), 'engine': ENGINE, 'agreement': AGREE}

def edge(t, s, o, sn, on, prov, **extra):
    e = {'type': t, 'subject_id': s, 'object_id': o, 'subject_name': sn, 'object_name': on,
         'n_support': 1, 'provenance': [prov], 'passage_id': prov['passage_id'],
         'chapter_path': prov['chapter_path'], 'engine': ENGINE, 'agreement': AGREE}
    e.update({k: v for k, v in extra.items() if v})
    new_edges.append(e)

# ---------- 书名归一：《通俗伤寒论·发汗剂》→ 通俗伤寒论 ----------
def work_of(title):
    if not title:
        return None
    base = re.split(r'[·•・]', title)[0].strip()
    for cand in (title, base):
        if cand in by_cls['Work']:
            return by_cls['Work'][cand]['id'], cand
    return None

def physician_of(chapter_path):
    parts = chapter_path.split(' / ')
    if len(parts) > 1:
        nm = parts[1].replace(' ', '')
        for cand in (nm, {'章楠': '章虚谷'}.get(nm, nm)):
            if cand in by_cls['Physician']:
                return by_cls['Physician'][cand]['id'], cand
    return None

# ---------- 方剂 ----------
PAT_NAMES = sorted(by_cls['Pattern'], key=len, reverse=True)

for f in raw['formulas']:
    pid, cp, sent = f['pid'], f['chapter_path'], f['sentence']
    ph = physician_of(cp)
    wk = work_of(f['source_work'])
    fattrs = {'source_work': f['source_work'], 'attributed_to': f['attrib'] or (ph[1] if ph else ''),
              'preparation': f['preparation'][:200], 'indication': f['indication'][:200]}
    fid = node('Formula', f['name'], fattrs, prov_of(pid, cp, sent))

    for r in f['ingredients']:
        hid = node('Herb', r['herb'], {}, prov_of(pid, cp, sent))
        edge('hasIngredient', fid, hid, f['name'], r['herb'], prov_of(pid, cp, sent),
             dose=r['dose'], dose_note=r['note'])
    for herb, (role, rtext, rpid) in (f.get('roles') or {}).items():
        hid = node('Herb', herb, {}, prov_of(rpid, cp, rtext))
        edge('ingredientRole', fid, hid, f['name'], herb,
             prov_of(rpid, cp, rtext), role=role)
    for m in f.get('mods') or []:
        hid = node('Herb', m['herb'], {}, prov_of(pid, cp, sent))
        edge('addHerbIf' if m['kind'] == 'add' else 'removeHerbIf',
             fid, hid, f['name'], m['herb'], prov_of(pid, cp, f['mod_text'][:400] or sent),
             condition=m['cond'])
    if wk:
        edge('derivesFrom', fid, wk[0], f['name'], wk[1], prov_of(pid, cp, sent))
    if f['principle']:
        tid = node('TreatmentPrinciple', f['principle'], {'action_type': ''},
                   prov_of(pid, cp, sent))
        edge('principleRealizedBy', tid, fid, f['principle'], f['name'], prov_of(pid, cp, sent))
    # 方剂主治 → 已有证候（连通谱系层与诊法层的桥）
    hay = f['indication'] + ' ' + f['sentence']
    for pn in PAT_NAMES:
        if len(pn) >= 3 and pn in hay:
            edge('formulaTreats', fid, by_cls['Pattern'][pn]['id'], f['name'], pn,
                 prov_of(pid, cp, hay[:400]))
            break

# ---------- 医案 ----------
for c in raw['cases']:
    pid, cp, sent = c['pid'], c['chapter_path'], c['sentence']
    ph = physician_of(cp)
    presc = '、'.join(f"{r['herb']}{r['dose']}" for r in c['ingredients'] if r['herb'])
    cid = node('CaseRecord', c['name'], {'physician': ph[1] if ph else '',
                                         'prescription': presc[:300],
                                         'presentation': sent[:200]},
               prov_of(pid, cp, sent))
    if ph:
        edge('caseByPhysician', cid, ph[0], c['name'], ph[1], prov_of(pid, cp, sent))

# ---------- 校验 ----------
allnodes = {n['id']: n for n in kg['nodes']}
allnodes.update({n['id']: n for n in new_nodes.values()})
props = onto['object_properties']
bad = []
for e in new_edges:
    p = props.get(e['type'])
    s, o = allnodes.get(e['subject_id']), allnodes.get(e['object_id'])
    if not p or not s or not o:
        bad.append(('悬空/未知属性', e['type'], e['subject_name'], e['object_name'])); continue
    if s['cls'] != p['domain'] or o['cls'] != p['range']:
        bad.append(('定义域/值域', e['type'], s['cls'], o['cls']))
seen = set()
dedup = []
for e in new_edges:
    k = (e['type'], e['subject_id'], e['object_id'])
    if k in seen:
        continue
    seen.add(k); dedup.append(e)

cc = collections.Counter(n['cls'] for n in new_nodes.values())
ec = collections.Counter(e['type'] for e in dedup)
print('新增节点:', dict(cc), '合计', len(new_nodes))
print('新增关系:', dict(ec), '合计', len(dedup), f'（去重前 {len(new_edges)}）')
print('本体违例:', bad if bad else '0 ✓')

if '--write' in sys.argv:
    kg['nodes'].extend(new_nodes.values())
    kg['edges'].extend(dedup)
    m = kg['meta']
    m['layers_extracted'] = ['lineage', 'diagnostic', 'materia']
    m['layers_pending'] = ['pattern']
    m['engines'] = list(dict.fromkeys(m.get('engines', []) + ['rule-parser-v1 (materia)']))
    m['n_nodes'], m['n_edges'] = len(kg['nodes']), len(kg['edges'])
    m['note'] = ('本草方剂层由确定性解析器自原书「方剂选录」「医案选按」等章节抽取，'
                 '同一输入必得同一结果；证候层仍待抽取。')
    (ROOT / 'data/shaopai_kg.json').write_text(
        json.dumps(kg, ensure_ascii=False), encoding='utf-8')
    print(f'已写入 → 节点 {m["n_nodes"]}  关系 {m["n_edges"]}')
