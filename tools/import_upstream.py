#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把上游（医哲未来人工智能研究院，IMPFAI）交付的图谱导入 data/。

  # 推荐：浏览器载荷 + 上游 CSV + 本体规格 + 语料 —— 出处最全
  python3 tools/import_upstream.py --explorer shaopai_explorer.html \\
      --nodes-csv nodes.csv --edges-csv edges.csv --ontology ontology_spec.json \\
      --corpus corpus_yueyi.json --profiles modern_case_profiles.csv

  # 仅浏览器载荷（V5 / V6 的做法；每条关系只有 1 条原文，无段落编号）
  python3 tools/import_upstream.py --explorer shaopai_explorer.html

  # 上游完整主图谱
  python3 tools/import_upstream.py --kg shaopai_kg.json

输入各自补上什么：
  --explorer   节点、关系、布局坐标、节点出处（每节点最多 3 条章节路径 + 1 条原文）
  --nodes-csv  浏览器载荷里没有的节点属性（case_no、base_formula、route…）
  --edges-csv  每条关系的**段落编号**与**实际抽取引擎**（浏览器载荷里都没有）
  --ontology   上游本体规格（类、属性、定义域 / 值域 / 基数），原样采用；不给则用内置表
  --corpus     分段语料：用于独立核验「原文是否真在所引段落里」，并发布到 data/
  --profiles   当代门诊的聚合统计（西医诊断 × 中医病证 × 证候 × 用药 × 外治）；默认只发布
               至少 MIN_K（3）例的行，1–2 例的行实为单个患者的诊疗概况，随逐案记录一并暂缓

当代病案（2022—2026，语料根「2022-2026病案」）
  默认**不发布逐案记录**：删去该语料的全部关系、只由它引出的节点、以及其余节点上源自它的
  出处与属性；布局取上一版坐标，保持全图几何不变。聚合统计（--profiles）只发布至少 3 例的行。
  --include-modern-cases  改为发布逐案记录，但先经 tools/deidentify.py 去标识化，
                          并在写盘前核验：任何残留（患者抬头、住院号、完整日期、运行时推导的
                          姓名）都会使导入中止。只有数据方确认已获发布授权时才应使用此开关。

  两种模式下，写盘前都会对**全部输出文本**跑同一道隐私闸门。

层（layer）/ 来源文献（corpus）/ 引擎（engine）
  corpus  按章节根映射到文献（CORPUS_OF_ROOT）。
  layer   当代门诊病案整体归「当代病案层」（上游把该语料整批路由到此层）；
          其余语料按关系类型的语义归层（LAYER_OF_REL），与出自哪部书无关。
  engine  有 --edges-csv 时取上游逐条记录的引擎；否则沿用上一版记录，再否则取层默认值。
