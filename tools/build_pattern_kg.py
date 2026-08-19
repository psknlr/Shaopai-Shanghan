#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证候层（第四层）：病证 · 证候 · 治法，及其相互关系。

与本草层同为确定性解析（engine=rule-parser-v1）。素材集中在几处
原书自带列举的段落，逐条附原文与段落编号。

刻意不建 Symptom 类：候选症状 17/18 已是 DiagnosticSign 节点
（modality=问诊/望诊 者 672 个），另立一类会重复并割裂图谱。
"""
import json, re, hashlib, collections, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE, AGREE = 'rule-parser-v1', 'deterministic_parse'

kg = json.loads((ROOT / 'data/shaopai_kg.json').read_text(encoding='utf-8'))
corpus = json.loads((ROOT / 'data/corpus_shaopai.json').read_text(encoding='utf-8'))
P = {p['id']: p for p in corpus['passages']}
onto = kg['ontology']

# ---- 本体扩展 1.0.0 → 1.1.0 ----
# 原书明言「伤寒本证…分小伤寒、大伤寒…」，但 1.0.0 没有任何病证之间的关系，
# 51 个病证只能成为孤点。补一条 subDiseaseOf，其余一字不动。
if 'subDiseaseOf' not in onto['object_properties']:
    onto['object_properties']['subDiseaseOf'] = {
        'zh': '子病证', 'domain': 'Disease', 'range': 'Disease', 'card': '0..1'}
    onto['version'] = '1.1.0'
# 1.1.0 → 1.2.0：病证与图谱其余部分之间原本没有任何通路，
# 57 个伤寒病证只能自成孤岛。补一条「病证论者」，把病证系回论述它的医家。
if 'describedBy' not in onto['object_properties']:
    onto['object_properties']['describedBy'] = {
        'zh': '病证论者', 'domain': 'Disease', 'range': 'Physician', 'card': '0..*'}
    onto['version'] = '1.2.0'

by_cls = collections.defaultdict(dict)
for n in kg['nodes']:
    by_cls[n['cls']].setdefault(n['name'], n)
existing_ids = {n['id'] for n in kg['nodes']}
new_nodes, new_edges = {}, []

def nid(cls, name):
    return f'{cls}_{hashlib.md5(f"{cls}|{name}|pattern".encode()).hexdigest()[:10]}'

def prov(pid, sent, verbatim=True):
    p = P.get(pid, {})
    return {'passage_id': pid, 'chapter_path': p.get('chapter_path', ''),
            'source_sentence': sent[:400], 'evidence_verbatim': bool(verbatim),
            'engine': ENGINE, 'agreement': AGREE}

def physician_of(chapter_path):
    parts = chapter_path.split(' / ')
    if len(parts) > 1:
        nm = parts[1].replace(' ', '')
        nm = {'章楠': '章虚谷'}.get(nm, nm)
        if nm in by_cls['Physician']:
            return by_cls['Physician'][nm]['id'], nm
    return None


def node(cls, name, attrs, pv):
    if name in by_cls[cls]:
        n = by_cls[cls][name]
        for k, v in attrs.items():
            if v and not (n.get('attrs') or {}).get(k):
                n.setdefault('attrs', {})[k] = v
        return n['id']
    key = (cls, name)
    if key in new_nodes:
        n = new_nodes[key]
        n['n_mentions'] += 1
        if not any(x['passage_id'] == pv['passage_id'] for x in n['provenance']):
            n['provenance'].append(pv)
        for k, v in attrs.items():
            if v:
                n['attrs'].setdefault(k, v)
        return n['id']
    i = nid(cls, name)
    assert i not in existing_ids, f'ID 冲突 {i}'
    n = {'id': i, 'cls': cls, 'name': name, 'aliases': [],
         'attrs': {k: v for k, v in attrs.items() if v},
         'provenance': [pv], 'n_mentions': 1}
    new_nodes[key] = n
    return i

def edge(t, s, o, sn, on, pv):
    new_edges.append({'type': t, 'subject_id': s, 'object_id': o,
                      'subject_name': sn, 'object_name': on, 'n_support': 1,
                      'provenance': [pv], 'passage_id': pv['passage_id'],
                      'chapter_path': pv['chapter_path'],
                      'engine': ENGINE, 'agreement': AGREE})

# ============ 一、病证分类（原书逐条列举，并自报条数）============
TAXONOMY = [
    ('b00436', '伤寒本证', '受寒而致病者也',
     ['小伤寒', '大伤寒', '两感伤寒', '伏气伤寒', '阴证伤寒'], 5),
    ('b00437', '伤寒兼证', '或寒邪兼他邪，或他邪兼寒邪，二邪兼发者也',
     ['伤寒兼风', '伤寒兼湿', '伤寒兼痧', '伤寒兼疟', '伤寒兼疫', '风温伤寒', '风湿伤寒',
      '湿温伤寒', '春温伤寒', '热证伤寒', '暑湿伤寒', '伏暑伤寒', '秋燥伤寒', '冬温伤寒',
      '大头伤寒', '黄耳伤寒', '赤隔伤寒', '发斑伤寒', '发狂伤寒', '漏底伤寒', '脱脚伤寒'], 21),
    ('b00438', '伤寒夹证', '其病内外夹发，较兼证尤为难治',
     ['夹食伤寒', '夹痰伤寒', '夹饮伤寒', '夹血伤寒', '夹阴伤寒', '夹哮伤寒', '夹痞伤寒',
      '夹痛伤寒', '夹胀伤寒', '夹泻伤寒', '夹痢伤寒', '夹疝伤寒', '夹痨伤寒', '临经伤寒',
      '妊娠伤寒', '产后伤寒'], 16),
    ('b00439', '伤寒坏证', '四大重证', ['转痉', '转厥', '转闭', '转脱'], 4),
    ('b00440', '伤寒复证', '五大难证', ['劳复', '食复', '房复', '感复', '怒复'], 5),
]
tax_report = []
ROOT_SENT = '伤寒为外感百病之总名'
# 「伤寒为外感百病之总名」多处出现，优先取落在某位医家章节内的那处，
# 这样根节点也能系到论者（张景岳）
_cands = [i for i, p in P.items() if ROOT_SENT in p['text']]
root_pid = next((i for i in _cands if physician_of(P[i]['chapter_path'])), _cands[0] if _cands else 'b00436')
rid = node('Disease', '伤寒', {'category': '总名', 'note': ROOT_SENT},
           prov(root_pid, P[root_pid]['text'], ROOT_SENT in P[root_pid]['text']))
for pid, cat, gloss, members, stated in TAXONOMY:
    sent = P[pid]['text']
    miss = [m for m in members if m not in sent]
    tax_report.append((cat, len(members), stated, miss))
    pv = prov(pid, sent)
    cid = node('Disease', cat, {'category': '《通俗伤寒论》病证分类', 'note': gloss}, pv)
    edge('subDiseaseOf', cid, rid, cat, '伤寒', pv)
    for m in members:
        mid = node('Disease', m, {'category': cat}, pv)
        edge('subDiseaseOf', mid, cid, m, cat, pv)

# ============ 二、六淫正病 ============
LIUYIN = ['风病', '寒病', '暑病', '湿病', '燥病', '火病']
sent628 = P['b00628']['text']
for d in LIUYIN:
    node('Disease', d, {'category': '六淫正病'}, prov('b00628', sent628))

# 暑病子病（原文「名曰」句）
SUB_SHU = [('暑湿', '暑必夹湿，名曰暑湿'), ('暑秽', '亦多夹秽，名曰暑秽，俗曰热痧'),
           ('暑风', '炎风如箭，名曰暑风'), ('暑厥', '病多晕厥，名曰暑厥'),
           ('暑瘵', '亦多咳血，名曰暑瘵')]
s634 = P['b00634']['text']
shu_id = node('Disease', '暑病', {'category': '六淫正病'}, prov('b00628', sent628))
for nm, ev in SUB_SHU:
    ok = ev in s634
    pv = prov('b00634', ev if ok else s634[:300], ok)
    edge('subDiseaseOf', node('Disease', nm, {'category': '暑病'}, pv), shu_id, nm, '暑病', pv)

# ============ 三、证候（新增）与治法 ============
VERB2NAME = {'汗': '汗法', '和': '和法', '下': '下法', '温': '温法', '补': '补法',
             '清': '清法', '散': '散法', '熄': '熄法', '开': '开法', '发': '发法',
             '泻': '泻法', '引': '引法', '宣': '宣法', '润': '润法', '滋': '滋法',
             '涩': '涩法', '通': '通法', '吐': '吐法', '消': '消法', '降': '降法',
             '疏': '疏法', '凉': '凉法'}
LEAD = re.compile(r'^(?:除|惟|他如|故|若|如|凡|其|则|又|且|治|须|辨|为|而|之|以)')
# 证候名须落在病邪 / 病机字上，滤掉「宜汗」「分际最」这类误截
TAIL_OK = re.compile(r'[火寒湿燥风热暑结瘀痰虚实毒]$')

def clean_subject(s):
    s = s.strip()
    for _ in range(6):
        t = LEAD.sub('', s)
        if t == s:
            break
        s = t
    if not (2 <= len(s) <= 6) or '宜' in s or not TAIL_OK.search(s):
        return ''
    return s

# 3a 六经宜法（六经用药法）
SIX = re.compile(r'([太少厥][阳阴]|阳明)宜([汗和下温补清])')
for pid in ['b00612', 'b00614', 'b00615', 'b00616', 'b00617', 'b00618']:
    t = P[pid]['text']
    for m in SIX.finditer(t):
        chan, v = m.group(1), m.group(2)
        if chan not in by_cls['Pattern']:
            continue
        tp = VERB2NAME[v]
        pv = prov(pid, t)
        tid = node('TreatmentPrinciple', tp, {'action_type': '六经治法'}, pv)
        edge('treatedByPrinciple', by_cls['Pattern'][chan]['id'], tid, chan, tp, pv)

# 3b 治则总纲（b00494 / b00662 / b00512 / b00642 / b00636）
GEN = re.compile(r'([一-鿿]{1,6})宜([汗和下温补清散熄开发泻引宣润滋涩通吐消降疏凉])')
for pid in ['b00494', 'b00662', 'b00512', 'b00642', 'b00636', 'b00468']:
    t = P[pid]['text']
    for m in GEN.finditer(t):
        subj, v = clean_subject(m.group(1)), m.group(2)
        if not subj or subj in ('六经', '治风'):
            continue
        tp = VERB2NAME[v]
        pv = prov(pid, t)
        sid = node('Pattern', subj, {'nature': ''}, pv)
        tid = node('TreatmentPrinciple', tp, {'action_type': '六淫治则'}, pv)
        edge('treatedByPrinciple', sid, tid, subj, tp, pv)

# 3c 何廉臣下法七分：证候 → 治法 → 方剂
DOWN = re.compile(r'([一-鿿]{2,6})宜([急疏润降清通导]下)[，,]\s*如([^；。]{2,60})')
t932 = P['b00932']['text']
for m in DOWN.finditer(t932):
    subj, meth, fml = clean_subject(m.group(1)), m.group(2) + '法', m.group(3)
    if not subj:
        continue
    pv = prov('b00932', t932)
    sid = node('Pattern', subj, {}, pv)
    tid = node('TreatmentPrinciple', meth, {'action_type': '下法分类'}, pv)
    edge('treatedByPrinciple', sid, tid, subj, meth, pv)
    for f in re.findall(r'[一-鿿]{2,10}(?:汤|散|丸|丹)', fml):
        f = re.sub(r'^(局方|千金|《温疫论》|《金匮翼》)', '', f)
        if f in by_cls['Formula']:
            edge('principleRealizedBy', tid, by_cls['Formula'][f]['id'], meth, f, pv)

# 3d 燥病诸证与主方（b00640）
DRY = re.compile(r'([上中下肠筋]燥)则([一-鿿]{1,4})[，,]\s*([一-鿿]{2,12}(?:汤|散|饮|丸|煎))为主药')
t640 = P['b00640']['text']
for m in DRY.finditer(t640):
    pat, sym, fml = m.group(1), m.group(2), m.group(3)
    pv = prov('b00640', t640)
    sid = node('Pattern', pat, {'nature': '燥'}, pv)
    edge('patternOfDisease', sid, node('Disease', '燥病', {'category': '六淫正病'},
                                       prov('b00628', sent628)), pat, '燥病', pv)
    fid = by_cls['Formula'].get(fml)
    if fid:
        edge('formulaTreats', fid['id'], sid, fml, pat, pv)

# 3e 证候归属六淫正病（依原书分节论述）
BELONG = {'风病': ['外风', '内风'], '寒病': ['外寒', '里寒', '表寒'],
          '暑病': ['伤暑', '中暑', '伏暑', '暑火'],
          '湿病': ['风湿', '寒湿', '湿热', '湿火'],
          '燥病': ['寒燥', '热燥'], '火病': ['郁火', '实火', '虚火', '阴火']}
SEC = {'风病': 'b00630', '寒病': 'b00632', '暑病': 'b00634',
       '湿病': 'b00636', '燥病': 'b00638', '火病': 'b00642'}
for dis, pats in BELONG.items():
    pid = SEC[dis]
    pv = prov(pid, P[pid]['text'])
    did = node('Disease', dis, {'category': '六淫正病'}, prov('b00628', sent628))
    for pn in pats:
        key = ('Pattern', pn)
        if pn in by_cls['Pattern'] or key in new_nodes:
            sid = by_cls['Pattern'][pn]['id'] if pn in by_cls['Pattern'] else new_nodes[key]['id']
            edge('patternOfDisease', sid, did, pn, dis, pv)

# ============ 四、病证 → 论述它的医家 ============
for (cls, nm), n in list(new_nodes.items()):
    if cls != 'Disease':
        continue
    pv0 = n['provenance'][0]
    ph = physician_of(pv0.get('chapter_path', ''))
    if ph:
        edge('describedBy', n['id'], ph[0], nm, ph[1], pv0)

# ============ 校验 ============
allnodes = {n['id']: n for n in kg['nodes']}
allnodes.update({n['id']: n for n in new_nodes.values()})
props = onto['object_properties']
bad = []
for e in new_edges:
    p = props.get(e['type']); s = allnodes.get(e['subject_id']); o = allnodes.get(e['object_id'])
    if not (p and s and o):
        bad.append(('悬空', e['type'], e['subject_name'], e['object_name'])); continue
    if s['cls'] != p['domain'] or o['cls'] != p['range']:
        bad.append(('域/值域', e['type'], s['cls'], o['cls']))
seen, dedup = set(), []
for e in new_edges:
    k = (e['type'], e['subject_id'], e['object_id'])
    if k not in seen:
        seen.add(k); dedup.append(e)

print('=== 病证分类完整性（原书自报条数 vs 抽出条数）===')
for cat, got, stated, miss in tax_report:
    flag = '✓' if got == stated and not miss else '✗'
    print(f'  {cat:8s} 抽出 {got:2d} / 原书称 {stated:2d} {flag}' + (f'  未见于原文: {miss}' if miss else ''))
cc = collections.Counter(n['cls'] for n in new_nodes.values())
ec = collections.Counter(e['type'] for e in dedup)
print('\n新增节点:', dict(cc), '合计', len(new_nodes))
print('新增关系:', dict(ec), '合计', len(dedup))
print('本体违例:', bad if bad else '0 ✓')

if '--write' in sys.argv:
    kg['nodes'].extend(new_nodes.values())
    kg['edges'].extend(dedup)
    m = kg['meta']
    m['layers_extracted'] = ['lineage', 'diagnostic', 'materia', 'pattern']
    m['layers_pending'] = []
    m['n_nodes'], m['n_edges'] = len(kg['nodes']), len(kg['edges'])
    m['note'] = ('四层均已抽取。谱系层与诊法层为单模型 LLM 抽取；'
                 '本草方剂层与证候层为确定性解析，同一输入必得同一图谱。'
                 'Symptom 类刻意留空——症状已由 DiagnosticSign（问诊/望诊）承载。')
    (ROOT / 'data/shaopai_kg.json').write_text(json.dumps(kg, ensure_ascii=False), encoding='utf-8')
    print(f'\n已写入 → 节点 {m["n_nodes"]}  关系 {m["n_edges"]}')
