#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把上游（医哲未来人工智能研究院，IMPFAI）交付的图谱导入 data/。

  python3 tools/import_upstream.py --explorer shaopai_explorer.html
  python3 tools/import_upstream.py --kg shaopai_kg.json

--explorer  读取上游自包含浏览器内嵌的 JSON 载荷（<script type="application/json" id="data">）。
            该载荷是上游主图谱的精简副本：每条关系只带 1 条原文与章节路径，每个节点最多
            3 条章节路径与 1 条原文，且不含段落编号（passage_id）。
--kg        读取上游完整主图谱（含全部出处与段落编号），节点与关系字段按原样保留。

产出（默认写入 data/，可用 --out-dir 改）：
  shaopai_kg.json        仓库统一格式的主图谱（meta · ontology · vocabularies · nodes · edges）
  layout_positions.json  上游烘焙的布局坐标，逐字保留
  qc_audit.json          由图谱实测重算的质检数字
  disease_profiles.csv   病证 × 医案：病例数与共现药物 / 症状

层归属（layer）、来源文献（corpus）与抽取引擎（engine）在浏览器载荷中不逐条给出，这里补出：

  layer   按关系类型的语义归层，见 LAYER_OF_REL——每条关系的层由本体唯一决定，
          与它出自哪部书无关。（V5 曾以「章节根优先」推定，导致《赵晴初医论》的
          学术观点被归入越医文化层；自 V6 起改为纯语义归层。）
  corpus  按章节根映射到八种文献之一，见 CORPUS_OF_ROOT——「出自哪部书」由它承载。
  engine  按上游 meta 声明取层默认值；对上一版已收录的关系，沿用其记录在案的引擎
          （上游 V2 给六经归属与子证候标的是 builtin-haiku+vocab）。重复运行时
          --prev 指向当前 data/shaopai_kg.json，引擎标注保持不变。