"""
import json, re, io, csv, sys, argparse, collections, datetime, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deidentify as DI  # noqa: E402

csv.field_size_limit(sys.maxsize)
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
NS, PREFIX = 'https://w3id.org/shaopai/ontology#', 'sp'
AGREEMENT = 'single_engine'          # 上游：MiniMax 交叉验证从未运行

# ---------------------------------------------------------------- 本体（无 --ontology 时的内置表）
CLASS_ATTRS = {
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
PROP_SPEC = {   # 仅在没有 --ontology 时使用
    'studiedUnder': ('Physician', 'Physician', '0..*'), 'influencedBy': ('Physician', 'Physician', '0..*'),
    'authored': ('Physician', 'Work', '0..*'), 'editedRevised': ('Physician', 'Work', '0..*'),
    'proposes': ('Physician', 'Doctrine', '0..*'), 'statedIn': ('Doctrine', 'Work', '0..1'),
    'belongsToChannel': ('Pattern', 'Pattern', '0..1'), 'subPatternOf': ('Pattern', 'Pattern', '0..1'),
    'patternOfDisease': ('Pattern', 'Disease', '0..*'), 'manifestsAs': ('Pattern', 'Symptom', '0..*'),
    'signIndicates': ('DiagnosticSign', 'Pattern', '0..*'), 'signExcludes': ('DiagnosticSign', 'Pattern', '0..*'),
    'treatedByPrinciple': ('Pattern', 'TreatmentPrinciple', '0..*'),
    'principleRealizedBy': ('TreatmentPrinciple', 'Formula', '0..*'),
    'formulaTreats': ('Formula', 'Pattern', '0..*'), 'hasIngredient': ('Formula', 'Herb', '1..*'),
    'ingredientRole': ('Formula', 'Herb', '0..*'), 'hasDosage': ('Formula', 'Dosage', '0..*'),
    'modifiedBy': ('Formula', 'Formula', '0..*'), 'addHerbIf': ('Formula', 'Herb', '0..*'),
    'removeHerbIf': ('Formula', 'Herb', '0..*'), 'herbHasProperty': ('Herb', 'HerbProperty', '0..*'),
    'caseUsesFormula': ('CaseRecord', 'Formula', '0..*'), 'caseShowsPattern': ('CaseRecord', 'Pattern', '0..*'),
    'caseByPhysician': ('CaseRecord', 'Physician', '0..1'), 'derivesFrom': ('Formula', 'Work', '0..1'),
    'caseDiagnosedAs': ('CaseRecord', 'Disease', '0..*'), 'caseShowsSign': ('CaseRecord', 'DiagnosticSign', '0..*'),
    'caseUsesHerb': ('CaseRecord', 'Herb', '0..*'),
    'caseAppliesPrinciple': ('CaseRecord', 'TreatmentPrinciple', '0..*'),
    'caseShowsSymptom': ('CaseRecord', 'Symptom', '0..*'), 'diseaseManifestsAs': ('Disease', 'Symptom', '0..*'),
    'diseaseSubtypeOf': ('Disease', 'Disease', '0..1'), 'diseaseTreatedByFormula': ('Formula', 'Disease', '0..*'),
    'physicianFounded': ('Physician', 'Institution', '0..*'), 'physicianOfPlace': ('Physician', 'Place', '0..*'),
    'physicianInFamily': ('Physician', 'MedicalFamily', '0..*'),
    'familySpecializesIn': ('MedicalFamily', 'Disease', '0..*'), 'institutionAtPlace': ('Institution', 'Place', '0..1'),
}
PROVENANCE_FIELDS = ['source_sentence', 'chapter_path', 'passage_id', 'evidence_verbatim',
                     'engine', 'agreement']

# ---------------------------------------------------------------- 层、文献与引擎
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
    'modern_case': ['caseWesternDiagnosis', 'caseUsesProcedure', 'caseUsesWesternDrug',
                    'caseHasExamination', 'caseComorbidity', 'wdCorrespondsToTcm', 'examSupportsDiagnosis'],
}
REL_LAYER = {r: l for l, rs in LAYER_OF_REL.items() for r in rs}
LAYER_ZH = {'lineage': '谱系层', 'diagnostic': '诊法层', 'pattern': '证候层', 'materia': '本草方剂层',
            'case': '医案层', 'culture': '越医文化层', 'modern_case': '当代病案层'}
DEFAULT_ENGINE = {l: 'builtin-haiku' for l in LAYER_OF_REL}
DEFAULT_ENGINE['lineage'] = 'builtin-sonnet'

MODERN_ROOT, MODERN_CORPUS = '2022-2026病案', 'modern_clinic'
MIN_K = 3   # 当代门诊聚合统计的最小格：少于 3 例的行不发布（与主页「当代门诊」一节一致）
CORPUS_OF_ROOT = {
    '概述': 'shaopai', '代表医家': 'shaopai', 'controlled vocabulary': 'shaopai',
    '何廉臣医案': 'hlc_yian',
    '俞根初临证经验集要': 'ygc_jingyao',
    '赵晴初医论': 'zqc_yilun',
    '下篇越中名醫傳': 'yz_mingyi', '越中名医传补': 'yz_mingyi',
    '越醫雜詠': 'yy_zayong',
    '绍派伤寒史料图片研究': 'sp_shiliao',
    '后记': 'yue_wenhua', '《越医文化》目录': 'yue_wenhua',
    MODERN_ROOT: MODERN_CORPUS,
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
    MODERN_CORPUS: '沈钦荣当代骨伤科门诊病案（2022—2026）',
}


def root_of(chapter_path):
    return (chapter_path or '').split(' / ')[0].strip()


def corpus_of(chapter_path):
    """章节根 → 来源文献键；「第N章…」归《越医文化》，未知根返回 ''。"""
    root = root_of(chapter_path)
    if not root:
        return ''
    if root in CORPUS_OF_ROOT:
        return CORPUS_OF_ROOT[root]
    if re.match(r'^第[一二三四五六七八九十]+章', root):
        return 'yue_wenhua'
    return ''


def layer_of(rel, corpus=''):
    """当代门诊病案整体归当代病案层；其余按关系类型的语义归层。"""
    if corpus == MODERN_CORPUS:
        return 'modern_case'
    return REL_LAYER.get(rel, 'lineage')


def engines_from_meta(meta):
    """解析 meta.engines 的 'builtin-haiku (diagnostic/pattern/…)' 写法；括号内只认层名。"""
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
    p = Path(path)
    if p.suffix == '.json':
        return json.loads(p.read_text(encoding='utf-8'))
    src = p.read_text(encoding='utf-8')
    m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', src, re.S)
    if not m:
        sys.exit(f'{path}: 未找到 <script type="application/json"> 载荷')
    return json.loads(m.group(1))


def read_prev(prev_path):
    """上一版 data/shaopai_kg.json：节点（含坐标与出处）、关系引擎、受控词表。"""
    p = Path(prev_path)
    if not p.exists():
        return {}, {}, None
    kg = json.loads(p.read_text(encoding='utf-8'))
    eng = {}
    for e in kg.get('edges', []):
        en = e.get('engine') or (e.get('provenance') or [{}])[0].get('engine')
        if en and en != 'rule-parser-v1':
            eng[(e['subject_id'], e['object_id'], e['type'])] = en
    return {n['id']: n for n in kg.get('nodes', [])}, eng, kg.get('vocabularies')


def read_nodes_csv(path):
    out = {}
    for r in csv.DictReader(open(path, encoding='utf-8')):
        attrs = {}
        for k, v in r.items():
            if not k or k.startswith(':') or not v:
                continue
            key = k.split(':')[0]
            if key in ('name', 'aliases', 'n_mentions'):
                continue
            attrs[key] = v
        out[r[':ID']] = attrs
    return out


def read_edges_csv(path):
    """(s, o, t) → [行…]，按出现顺序；重复三元组依次取用。"""
    out = collections.defaultdict(list)
    for r in csv.DictReader(open(path, encoding='utf-8')):
        out[(r[':START_ID'], r[':END_ID'], r[':TYPE'])].append({
            'passage_id': r.get('passage_id:string', ''),
            'engine': r.get('engine:string', ''),
            'agreement': r.get('agreement:string', ''),
            'source_sentence': r.get('source_sentence:string', ''),
        })
    return out


def read_passages(paths):
    """段落编号 → 正文。兼容 corpus_yueyi（pid / source / text）与 corpus_shaopai（id / chapter_path / text）。"""
    out = {}
    for p in paths:
        if not p or not Path(p).exists():
            continue
        c = json.loads(Path(p).read_text(encoding='utf-8'))
        for x in c.get('passages', []):
            pid = x.get('pid') or x.get('id')
            if pid:
                out[pid] = x.get('text', '')
    return out


# ---------------------------------------------------------------- 本体
def build_ontology(spec, version, classes_zh, props_zh, nodes, edges):
    """有上游规格就原样采用（只在类属性表末尾补上数据里出现但未声明的属性）；否则用内置表。"""
    observed = collections.defaultdict(set)
    for n in nodes:
        for k in (n.get('attrs') or {}):
            observed[n['cls']].add(k)
    if spec:
        classes = json.loads(json.dumps(spec['classes']))
        for c, entry in classes.items():
            for k in sorted(observed.get(c, ())):
                if k not in entry['attrs']:
                    entry.setdefault('undeclared_attrs', []).append(k)
        props = json.loads(json.dumps(spec['object_properties']))
        return {'namespace': spec.get('namespace', NS), 'prefix': spec.get('prefix', PREFIX),
                'version': spec.get('version', version), 'classes': classes, 'object_properties': props,
                'provenance_fields': spec.get('provenance_fields', PROVENANCE_FIELDS), 'source': 'upstream ontology_spec.json'}
    classes = {}
    for c, zh in classes_zh.items():
        attrs = list(CLASS_ATTRS.get(c, ['name_zh']))
        extra = [k for k in sorted(observed.get(c, ())) if k not in attrs]
        entry = {'zh': zh, 'attrs': attrs}
        if extra:
            entry['undeclared_attrs'] = extra
        if c == 'DiagnosticSign':
            entry['modalities'] = MODALITIES
        classes[c] = entry
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
            'object_properties': props, 'provenance_fields': PROVENANCE_FIELDS, 'source': 'built-in'}


# ---------------------------------------------------------------- 组装
def from_explorer(payload, prev_eng, ncsv, ecsv, spec):
    meta_in, onto_in = payload['meta'], payload['onto']
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
        attrs = {k: v for k, v in (n.get('t') or {}).items() if v not in (None, '', [])}
        for k, v in (ncsv.get(n['i']) or {}).items():      # CSV 只补缺，不覆盖
            attrs.setdefault(k, v)
        nodes.append({
            'id': n['i'], 'cls': n['c'], 'name': n['n'],
            'aliases': list(n.get('a') or []),
            'attrs': attrs, 'provenance': prov,
            'n_mentions': n.get('m', 0), 'n_provenance': pv.get('n', len(prov)),
            'x': n['x'], 'y': n['y'],
        })
    name_of = {n['id']: n['name'] for n in nodes}

    edges, src = [], collections.Counter()
    for e in payload['edges']:
        corpus = corpus_of(e.get('ch'))
        layer = layer_of(e['t'], corpus)
        key = (e['s'], e['o'], e['t'])
        row = ecsv[key].pop(0) if ecsv.get(key) else None
        if row and row['engine']:
            engine = row['engine']; src['engine_from_csv'] += 1
        elif key in prev_eng:
            engine = prev_eng[key]; src['engine_from_prev'] += 1
        else:
            engine = eng_of_layer.get(layer, DEFAULT_ENGINE.get(layer, 'builtin-haiku')); src['engine_by_layer_default'] += 1
        pid = (row or {}).get('passage_id', '')
        if pid:
            src['passage_id_from_csv'] += 1
        sentence = e.get('ev') if e.get('ev') is not None else e.get('e', '')   # V6+ 用 ev，V5 用 e
        agreement = (row or {}).get('agreement') or AGREEMENT
        prov = {'chapter_path': e.get('ch', ''), 'source_sentence': sentence, 'passage_id': pid,
                'evidence_verbatim': bool(e.get('v')), 'engine': engine, 'agreement': agreement}
        edges.append({
            'type': e['t'], 'subject_id': e['s'], 'object_id': e['o'],
            'subject_name': name_of[e['s']], 'object_name': name_of[e['o']],
            'chapter_path': prov['chapter_path'], 'source_sentence': sentence, 'passage_id': pid,
            'evidence_verbatim': prov['evidence_verbatim'],
            'engine': engine, 'agreement': agreement, 'layer': layer, 'corpus': corpus,
            'n_support': e.get('n', 1), 'provenance': [prov],
        })

    meta = {
        'title': meta_in.get('title', '绍派伤寒·越医知识图谱'),
        'source_book': (meta_in.get('corpora') or ['《浙派中医丛书》专题系列·绍派伤寒'])[0],
        'editor': '沈钦荣', 'year': 2021,
        'corpora': meta_in.get('corpora', []),
        'ontology_version': (spec or {}).get('version') or meta_in.get('ontology_version', '1.1.0'),
        'layers': meta_in.get('layers', list(LAYER_OF_REL)),
        'layers_zh': LAYER_ZH,
        'layer_coverage': meta_in.get('layer_coverage', {}),
        'coverage_note': meta_in.get('coverage_note', ''),
        'corpora_zh': CORPUS_ZH,
        'engines': meta_in.get('engines', []),
        'agreement': AGREEMENT,
        'cross_validation': meta_in.get('cross_validation', 'not_run'),
        'cross_validation_note': meta_in.get('cross_validation_note', ''),
        'identity_merge': meta_in.get('identity_merge', {}),
        'publisher': meta_in.get('publisher', '医哲未来人工智能研究院 (IMPFAI)'),
        'publisher_url': meta_in.get('publisher_url', 'https://impfai.github.io/'),
        'layout': dict(meta_in.get('layout') or {}, positions_included=True),
        'upstream_deidentification_claim': meta_in.get('deidentification'),
        'derived_from': {
            'kind': 'explorer_payload' + ('+csv' if ecsv or ncsv else ''),
            'sources': dict(src),
            'layer_rule': '当代门诊病案归当代病案层；其余按关系类型的语义归层（tools/import_upstream.py: layer_of）',
            'corpus_rule': '按章节根映射到来源文献（tools/import_upstream.py: corpus_of）',
        },
        'imported_at': datetime.date.today().isoformat(),
    }
    onto = build_ontology(spec, meta['ontology_version'], onto_in['classes'], onto_in['props'], nodes, edges)
    return {'meta': meta, 'ontology': onto, 'nodes': nodes, 'edges': edges}


def from_full_kg(kg):
    """上游完整主图谱：字段原样保留，只补齐 layer / corpus，便于站点工具消费。"""
    for k in ('meta', 'ontology', 'nodes', 'edges'):
        if k not in kg:
            sys.exit(f'--kg 文件缺少顶层字段 {k}')
    for e in kg['edges']:
        cp = e.get('chapter_path') or (e.get('provenance') or [{}])[0].get('chapter_path')
        e.setdefault('corpus', corpus_of(cp))
        e.setdefault('layer', layer_of(e['type'], e['corpus']))
    kg['meta'].setdefault('layers_zh', LAYER_ZH)
    kg['meta'].setdefault('corpora_zh', CORPUS_ZH)
    kg['meta'].setdefault('derived_from', {'kind': 'full_kg'})
    kg['meta']['upstream_deidentification_claim'] = kg['meta'].pop('deidentification', None)
    kg['meta']['imported_at'] = datetime.date.today().isoformat()
    return kg


# ---------------------------------------------------------------- 原文核验
def _norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s or ''))


def check_evidence(kg, passages):
    """独立核验：原文句是否真在所引段落里。结果写入 edge['evidence_in_passage']：
    True / False；段落无法解析或原文为空时为 None。允许空白与全半角差异，
    也接受以「 / 」分隔、各段分别命中的多段引文。"""
    stats = collections.Counter()
    for e in kg['edges']:
        pid, s = e.get('passage_id'), e.get('source_sentence')
        t = passages.get(pid) if pid else None
        if t is None:
            e['evidence_in_passage'] = None; stats['passage_unresolved' if pid else 'no_passage_id'] += 1
            continue
        if not s:
            e['evidence_in_passage'] = None; stats['no_sentence'] += 1
            continue
        nt = _norm(t)
        ok = _norm(s) in nt or all(_norm(x) in nt for x in s.split(' / ') if x.strip())
        e['evidence_in_passage'] = ok
        stats[('found' if ok else 'not_found') + ('' if e.get('evidence_verbatim') else '_flagged_nonverbatim')] += 1
    return dict(stats)


# ---------------------------------------------------------------- 当代病案
def is_modern_prov(p):
    return root_of(p.get('chapter_path')) == MODERN_ROOT


def withhold_modern(kg, prev_nodes):
    """删去当代病案的逐案记录，并把受其影响的节点恢复为上一版的样子。"""
    mod_edges = [e for e in kg['edges'] if e.get('corpus') == MODERN_CORPUS]
    kg['edges'] = [e for e in kg['edges'] if e.get('corpus') != MODERN_CORPUS]
    cls_deg, mod_touch = collections.Counter(), set()
    for e in kg['edges']:
        cls_deg[e['subject_id']] += 1; cls_deg[e['object_id']] += 1
    for e in mod_edges:
        mod_touch.add(e['subject_id']); mod_touch.add(e['object_id'])

    kept, dropped, restored, stripped = [], collections.Counter(), 0, 0
    for n in kg['nodes']:
        prov = n.get('provenance') or []
        has_cls_prov = any(not is_modern_prov(p) for p in prov)
        if not (n['id'] in prev_nodes or cls_deg[n['id']] or has_cls_prov):
            dropped[n['cls']] += 1
            continue
        involved = n['id'] in mod_touch or any(is_modern_prov(p) for p in prov)
        pn = prev_nodes.get(n['id'])
        if involved and pn:
            # 受当代病案影响的旧节点：属性、别名、出处、提及数一律取上一版
            for k in ('attrs', 'aliases', 'provenance', 'n_provenance', 'n_mentions'):
                if k in pn:
                    n[k] = pn[k]
            restored += 1
        elif involved:
            n['provenance'] = [p for p in prov if not is_modern_prov(p)]
            n['n_provenance'] = len(n['provenance'])
            stripped += 1
        if pn and pn.get('x') is not None:          # 布局取上一版坐标，全图几何不变
            n['x'], n['y'] = pn['x'], pn['y']
        kept.append(n)
    kg['nodes'] = kept
    return {'edges_withheld': len(mod_edges), 'nodes_withheld': sum(dropped.values()),
            'nodes_withheld_by_class': dict(dropped.most_common()),
            'nodes_restored_from_previous_release': restored,
            'nodes_modern_provenance_stripped': stripped}


def include_modern(kg):
    """发布逐案记录：对源自当代病案的全部文本去标识化。"""
    hits = collections.Counter()

    def R(s):
        out, h = DI.redact(s); hits.update(h); return out
    for e in kg['edges']:
        if e.get('corpus') == MODERN_CORPUS:
            e['source_sentence'] = R(e.get('source_sentence'))
            for p in e.get('provenance') or []:
                p['source_sentence'] = R(p.get('source_sentence'))
    for n in kg['nodes']:
        prov = n.get('provenance') or []
        modern_node = any(is_modern_prov(p) for p in prov)
        for p in prov:
            if is_modern_prov(p) and p.get('source_sentence'):
                p['source_sentence'] = R(p['source_sentence'])
        if modern_node and n['cls'] == 'CaseRecord':
            n['attrs'] = {k: R(v) if isinstance(v, str) else v for k, v in (n.get('attrs') or {}).items()}
            n['name'] = R(n['name'])
    return dict(hits)


def modern_texts(kg_in, corpus):
    """用于推导姓名：原始（未处理）文本中所有源自当代病案的片段。"""
    ts = [p.get('text', '') for p in (corpus or {}).get('passages', []) if p.get('source') == MODERN_ROOT]
    for n in kg_in['nodes']:
        for p in n.get('provenance') or []:
            if is_modern_prov(p):
                ts.append(p.get('source_sentence') or '')
    for e in kg_in['edges']:
        if e.get('corpus') == MODERN_CORPUS:
            ts.append(e.get('source_sentence') or '')
    return ts


ID_KEYS = {'id', 'subject_id', 'object_id', 'passage_id', 'pid'}


def string_leaves(x):
    """记录中全部字符串叶子（跳过 ID 字段），供隐私闸门逐字段核验。"""
    if isinstance(x, dict):
        for k, v in x.items():
            if k not in ID_KEYS:
                yield from string_leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from string_leaves(v)
    elif isinstance(x, str) and x:
        yield x


def privacy_gate(outputs, names, strict_modern_texts):
    """写盘前的隐私闸门。outputs: {标签: 文本}；strict_modern_texts: 源自当代病案的输出文本。
    全部输出：患者抬头、身份证号、手机号、推导姓名须为 0；
    当代病案文本：另要求完整日期、月日、住院号、90 岁以上均为 0。"""
    problems, warnings = {}, {}
    for label, text in outputs.items():
        r = DI.residuals(text, names)
        for k in ('patient_header', 'national_id', 'phone', 'derived_name'):
            if r.get(k):
                (problems if label.startswith('modern') or k != 'derived_name' else warnings)[f'{label}:{k}'] = r[k]
    for i, t in enumerate(strict_modern_texts):
        r = DI.residuals(t, names)
        for k, v in r.items():
            problems[f'modern_text[{i}]:{k}'] = v
    return problems, warnings


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
    max1 = {p for p, v in onto.items() if str(v.get('card', '')).endswith('..1')}
    over = collections.Counter(t for (s, t), c in out_count.items() if t in max1 and c > 1)
    dup = collections.Counter((e['subject_id'], e['object_id'], e['type']) for e in kg['edges'])
    return {
        'domain_range_violations': len(bad_dr),
        'domain_range_examples': [f'{t}: {a}→{b}' for t, a, b in bad_dr[:5]],
        'dangling_endpoints': dangling,
        'self_loops': loops,
        'duplicate_triples': sum(c - 1 for c in dup.values() if c > 1),
        'max_cardinality_exceptions': sum(over.values()),
        'max_cardinality_exceptions_by_property': dict(over.most_common()),
        'max_cardinality_note': '按本体声明的 0..1 逐一检查：列出带多条出边的主语数。'
                                '本仓库如实报告而不改动上游声明；这些属性在 OWL 导出中不声明为 FunctionalProperty，'
                                '以免推理机据此把不同宾语合并为同一实体。',
    }


def components(kg):
    ids = [n['id'] for n in kg['nodes']]
    idset = set(ids)
    adj = collections.defaultdict(set)
    for e in kg['edges']:
        s, o = e['subject_id'], e['object_id']
        if s in idset and o in idset and s != o:
            adj[s].add(o); adj[o].add(s)
    seen, comps = set(), []
    for i in sorted(ids):
        if i in seen:
            continue
        stack, cur = [i], set()
        while stack:
            x = stack.pop()
            if x in cur:
                continue
            cur.add(x); stack.extend(adj[x] - cur)
        seen |= cur; comps.append(cur)
    comps.sort(key=lambda c: (-len(c), min(c)))
    return comps


def disease_profiles(kg, corpus='hlc_yian'):
    """病证 × 医案（默认只取《何廉臣医案》；当代门诊另有上游聚合表）。"""
    name = {n['id']: n['name'] for n in kg['nodes']}
    case_dis, case_herb, case_sym = (collections.defaultdict(set) for _ in range(3))
    for e in kg['edges']:
        if e.get('corpus') != corpus:
            continue
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


def audit(kg, profiles, n_cases_dx, evidence_stats, release):
    nodes, edges = kg['nodes'], kg['edges']
    deg = collections.Counter()
    for e in edges:
        deg[e['subject_id']] += 1; deg[e['object_id']] += 1
    by_cls = collections.Counter(n['cls'] for n in nodes)
    by_type = collections.Counter(e['type'] for e in edges)
    comps = components(kg)
    isolates = [n for n in nodes if deg[n['id']] == 0]
    verbatim = sum(1 for e in edges if e.get('evidence_verbatim'))
    single = sum(1 for e in edges if e.get('n_support', 1) == 1)
    onto = kg['ontology']
    mods = collections.Counter((n.get('attrs') or {}).get('modality') for n in nodes if n['cls'] == 'DiagnosticSign')
    mods.pop(None, None)
    pid_filled = sum(1 for e in edges if e.get('passage_id'))
    E = len(edges)
    return {
        'generated_from': {'corpora': kg['meta'].get('corpora', []),
                           'delivery': kg['meta'].get('derived_from', {}).get('kind'),
                           'imported_at': kg['meta'].get('imported_at')},
        'ontology': {
            'version': onto['version'], 'source': onto.get('source'),
            'classes_defined': len(onto['classes']), 'classes_populated': len(by_cls),
            'unpopulated_classes': sorted(set(onto['classes']) - set(by_cls)),
            'properties_defined': len(onto['object_properties']), 'properties_used': len(by_type),
            'unused_properties': sorted(set(onto['object_properties']) - set(by_type)),
            'undeclared_attrs': {c: v['undeclared_attrs'] for c, v in onto['classes'].items() if v.get('undeclared_attrs')},
        },
        'graph': {
            'n_nodes': len(nodes), 'n_edges': E,
            'nodes_by_class': dict(by_cls.most_common()),
            'edges_by_type': dict(by_type.most_common()),
            'edges_by_layer': dict(collections.Counter(e.get('layer') for e in edges).most_common()),
            'edges_by_corpus': dict(collections.Counter(e.get('corpus') or '(未映射)' for e in edges).most_common()),
            'nodes_with_relations': len(nodes) - len(isolates), 'isolated_nodes': len(isolates),
            'isolates_by_class': dict(collections.Counter(n['cls'] for n in isolates).most_common()),
            'connectivity_pct': round(100 * (len(nodes) - len(isolates)) / max(len(nodes), 1), 1),
            'n_components': len(comps), 'largest_component': len(comps[0]) if comps else 0,
            'satellite_components': sum(1 for c in comps[1:] if len(c) >= 2),
        },
        'coverage': {'layer_coverage': kg['meta'].get('layer_coverage', {}), 'note': kg['meta'].get('coverage_note', '')},
        'engines': {'edges_by_engine': dict(collections.Counter(e.get('engine') for e in edges).most_common()),
                    'cross_validation': kg['meta'].get('cross_validation', 'not_run'),
                    'agreement': dict(collections.Counter(e.get('agreement') for e in edges).most_common())},
        'provenance': {
            'passage_id_filled': f'{pid_filled}/{E}',
            'evidence_check': evidence_stats,
            'evidence_check_note': '独立核验：规范化空白与全半角后，原文句（或以「 / 」分隔的各段）是否出现在所引段落正文中。'
                                   '段落无法解析者（《绍派伤寒》专著沿用上游 p##### 编号，本仓库语料为 b##### 重切分）不计入。',
        },
        'integrity': dict(validate(kg), **{
            'edges_with_provenance': sum(1 for e in edges if e.get('provenance')),
            'edges_without_source_sentence': sum(1 for e in edges if not e.get('source_sentence')),
            'evidence_verbatim_upstream_flag': f'{verbatim}/{E} ({100 * verbatim / max(E, 1):.1f}%)',
            'single_mention_edges': f'{single}/{E} ({100 * single / max(E, 1):.1f}%)',
        }),
        'diagnostic_modalities': dict(mods.most_common()),
        'disease_layer': {
            'n_disease': by_cls.get('Disease', 0), 'diseases_with_cases': len(profiles),
            'cases_with_diagnosis': n_cases_dx,
            'n_cases': sum(1 for n in nodes if n['cls'] == 'CaseRecord'),
            'top': [{'disease': r['disease'], 'cases': r['n_cases'], 'herbs': r['signature_herbs']} for r in profiles[:12]],
        },
        'modern_case_release': release,
        'derived_copy': kg['meta'].get('derived_from', {}),
    }


# ---------------------------------------------------------------- 输出
def dump_kg(kg, path):
    """meta / ontology / vocabularies 缩进排版；nodes / edges 每条一行（便于 diff 与流式读取）。"""
    j = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    parts = ['{']
    for k in ('meta', 'ontology', 'vocabularies'):
        if k in kg:
            parts.append(f'"{k}":' + json.dumps(kg[k], ensure_ascii=False, indent=1) + ',')
    parts.append('"nodes":[\n' + ',\n'.join(j(n) for n in kg['nodes']) + '\n],')
    parts.append('"edges":[\n' + ',\n'.join(j(e) for e in kg['edges']) + '\n]')
    parts.append('}')
    Path(path).write_text('\n'.join(parts), encoding='utf-8')


def publish_corpus(corpus, include, redact_hits):
    """发布语料：默认删去当代病案段落；--include-modern-cases 时去标识化后保留。"""
    c = json.loads(json.dumps(corpus))
    mod = [p for p in c['passages'] if p.get('source') == MODERN_ROOT]
    if include:
        for p in mod:
            for k in ('text', 'title', 'comment', 'patient_desc'):
                if isinstance(p.get(k), str):
                    p[k], h = DI.redact(p[k]); redact_hits.update(h)
            for k in ('patient', 'locus'):
                if k in p:
                    p[k] = None
            # 逐次就诊日期只保留跨度（天）；就诊次数（n_visits）与年份（year）原有
            dates = p.pop('visit_dates', None) or []
            redact_hits['visit_dates'] += len(dates)
            p['visit_span_days'] = DI.span_days(dates)
            if p.get('age') not in (None, ''):
                try:
                    if int(p['age']) >= 90:
                        p['age'] = '90+'
                except ValueError:
                    p['age'] = None
            p['n_chars'] = len(p.get('text') or '')
    else:
        c['passages'] = [p for p in c['passages'] if p.get('source') != MODERN_ROOT]
        c['source_docs'] = [s for s in c.get('source_docs', []) if s != MODERN_ROOT]
    c.pop('deidentification', None)
    st = c.setdefault('stats', {})
    st['n_passages'] = len(c['passages'])
    st['n_chars'] = sum(len(p.get('text', '')) for p in c['passages'])
    c['modern_case_release'] = ('included_deidentified' if include else 'withheld') + \
        f' ({len(mod)} passages from 「{MODERN_ROOT}」)'
    return c


def publish_profiles(text, include):
    """发布当代门诊聚合表：默认删去 n_cases < MIN_K 的行；--include-modern-cases 时原样发布。"""
    rows = list(csv.DictReader(text.splitlines()))
    if not rows or 'n_cases' not in rows[0]:
        raise SystemExit('modern_case_profiles.csv 缺少 n_cases 列，无法按最小格过滤')
    keep = rows if include else [r for r in rows if int(r['n_cases'] or 0) >= MIN_K]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator='\n')
    w.writeheader(); w.writerows(keep)
    stats = {'rows': len(rows), 'rows_published': len(keep),
             'min_cases': None if include else MIN_K}
    return buf.getvalue(), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--explorer', help='上游自包含浏览器 HTML（或其 JSON 载荷）')
    src.add_argument('--kg', help='上游完整 shaopai_kg.json')
    ap.add_argument('--nodes-csv'); ap.add_argument('--edges-csv')
    ap.add_argument('--ontology', help='上游 ontology_spec.json')
    ap.add_argument('--layout', help='上游 layout_positions.json（与浏览器载荷坐标一致时可省）')
    ap.add_argument('--corpus', help='上游分段语料 corpus_yueyi.json')
    ap.add_argument('--profiles', help='上游 modern_case_profiles.csv（聚合统计）')
    ap.add_argument('--include-modern-cases', action='store_true',
                    help='发布当代病案的逐案记录（去标识化并通过核验后）。须数据方确认已获发布授权。')
    ap.add_argument('--prev', default=str(DATA / 'shaopai_kg.json'),
                    help='上一版主图谱：沿用引擎标注、受控词表与坐标（默认 data/shaopai_kg.json）')
    ap.add_argument('--out-dir', default=str(DATA))
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    prev_nodes, prev_eng, prev_vocab = read_prev(a.prev)
    spec = json.loads(Path(a.ontology).read_text(encoding='utf-8')) if a.ontology else None
    corpus = json.loads(Path(a.corpus).read_text(encoding='utf-8')) if a.corpus else None
    if a.explorer:
        payload = read_explorer_payload(a.explorer)
        kg = from_explorer(payload, prev_eng,
                           read_nodes_csv(a.nodes_csv) if a.nodes_csv else {},
                           read_edges_csv(a.edges_csv) if a.edges_csv else {}, spec)
        if a.layout:
            lay = json.loads(Path(a.layout).read_text(encoding='utf-8'))
            for n in kg['nodes']:
                if n['id'] in lay:
                    n['x'], n['y'] = lay[n['id']]
    else:
        kg = from_full_kg(json.loads(Path(a.kg).read_text(encoding='utf-8')))
    if prev_vocab and 'vocabularies' not in kg:
        kg['vocabularies'] = prev_vocab

    # 运行时从原始文本推导姓名（只在内存中，用于核验）
    names = DI.names_from_headers(modern_texts(kg, corpus))

    # ---- 当代病案：默认不发布逐案记录
    n_modern_edges = sum(1 for e in kg['edges'] if e.get('corpus') == MODERN_CORPUS)
    redact_hits = collections.Counter()
    if a.include_modern_cases:
        redact_hits.update(include_modern(kg))
        release = {'status': 'included_deidentified', 'edges': n_modern_edges}
    else:
        release = dict({'status': 'withheld'}, **withhold_modern(kg, prev_nodes))
    release['reason'] = ('当代门诊病案涉及在世患者；逐案记录须经去标识化复核并由数据方确认发布授权。'
                         '聚合统计（modern_case_profiles.csv）只发布至少 %d 例的行。' % MIN_K
                         if not a.include_modern_cases else
                         '数据方已确认发布授权；逐案记录经去标识化并通过隐私闸门后发布。')
    release['names_checked'] = len(names)
    kg['meta']['modern_case_release'] = release
    kg['meta'].pop('upstream_deidentification_claim', None)   # 该说明未经本仓库复核通过，不随发布
    # 组件编号按发布后的图重算
    comp_of = {i: k for k, c in enumerate(components(kg)) for i in c}
    for n in kg['nodes']:
        n['component'] = comp_of.get(n['id'], -1)
    # 引擎按层取众数，供页面省略与层默认值相同的引擎字段
    by_layer = collections.defaultdict(collections.Counter)
    for e in kg['edges']:
        by_layer[e['layer']][e['engine']] += 1
    kg['meta']['engine_by_layer'] = {l: c.most_common(1)[0][0] for l, c in by_layer.items()}
    kg['meta']['n_nodes'], kg['meta']['n_edges'] = len(kg['nodes']), len(kg['edges'])
    kg = {k: kg[k] for k in ('meta', 'ontology', 'vocabularies', 'nodes', 'edges') if k in kg}

    # ---- 原文核验
    passages = read_passages([a.corpus, DATA / 'corpus_shaopai.json'])
    ev_stats = check_evidence(kg, passages)

    # ---- 发布物
    corpus_out = publish_corpus(corpus, a.include_modern_cases, redact_hits) if corpus else None
    profiles, n_cases_dx = disease_profiles(kg)
    release['redactions'] = dict(redact_hits)
    prof_text = ''
    if a.profiles:
        prof_text, release['profiles'] = publish_profiles(
            Path(a.profiles).read_text(encoding='utf-8'), a.include_modern_cases)
    qc = audit(kg, profiles, n_cases_dx, ev_stats, release)
    kg_text = json.dumps(kg, ensure_ascii=False)
    outputs = {'kg': kg_text, 'qc': json.dumps(qc, ensure_ascii=False)}
    if corpus_out:
        outputs['corpus'] = json.dumps(corpus_out, ensure_ascii=False)
    if prof_text:
        outputs['modern_profiles'] = prof_text
    strict = []
    if a.include_modern_cases:
        # 源自当代病案的记录逐个字符串字段都查（ID 字段除外：节点 ID 是十六进制散列，会被误判为住院号）
        strict += [t for e in kg['edges'] if e.get('corpus') == MODERN_CORPUS for t in string_leaves(e)]
        strict += [t for n in kg['nodes'] if any(is_modern_prov(p) for p in n.get('provenance') or [])
                   for t in string_leaves(n)]
        if corpus_out:
            strict += [t for p in corpus_out['passages'] if p.get('source') == MODERN_ROOT
                       for t in string_leaves(p)]
    problems, warnings = privacy_gate(outputs, names, strict)
    if problems:
        print('隐私闸门未通过，未写入任何文件：', json.dumps(problems, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
    if warnings:
        print('提示：推导姓名在非当代文本中出现（多为古籍巧合）：', warnings, file=sys.stderr)

    dump_kg(kg, out / 'shaopai_kg.json')
    (out / 'layout_positions.json').write_text(json.dumps(
        {n['id']: [n['x'], n['y']] for n in kg['nodes'] if n.get('x') is not None},
        ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (out / 'qc_audit.json').write_text(json.dumps(qc, ensure_ascii=False, indent=1), encoding='utf-8')
    with (out / 'disease_profiles.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['disease_id', 'disease', 'n_cases', 'signature_herbs', 'signature_symptoms'])
        for r in profiles:
            w.writerow([r['disease_id'], r['disease'], r['n_cases'],
                        '、'.join(r['signature_herbs']), '、'.join(r['signature_symptoms'])])
    if corpus_out:
        (out / 'corpus_yueyi.json').write_text(json.dumps(corpus_out, ensure_ascii=False), encoding='utf-8')
    if prof_text:
        (out / 'modern_case_profiles.csv').write_text(prof_text, encoding='utf-8')

    g = qc['graph']
    print(f"节点 {g['n_nodes']:,}  关系 {g['n_edges']:,}  类 {qc['ontology']['classes_populated']}/"
          f"{qc['ontology']['classes_defined']}  关系类型 {qc['ontology']['properties_used']}/"
          f"{qc['ontology']['properties_defined']}  巨分量 {g['largest_component']:,}  孤点 {g['isolated_nodes']:,}")
    print(f"  当代病案：{release['status']}  {json.dumps({k: v for k, v in release.items() if k not in ('reason',)}, ensure_ascii=False)}")
    print(f"  来源：{kg['meta']['derived_from']['sources']}")
    print(f"  层 {g['edges_by_layer']}")
    print(f"  原文核验 {ev_stats}")
    print(f"  完整性 {json.dumps({k: v for k, v in qc['integrity'].items() if 'note' not in k}, ensure_ascii=False)}")
    print(f"  隐私闸门：通过（推导姓名 {len(names)} 个，残留 0）")


if __name__ == '__main__':
    main()