"""
import json, re, csv, sys, argparse, collections, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
NS, PREFIX = 'https://w3id.org/shaopai/ontology#', 'sp'
AGREEMENT = 'single_engine'          # 上游：MiniMax 交叉验证从未运行

# ---------------------------------------------------------------- 本体
CLASS_ATTRS = {   # 沿用上游 1.0.0 的属性表，并补入本次交付新出现的类与属性
    'Physician': ['name_zh', 'courtesy_name', 'birth_year', 'death_year', 'native_place',
                  'dynasty', 'role_in_school'],
    'Work': ['title_zh', 'author', 'year', 'edition', 'is_extant'],
    'Doctrine': ['statement_zh', 'topic', 'proposed_by', 'novelty'],
    'Disease': ['name_zh', 'category', 'aliases'],
    'Pattern': ['name_zh', 'channel', 'triple_burner', 'nature', 'note', 'aliases'],
    'Symptom': ['name_zh', 'body_region', 'severity', 'timing'],
    'DiagnosticSign': ['name_zh', 'modality', 'descriptor'],
    'TreatmentPrinciple': ['name_zh', 'action_type'],
    'Formula': ['name_zh', 'source_work', 'attributed_to', 'preparation', 'indication', 'aliases'],
    'Herb': ['name_zh', 'aliases', 'part_used', 'is_fresh', 'dose', 'unit', 'processing'],
    'HerbProperty': ['flavor', 'temperature', 'channel_tropism'],
    'Dosage': ['amount', 'unit', 'processing', 'admin_note'],
    'CaseRecord': ['patient_desc', 'presentation', 'outcome', 'physician', 'prescription'],
    'Institution': ['name_zh', 'kind', 'place', 'founder', 'founded_year'],
    'Place': ['name_zh', 'modern_name'],
    'MedicalFamily': ['name_zh', 'specialty', 'place', 'generations'],
}
MODALITIES = ['舌诊', '脉诊', '腹诊', '目诊', '望诊', '闻诊', '问诊']

# 定义域 / 值域 / 基数。前 26 条沿用上游 1.0.0 声明；后 13 条为本次交付新增，
# 定义域与值域取自数据中唯一出现的类对（导入时逐条校验，见 validate()）。
# statedIn / belongsToChannel / subPatternOf / derivesFrom / institutionAtPlace 在 1.0.0
# 声明为 0..1，交付数据中分别有 11 / 3 / 2 / 14 / 2 个主语带多条出边（一条观点载于多部著作、
# 一首方剂同出数书等），而上游自报全部关系通过校验，故按交付数据放宽为 0..*。
PROP_SPEC = {
    'studiedUnder': ('Physician', 'Physician', '0..*'),
    'influencedBy': ('Physician', 'Physician', '0..*'),
    'authored': ('Physician', 'Work', '0..*'),
    'editedRevised': ('Physician', 'Work', '0..*'),
    'proposes': ('Physician', 'Doctrine', '0..*'),
    'statedIn': ('Doctrine', 'Work', '0..*'),
    'belongsToChannel': ('Pattern', 'Pattern', '0..*'),
    'subPatternOf': ('Pattern', 'Pattern', '0..*'),
    'patternOfDisease': ('Pattern', 'Disease', '0..*'),
    'manifestsAs': ('Pattern', 'Symptom', '0..*'),
    'signIndicates': ('DiagnosticSign', 'Pattern', '0..*'),
    'signExcludes': ('DiagnosticSign', 'Pattern', '0..*'),
    'treatedByPrinciple': ('Pattern', 'TreatmentPrinciple', '0..*'),
    'principleRealizedBy': ('TreatmentPrinciple', 'Formula', '0..*'),
    'formulaTreats': ('Formula', 'Pattern', '0..*'),
    'hasIngredient': ('Formula', 'Herb', '1..*'),
    'ingredientRole': ('Formula', 'Herb', '0..*'),
    'hasDosage': ('Formula', 'Dosage', '0..*'),
    'modifiedBy': ('Formula', 'Formula', '0..*'),
    'addHerbIf': ('Formula', 'Herb', '0..*'),
    'removeHerbIf': ('Formula', 'Herb', '0..*'),
    'herbHasProperty': ('Herb', 'HerbProperty', '0..*'),
    'caseUsesFormula': ('CaseRecord', 'Formula', '0..*'),
    'caseShowsPattern': ('CaseRecord', 'Pattern', '0..*'),
    'caseByPhysician': ('CaseRecord', 'Physician', '0..1'),
    'derivesFrom': ('Formula', 'Work', '0..*'),
    # ---- 1.1.0 新增 ----
    'caseDiagnosedAs': ('CaseRecord', 'Disease', '0..*'),
    'caseShowsSign': ('CaseRecord', 'DiagnosticSign', '0..*'),
    'caseUsesHerb': ('CaseRecord', 'Herb', '0..*'),
    'caseAppliesPrinciple': ('CaseRecord', 'TreatmentPrinciple', '0..*'),
    'caseShowsSymptom': ('CaseRecord', 'Symptom', '0..*'),
    'diseaseManifestsAs': ('Disease', 'Symptom', '0..*'),
    'diseaseSubtypeOf': ('Disease', 'Disease', '0..1'),
    'diseaseTreatedByFormula': ('Formula', 'Disease', '0..*'),
    'physicianFounded': ('Physician', 'Institution', '0..*'),
    'physicianOfPlace': ('Physician', 'Place', '0..*'),
    'physicianInFamily': ('Physician', 'MedicalFamily', '0..*'),
    'familySpecializesIn': ('MedicalFamily', 'Disease', '0..*'),
    'institutionAtPlace': ('Institution', 'Place', '0..*'),
}
PROVENANCE_FIELDS = ['source_sentence', 'chapter_path', 'passage_id', 'evidence_verbatim',
                     'engine', 'agreement']

# ---------------------------------------------------------------- 层与引擎
LAYER_OF_REL = {
    'lineage':    ['studiedUnder', 'influencedBy', 'authored', 'editedRevised', 'proposes', 'statedIn'],
    'diagnostic': ['signIndicates', 'signExcludes', 'belongsToChannel', 'subPatternOf'],
    'pattern':    ['patternOfDisease', 'manifestsAs', 'treatedByPrinciple', 'principleRealizedBy',
                   'formulaTreats', 'diseaseManifestsAs', 'diseaseSubtypeOf', 'diseaseTreatedByFormula'],
    'materia':    ['hasIngredient', 'ingredientRole', 'hasDosage', 'modifiedBy', 'addHerbIf',
                   'removeHerbIf', 'herbHasProperty', 'derivesFrom'],
    'case':       ['caseUsesFormula', 'caseShowsPattern', 'caseByPhysician', 'caseDiagnosedAs',
                   'caseShowsSign', 'caseUsesHerb', 'caseAppliesPrinciple', 'caseShowsSymptom'],
    'culture':    ['physicianFounded', 'physicianOfPlace', 'physicianInFamily',
                   'familySpecializesIn', 'institutionAtPlace'],
}
REL_LAYER = {r: l for l, rs in LAYER_OF_REL.items() for r in rs}
LAYER_ZH = {'lineage': '谱系层', 'diagnostic': '诊法层', 'pattern': '证候层', 'materia': '本草方剂层',
            'case': '医案层', 'culture': '越医文化层'}
DEFAULT_ENGINE = {'lineage': 'builtin-sonnet', 'diagnostic': 'builtin-haiku', 'pattern': 'builtin-haiku',
                  'materia': 'builtin-haiku', 'case': 'builtin-haiku', 'culture': 'builtin-haiku'}

# 章节根 → 来源文献。第 N 章 / 后记 属《越医文化》；受控词表随专著。
CORPUS_OF_ROOT = {
    '概述': 'shaopai', '代表医家': 'shaopai', 'controlled vocabulary': 'shaopai',
    '何廉臣医案': 'hlc_yian',
    '俞根初临证经验集要': 'ygc_jingyao',
    '赵晴初医论': 'zqc_yilun',
    '下篇越中名醫傳': 'yz_mingyi',
    '越醫雜詠': 'yy_zayong',
    '绍派伤寒史料图片研究': 'sp_shiliao',
    '后记': 'yue_wenhua',
}
CORPUS_ZH = {
    'shaopai': '《浙派中医丛书·绍派伤寒》',
    'hlc_yian': '《何廉臣医案》',
    'ygc_jingyao': '《俞根初临证经验集要》',
    'zqc_yilun': '《赵晴初医论》',
    'yz_mingyi': '《越中名医传》',
    'yy_zayong': '《越醫雜詠》',
    'sp_shiliao': '《绍派伤寒史料图片研究》',
    'yue_wenhua': '《越医文化》',
}


def layer_of(rel, chapter_path=None):
    """按关系类型的语义归层——每条关系的层由本体唯一决定，与出自哪部书无关。

    chapter_path 仅为向后兼容保留，不参与判定；「出自哪部书」由 corpus_of() 承载。
    """
    return REL_LAYER.get(rel, 'lineage')


def corpus_of(chapter_path):
    """章节根 → 来源文献键；「第N章…」归《越医文化》，未知根返回 ''。"""
    root = (chapter_path or '').split(' / ')[0].strip()
    if not root:
        return ''
    if root in CORPUS_OF_ROOT:
        return CORPUS_OF_ROOT[root]
    if re.match(r'^第[一二三四五六七八九十]+章', root):
        return 'yue_wenhua'
    return ''


def engines_from_meta(meta):
    """解析上游 meta.engines 里的 'builtin-haiku (diagnostic/pattern/…)' 写法；
    括号内只取确实是层名的词（'first pass'、'all other layers' 之类描述性文字跳过）。"""
    out = dict(DEFAULT_ENGINE)
    for s in meta.get('engines') or []:
        m = re.match(r'^(\S+)\s*\((.+)\)$', s.strip())
        if not m:
            continue
        for layer in re.split(r'[/,、\s]+', m.group(2)):
            if layer.strip() in LAYER_OF_REL:
                out[layer.strip()] = m.group(1)
    return out


# ---------------------------------------------------------------- 读取
def read_explorer_payload(path):
    src = Path(path).read_text(encoding='utf-8')
    m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', src, re.S)
    if not m:
        sys.exit(f'{path}: 未找到 <script type="application/json"> 载荷')
    return json.loads(m.group(1))


def previous_engines(prev_path):
    """上一版 data/shaopai_kg.json 里记录在案的引擎：(subject, object, type) → engine。"""
    p = Path(prev_path)
    if not p.exists():
        return {}, None
    kg = json.loads(p.read_text(encoding='utf-8'))
    eng = {}
    for e in kg.get('edges', []):
        en = e.get('engine') or (e.get('provenance') or [{}])[0].get('engine')
        if en and en != 'rule-parser-v1':
            eng[(e['subject_id'], e['object_id'], e['type'])] = en
    return eng, kg.get('vocabularies')


def build_ontology(version, classes_zh, props_zh, nodes, edges):
    observed_attrs = collections.defaultdict(set)
    for n in nodes:
        for k in (n.get('attrs') or {}):
            observed_attrs[n['cls']].add(k)
    classes = {}
    for c, zh in classes_zh.items():
        attrs = list(CLASS_ATTRS.get(c, ['name_zh']))
        for k in sorted(observed_attrs.get(c, ())):
            if k not in attrs:
                attrs.append(k)
        entry = {'zh': zh, 'attrs': attrs}
        if c == 'DiagnosticSign':
            entry['modalities'] = MODALITIES
        classes[c] = entry
    # 数据中每种关系实际出现的 (定义域, 值域)
    seen = collections.defaultdict(collections.Counter)
    cls_of = {n['id']: n['cls'] for n in nodes}
    for e in edges:
        seen[e['type']][(cls_of[e['subject_id']], cls_of[e['object_id']])] += 1
    props = {}
    for p, zh in props_zh.items():
        if p in PROP_SPEC:
            d, r, card = PROP_SPEC[p]
        elif seen.get(p):
            (d, r), _ = seen[p].most_common(1)[0]
            card = '0..*'
        else:
            sys.exit(f'关系 {p} 既无声明也无数据，无法确定定义域/值域')
        props[p] = {'zh': zh, 'domain': d, 'range': r, 'card': card}
    return {'namespace': NS, 'prefix': PREFIX, 'version': version, 'classes': classes,
            'object_properties': props, 'provenance_fields': PROVENANCE_FIELDS}


def from_explorer(payload, prev_engines):
    meta_in = payload['meta']
    onto_in = payload['onto']
    eng_of_layer = engines_from_meta(meta_in)

    nodes = []
    for n in payload['nodes']:
        pv = n.get('p') or {}
        prov = []
        for i, ch in enumerate(pv.get('ch') or []):
            item = {'chapter_path': ch}
            if i == 0 and pv.get('ev'):
                item['source_sentence'] = pv['ev']
            prov.append(item)
        nodes.append({
            'id': n['i'], 'cls': n['c'], 'name': n['n'],
            'aliases': list(n.get('a') or []),
            'attrs': {k: v for k, v in (n.get('t') or {}).items() if v not in (None, '', [])},
            'provenance': prov,
            'n_mentions': n.get('m', 0),
            'n_provenance': pv.get('n', len(prov)),
            'x': n['x'], 'y': n['y'],
            'component': n.get('g'),
        })
    name_of = {n['id']: n['name'] for n in nodes}

    edges, reused, no_corpus = [], 0, 0
    for e in payload['edges']:
        layer = layer_of(e['t'])
        corpus = corpus_of(e.get('ch'))
        if not corpus:
            no_corpus += 1
        key = (e['s'], e['o'], e['t'])
        if key in prev_engines:
            engine = prev_engines[key]; reused += 1
        else:
            engine = eng_of_layer.get(layer, DEFAULT_ENGINE[layer])
        # 原文句在不同交付里键名不同：V6 用 ev，V5 用 e
        sentence = e.get('ev') if e.get('ev') is not None else e.get('e', '')
        prov = {'chapter_path': e.get('ch', ''), 'source_sentence': sentence,
                'evidence_verbatim': bool(e.get('v')), 'engine': engine, 'agreement': AGREEMENT}
        edges.append({
            'type': e['t'], 'subject_id': e['s'], 'object_id': e['o'],
            'subject_name': name_of[e['s']], 'object_name': name_of[e['o']],
            'chapter_path': prov['chapter_path'], 'source_sentence': prov['source_sentence'],
            'evidence_verbatim': prov['evidence_verbatim'],
            'engine': engine, 'agreement': AGREEMENT, 'layer': layer, 'corpus': corpus,
            'n_support': e.get('n', 1), 'provenance': [prov],
        })
    if no_corpus:
        print(f'警告：{no_corpus} 条关系的章节根未能映射到来源文献（corpus 为空）', file=sys.stderr)

    meta = {
        'title': meta_in.get('title', '绍派伤寒·越医知识图谱'),
        'source_book': (meta_in.get('corpora') or ['《浙派中医丛书》专题系列·绍派伤寒'])[0],
        'editor': '沈钦荣', 'year': 2021,
        'corpora': meta_in.get('corpora', []),
        'ontology_version': meta_in.get('ontology_version', '1.1.0'),
        'layers': meta_in.get('layers', list(LAYER_OF_REL)),
        'layers_zh': LAYER_ZH,
        'layer_coverage': meta_in.get('layer_coverage', {}),
        'coverage_note': meta_in.get('coverage_note', ''),
        'corpora_zh': CORPUS_ZH,
        'engines': meta_in.get('engines', []),
        'engine_by_layer': eng_of_layer,
        'agreement': AGREEMENT,
        'cross_validation': meta_in.get('cross_validation', 'not_run'),
        'cross_validation_note': meta_in.get('cross_validation_note', ''),
        'identity_merge': meta_in.get('identity_merge', {}),
        'n_nodes': len(nodes), 'n_edges': len(edges),
        'publisher': meta_in.get('publisher', '医哲未来人工智能研究院 (IMPFAI)'),
        'publisher_url': meta_in.get('publisher_url', 'https://impfai.github.io/'),
        'layout': dict(meta_in.get('layout') or {}, positions_included=True),
        'derived_from': {
            'kind': 'explorer_payload',
            'note': '本文件由上游自包含浏览器（shaopai_explorer.html）内嵌的精简载荷还原：'
                    '每条关系 1 条原文与章节路径，每个节点最多 3 条章节路径与 1 条原文，不含段落编号。'
                    '完整出处以上游 shaopai_kg.json 为准。',
            'engine_reused_from_previous_release': reused,
            'layer_rule': '按关系类型的语义归层（tools/import_upstream.py: layer_of）',
            'corpus_rule': '按章节根映射到八种文献（tools/import_upstream.py: corpus_of）',
        },
        'imported_at': datetime.date.today().isoformat(),
    }
    onto = build_ontology(meta['ontology_version'], onto_in['classes'], onto_in['props'], nodes, edges)
    return {'meta': meta, 'ontology': onto, 'nodes': nodes, 'edges': edges}


def from_full_kg(kg):
    """上游完整主图谱：字段原样保留，只补齐 layer 与 component，便于站点工具消费。"""
    for k in ('meta', 'ontology', 'nodes', 'edges'):
        if k not in kg:
            sys.exit(f'--kg 文件缺少顶层字段 {k}')
    for e in kg['edges']:
        e.setdefault('layer', layer_of(e['type']))
        e.setdefault('corpus', corpus_of(e.get('chapter_path')
                                         or (e.get('provenance') or [{}])[0].get('chapter_path')))
    kg['meta'].setdefault('layers_zh', LAYER_ZH)
    kg['meta'].setdefault('corpora_zh', CORPUS_ZH)
    kg['meta'].setdefault('derived_from', {'kind': 'full_kg'})
    kg['meta']['imported_at'] = datetime.date.today().isoformat()
    return kg


# ---------------------------------------------------------------- 校验与统计
def validate(kg):
    onto = kg['ontology']['object_properties']
    cls_of = {n['id']: n['cls'] for n in kg['nodes']}
    bad_dr, dangling, loops = [], 0, 0
    out_count = collections.Counter()
    for e in kg['edges']:
        s, o, t = e['subject_id'], e['object_id'], e['type']
        if s not in cls_of or o not in cls_of:
            dangling += 1; continue
        if s == o:
            loops += 1
        spec = onto.get(t)
        if not spec or cls_of[s] != spec['domain'] or cls_of[o] != spec['range']:
            bad_dr.append((t, cls_of[s], cls_of[o]))
        out_count[(s, t)] += 1
    max1 = {p for p, v in onto.items() if v['card'].endswith('..1')}
    over = sum(1 for (s, t), c in out_count.items() if t in max1 and c > 1)
    dup = collections.Counter((e['subject_id'], e['object_id'], e['type']) for e in kg['edges'])
    return {
        'domain_range_violations': len(bad_dr),
        'domain_range_examples': [f'{t}: {a}→{b}' for t, a, b in bad_dr[:5]],
        'dangling_endpoints': dangling,
        'self_loops': loops,
        'duplicate_triples': sum(c - 1 for c in dup.values() if c > 1),
        'max_cardinality_exceptions': over,
        'max_cardinality_note': '基数校验只检查上限为 1 的关系（caseByPhysician · derivesFrom · '
                                'diseaseSubtypeOf · institutionAtPlace）。',
    }


def components(kg):
    ids = {n['id'] for n in kg['nodes']}
    adj = collections.defaultdict(set)
    for e in kg['edges']:
        s, o = e['subject_id'], e['object_id']
        if s in ids and o in ids and s != o:
            adj[s].add(o); adj[o].add(s)
    seen, sizes = set(), []
    for i in ids:
        if i in seen:
            continue
        stack, cur = [i], set()
        while stack:
            x = stack.pop()
            if x in cur:
                continue
            cur.add(x); stack.extend(adj[x] - cur)
        seen |= cur; sizes.append(len(cur))
    sizes.sort(reverse=True)
    return sizes


def disease_profiles(kg):
    name = {n['id']: n['name'] for n in kg['nodes']}
    case_dis, case_herb, case_sym = (collections.defaultdict(set) for _ in range(3))
    for e in kg['edges']:
        if e['type'] == 'caseDiagnosedAs':
            case_dis[e['subject_id']].add(e['object_id'])
        elif e['type'] == 'caseUsesHerb':
            case_herb[e['subject_id']].add(e['object_id'])
        elif e['type'] == 'caseShowsSymptom':
            case_sym[e['subject_id']].add(e['object_id'])
    dis_cases = collections.defaultdict(set)
    for c, ds in case_dis.items():
        for d in ds:
            dis_cases[d].add(c)
    rows = []
    for d, cs in dis_cases.items():
        hc, sc = collections.Counter(), collections.Counter()
        for c in cs:
            hc.update(case_herb[c]); sc.update(case_sym[c])
        top = lambda cnt, k: [name[i] for i, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], name[kv[0]]))[:k]]
        rows.append({'disease_id': d, 'disease': name[d], 'n_cases': len(cs),
                     'signature_herbs': top(hc, 6), 'signature_symptoms': top(sc, 5)})
    rows.sort(key=lambda r: (-r['n_cases'], r['disease']))
    return rows, len(case_dis)


def audit(kg, profiles, n_cases_dx):
    nodes, edges = kg['nodes'], kg['edges']
    deg = collections.Counter()
    for e in edges:
        deg[e['subject_id']] += 1; deg[e['object_id']] += 1
    by_cls = collections.Counter(n['cls'] for n in nodes)
    by_type = collections.Counter(e['type'] for e in edges)
    sizes = components(kg)
    isolates = [n for n in nodes if deg[n['id']] == 0]
    verbatim = sum(1 for e in edges if e.get('evidence_verbatim'))
    single = sum(1 for e in edges if e.get('n_support', 1) == 1)
    no_sent = sum(1 for e in edges if not e.get('source_sentence'))
    onto = kg['ontology']
    used = set(by_type)
    mods = collections.Counter((n.get('attrs') or {}).get('modality') for n in nodes
                               if n['cls'] == 'DiagnosticSign')
    mods.pop(None, None)
    layers = collections.Counter(e.get('layer') for e in edges)
    corpora = collections.Counter(e.get('corpus') or '(未映射)' for e in edges)
    return {
        'generated_from': {
            'corpora': kg['meta'].get('corpora', []),
            'delivery': kg['meta'].get('derived_from', {}).get('kind'),
            'imported_at': kg['meta'].get('imported_at'),
        },
        'ontology': {
            'version': onto['version'],
            'classes_defined': len(onto['classes']), 'classes_populated': len(by_cls),
            'unpopulated_classes': sorted(set(onto['classes']) - set(by_cls)),
            'properties_defined': len(onto['object_properties']), 'properties_used': len(used),
            'unused_properties': sorted(set(onto['object_properties']) - used),
        },
        'graph': {
            'n_nodes': len(nodes), 'n_edges': len(edges),
            'nodes_by_class': dict(by_cls.most_common()),
            'edges_by_type': dict(by_type.most_common()),
            'edges_by_layer': dict(layers.most_common()),
            'edges_by_corpus': dict(corpora.most_common()),
            'nodes_with_relations': len(nodes) - len(isolates),
            'isolated_nodes': len(isolates),
            'isolates_by_class': dict(collections.Counter(n['cls'] for n in isolates).most_common()),
            'connectivity_pct': round(100 * (len(nodes) - len(isolates)) / len(nodes), 1),
            'n_components': len(sizes), 'largest_component': sizes[0] if sizes else 0,
            'satellite_components': sum(1 for s in sizes[1:] if s >= 2),
        },
        'coverage': {
            'layer_coverage': kg['meta'].get('layer_coverage', {}),
            'note': kg['meta'].get('coverage_note', ''),
        },
        'engines': {'by_layer': kg['meta'].get('engine_by_layer', {}),
                    'cross_validation': kg['meta'].get('cross_validation', 'not_run'),
                    'agreement': kg['meta'].get('agreement', AGREEMENT)},
        'integrity': dict(validate(kg), **{
            'edges_with_provenance': sum(1 for e in edges if e.get('provenance')),
            'edges_without_source_sentence': no_sent,
            'evidence_verbatim': f'{verbatim}/{len(edges)} ({100 * verbatim / len(edges):.1f}%)',
            'single_mention_edges': f'{single}/{len(edges)} ({100 * single / len(edges):.1f}%)',
        }),
        'diagnostic_modalities': dict(mods.most_common()),
        'disease_layer': {
            'n_disease': by_cls.get('Disease', 0),
            'diseases_with_cases': len(profiles),
            'cases_with_diagnosis': n_cases_dx,
            'n_cases': by_cls.get('CaseRecord', 0),
            'top': [{'disease': r['disease'], 'cases': r['n_cases'], 'herbs': r['signature_herbs']}
                    for r in profiles[:12]],
        },
        'derived_copy': kg['meta'].get('derived_from', {}),
    }


# ---------------------------------------------------------------- 输出
def dump_kg(kg, path):
    """meta / ontology / vocabularies 缩进排版；nodes / edges 每条记录一行——
    便于 diff 与流式读取，体积约为全缩进写法的一半。"""
    j = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    parts = ['{']
    for k in ('meta', 'ontology', 'vocabularies'):
        if k in kg:
            parts.append(f'"{k}":' + json.dumps(kg[k], ensure_ascii=False, indent=1) + ',')
    parts.append('"nodes":[\n' + ',\n'.join(j(n) for n in kg['nodes']) + '\n],')
    parts.append('"edges":[\n' + ',\n'.join(j(e) for e in kg['edges']) + '\n]')
    parts.append('}')
    Path(path).write_text('\n'.join(parts), encoding='utf-8')


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--explorer', help='上游自包含浏览器 HTML（或其 JSON 载荷）')
    src.add_argument('--kg', help='上游完整 shaopai_kg.json')
    ap.add_argument('--prev', default=str(DATA / 'shaopai_kg.json'),
                    help='上一版主图谱，用于沿用引擎标注与受控词表（默认 data/shaopai_kg.json）')
    ap.add_argument('--out-dir', default=str(DATA))
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    prev_eng, prev_vocab = previous_engines(a.prev)
    if a.explorer:
        p = Path(a.explorer)
        payload = json.loads(p.read_text(encoding='utf-8')) if p.suffix == '.json' else read_explorer_payload(p)
        kg = from_explorer(payload, prev_eng)
    else:
        kg = from_full_kg(json.loads(Path(a.kg).read_text(encoding='utf-8')))
    if prev_vocab and 'vocabularies' not in kg:
        kg['vocabularies'] = prev_vocab            # 上游 1.0.0 受控词表（六经、三焦、舌苔、脉象……）
    kg = {k: kg[k] for k in ('meta', 'ontology', 'vocabularies', 'nodes', 'edges') if k in kg}

    profiles, n_cases_dx = disease_profiles(kg)
    qc = audit(kg, profiles, n_cases_dx)
    if qc['integrity']['domain_range_violations'] or qc['integrity']['dangling_endpoints']:
        print('警告：存在定义域/值域违例或悬空端点', qc['integrity'], file=sys.stderr)

    dump_kg(kg, out / 'shaopai_kg.json')
    pos = {n['id']: [n['x'], n['y']] for n in kg['nodes'] if n.get('x') is not None}
    (out / 'layout_positions.json').write_text(
        json.dumps(pos, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (out / 'qc_audit.json').write_text(json.dumps(qc, ensure_ascii=False, indent=1), encoding='utf-8')
    with (out / 'disease_profiles.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['disease_id', 'disease', 'n_cases', 'signature_herbs', 'signature_symptoms'])
        for r in profiles:
            w.writerow([r['disease_id'], r['disease'], r['n_cases'],
                        '、'.join(r['signature_herbs']), '、'.join(r['signature_symptoms'])])

    g = qc['graph']
    print(f"节点 {g['n_nodes']:,}  关系 {g['n_edges']:,}  类 {qc['ontology']['classes_populated']}/"
          f"{qc['ontology']['classes_defined']}  关系类型 {qc['ontology']['properties_used']}/"
          f"{qc['ontology']['properties_defined']}  巨分量 {g['largest_component']:,}  孤点 {g['isolated_nodes']:,}")
    print(f"  引擎沿用上一版 {kg['meta'].get('derived_from', {}).get('engine_reused_from_previous_release', 0):,} 条"
          f"  · 层分布 {g['edges_by_layer']}")
    print(f"  完整性 {qc['integrity']}")
    print(f"  病证档案 {len(profiles)} 条（有诊断的医案 {n_cases_dx}）")


if __name__ == '__main__':
    main()
