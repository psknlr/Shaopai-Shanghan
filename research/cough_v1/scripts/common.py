"""V1 两书版图谱中的咳嗽医案数据集。

数据源：data/shaopai_kg.json 中来源文献为《俞根初临证经验集要》(ygc_jingyao) 与《何廉臣医案》(hlc_yian)
的全部关系——即站点 v1.html「V1 两书版」的同一子图（8,226 节点 / 17,498 关系，载入时校验）。
"""
import json, re, sys, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = OUT.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE))
from import_upstream import corpus_of          # noqa: E402  与站点构建同一口径
import herb_reference as H                     # noqa: E402

BOOKS = ('ygc_jingyao', 'hlc_yian')
V1_EXPECT = (8226, 17498)
COUGH = re.compile(r'[咳嗽]')


def load_v1():
    kg = json.loads((ROOT / 'data/shaopai_kg.json').read_text(encoding='utf-8'))
    edges = [e for e in kg['edges'] if e['corpus'] in BOOKS]
    ends = {x for e in edges for x in (e['subject_id'], e['object_id'])}
    nodes = [n for n in kg['nodes'] if n['id'] in ends
             or any(corpus_of(p.get('chapter_path')) in BOOKS for p in n.get('provenance') or [])]
    assert (len(nodes), len(edges)) == V1_EXPECT, (len(nodes), len(edges))
    corpus = json.loads((ROOT / 'data/corpus_yueyi.json').read_text(encoding='utf-8'))
    passages = {p['pid']: p for p in corpus['passages'] if p['source'] == '何廉臣医案'}
    return kg, nodes, edges, passages


def load_ygc():
    """《俞根初临证经验集要》段落（pid → passage），供方证判读与理法互证逐字核对。"""
    corpus = json.loads((ROOT / 'data/corpus_yueyi.json').read_text(encoding='utf-8'))
    return {p['pid']: p for p in corpus['passages'] if p['source'] == '俞根初临证经验集要'}


# ---------------------------------------------------------------- 病机归类（按关键词，优先级自上而下）
TYPE_RULES = [
    ('专病', '顿咳、肺痈等专病', r'顿咳|肺痈|脓血'),
    ('虚劳', '虚劳咳嗽（劳嗽、肺痨、阴虚、肾虚）', r'劳|痨|阴虚|肾咳|由肾传肺|肾虚|久咳成'),
    ('肝火', '肝火犯肺（木火刑金）', r'肝|木侮|木火|刑金|侮金'),
    ('湿热', '湿热咳嗽（湿温、暑湿、湿阻、酒湿）', r'湿热|湿温|暑湿|湿阻|酒湿|夹湿|湿滞|酒毒'),
    ('风邪', '外感风邪（风寒、风热、风燥、冬温）', r'风寒|风热|风燥|风嗽|伤风|冬温|秋燥|受寒'),
    ('肺热', '痰热肺热（肺热、痰火、伏火、肺燥）', r'肺热|肺火|伏火|热痰|痰火|肺燥'),
    ('痰饮', '痰饮痰阻（痰饮、寒饮、痰湿、气逆）', r'痰饮|寒饮|痰湿|痰阻|痰瘀|痰嗽|气逆|痰喘|气急|咳喘|痰浊'),
]
TYPE_OTHER = ('未明', '病机未明示')
TYPE_ORDER = [t[0] for t in TYPE_RULES] + [TYPE_OTHER[0]]
TYPE_ZH = {t[0]: t[1] for t in TYPE_RULES}
TYPE_ZH[TYPE_OTHER[0]] = TYPE_OTHER[1]


def classify(title, diags, pats):
    text = ' '.join([title] + diags + pats)
    for key, _, rx in TYPE_RULES:
        m = re.search(rx, text)
        if m:
            return key, m.group(0)
    return TYPE_OTHER[0], ''


# ---------------------------------------------------------------- 治法要素（一案可多项）
PRIN_RULES = [
    ('宣肺疏表', r'宣|疏|散|透|达表|解表|轻清|开泄|开达|辛'),
    ('肃肺降气', r'肃|降|顺气|下气|平喘|镇逆|纳气'),
    ('化痰豁痰', r'痰|化饮|涤饮'),
    ('清肺泄热', r'清肺|肃清|泻肺|清金|清痰|清上|清降|泄热|清热|清化|清宣|清燥|保肺|清肃|凉'),
    ('润燥养阴', r'润|燥|养阴|滋|救肺|生津|涵|填|育阴|甘寒'),
    ('清肝平肝', r'肝|熄风|息风|潜阳|涵木'),
    ('宁络止血', r'宁络|止血|络|血'),
    ('芳化淡渗', r'芳|淡|渗|湿|分消|宣化'),
    ('和胃调中', r'胃|调中|和中|开胃|消食|健脾|醒脾'),
    ('补益扶正', r'补|益气|扶正|培|固|健|养'),
]
PRIN_ORDER = [p[0] for p in PRIN_RULES]


def prin_elements(names):
    out = set()
    for n in names:
        for k, rx in PRIN_RULES:
            if re.search(rx, n):
                out.add(k)
    return out


# ---------------------------------------------------------------- 舌、脉、痰
PULSE_FEATS = ['浮', '沉', '数', '迟', '滑', '涩', '弦', '紧', '细', '缓', '软', '弱', '虚', '大', '洪', '芤', '搏', '滞']
PULSE_ALIAS = {'小': '细', '濡': '软', '搏': '搏'}
TONGUE_BODY = ['红', '绛', '淡', '紫']
COAT_COLOR = ['白', '黄', '灰', '黑']
COAT_TEXTURE = ['薄', '厚', '腻', '滑', '燥', '润', '糙']


def pulse_sides(name):
    """「脉右浮滑左弦数」→ {'右': {浮, 滑}, '左': {弦, 数}}；未分左右者归「双手」。"""
    s = name.replace('脉', '', 1) if name.startswith('脉') else name
    s = re.sub(r'[，,、。；;（）()]', '', s)
    out = collections.defaultdict(set)
    parts = re.findall(r'([左右])([^左右]*)', s)
    head = re.split(r'[左右]', s)[0]
    if head:
        parts = [('双手', head)] + parts
    if not parts:
        parts = [('双手', s)]
    for side, seg in parts:
        seg = ''.join(PULSE_ALIAS.get(c, c) for c in seg)
        for f in PULSE_FEATS:
            if f in seg:
                out[side].add(f)
    return out


def tongue_feats(name):
    out = set()
    if '苔' in name:
        body, coat = name.split('苔', 1)
    else:
        body, coat = name, ''
    body = body.replace('舌', '')
    if '淡红' in body:
        out.add('舌淡红')
        body = body.replace('淡红', '')
    for c in TONGUE_BODY:
        if c in body:
            out.add('舌' + c)
    if '无苔' in name or '少苔' in name or '光' in name:
        out.add('少苔/无苔')
    for c in COAT_COLOR:
        if c in coat:
            out.add('苔' + c)
    for t in COAT_TEXTURE:
        if t in coat:
            out.add('苔' + t)
    if not coat:
        for t in ('燥', '润'):
            if t in body:
                out.add('舌' + t)
    return out


SPUTUM_RULES = [
    ('痰白', r'白痰|痰白|稀白|白沫|白粘|吐白'),
    ('痰黄', r'黄痰|痰黄|黄稠|吐黄|黄白'),
    ('痰中带血', r'血|带红'),
    ('痰稠粘', r'稠|粘|胶|浓'),
    ('痰稀', r'稀|沫'),
    ('咯痰不爽', r'不爽|不出|难'),
    ('痰多', r'痰多|甚多|多痰|痰甚'),
    ('干咳少痰', r'干咳|无痰|痰少|咳少痰'),
]
SPUTUM_ORDER = [s[0] for s in SPUTUM_RULES]

SYM_MERGE = {'肢懈无力': '肢懈', '溺短热': '溺热', '溺赤热': '溺热', '溺黄热': '溺热', '溺短赤': '溺热',
             '胃不健': '胃钝', '胃纳不健': '胃钝', '胸胁痛': '胁痛', '头晕目眩': '头晕'}


# ---------------------------------------------------------------- 剂量
_CN = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
UNIT_QIAN = {'钱': 1.0, '两': 10.0, '分': 0.1}
DOSE_RX = re.compile(r'^([一二三四五六七八九十两]*)(钱|两|分)(半)?(?:([一二三四五六七八九十]+)分)?')
COUNT_RX = re.compile(r'^([一二三四五六七八九十百卅廿两]+)\s*小?(枚|个|片|朵|支|尺|寸|帚|张|对|粒|匙|只|茎|扎|颗|盅|瓢|滴)')
SKIP_RX = re.compile(r'^\s*(?:[（(][^）)]{0,6}[）)]|\[\]|各)\s*')
NUMERAL = set('一二三四五六七八九十两半钱分卅廿百')
TYPO = {'浅': '钱', '辆': '两'}
# 可疑剂量：与该药常用量相差一个数量级，疑为原文或录入之误，不计入剂量统计
DOSE_SUSPECT = {('白芍', 50.0): '「生白芍五两」疑为「五钱」之误'}


def _cn_int(s):
    if not s:
        return 1
    if s == '十':
        return 10
    if '十' in s:
        a, b = s.split('十')
        return (_CN.get(a, 1) if a else 1) * 10 + (_CN.get(b, 0) if b else 0)
    return _CN.get(s, 0)


def _dose_at(rest):
    m = DOSE_RX.match(rest)
    if m and (m.group(1) or m.group(3) or m.group(2) == '钱'):
        val = _cn_int(m.group(1)) * UNIT_QIAN[m.group(2)]
        if m.group(3):
            val += 0.5 * UNIT_QIAN[m.group(2)]
        if m.group(4):
            val += _cn_int(m.group(4)) * 0.1
        return round(val, 3), 'weight'
    if COUNT_RX.match(rest):
        return None, 'count'
    return None, None


def parse_dose(sentence, surfaces):
    """在原文句中定位药名，解析其后的剂量；返回 (钱数 或 None, 单位类别)。

    药名与剂量之间允许隔一处括注（如「（杵）」「（冲）」）、「各」字，或至多两个非数字字
    （如「桂枝木四分」「广皮红钱半」——图谱药名较原文少一两字）。
    """
    s = ''.join(TYPO.get(c, c) for c in sentence)
    for name in surfaces:
        i = s.find(name)
        if i < 0:
            continue
        rest = s[i + len(name):]
        for _ in range(3):
            rest = SKIP_RX.sub('', rest, count=1)
        val, kind = _dose_at(rest)
        if kind:
            return val, kind
        k = 0
        while k < 2 and k < len(rest) and rest[k] not in NUMERAL and '一' <= rest[k] <= '龥':
            k += 1
            val, kind = _dose_at(SKIP_RX.sub('', rest[k:], count=1))
            if kind:
                return val, kind
        return None, 'none'
    return None, 'notfound'


def usage_flags(sentence, raw):
    """鲜药、煎汤代水、拌药同煎。"""
    i = sentence.find(raw)
    fresh = i >= 0 and '鲜' in sentence[max(0, i - 3):i]
    daishui = bool(re.search(r'先用|代水|煎汤', sentence))
    ban = '拌' in sentence
    return fresh, daishui, ban


# ---------------------------------------------------------------- 数据集
def case_uid(pid):
    return 'H' + pid[3:7]


def build():
    kg, nodes, edges, passages = load_v1()
    byid = {n['id']: n for n in kg['nodes']}
    out = collections.defaultdict(list)
    for e in edges:
        if e['corpus'] == 'hlc_yian':
            out[e['subject_id']].append(e)
    cases = [n for n in nodes if n['cls'] == 'CaseRecord']

    def names(cid, t):
        return [byid[e['object_id']]['name'] for e in out[cid] if e['type'] == t]

    recs = []
    for c in cases:
        es = out[c['id']]
        pids = sorted({e['passage_id'] for e in es if e['passage_id'].startswith('hlc')})
        diag, pats = names(c['id'], 'caseDiagnosedAs'), names(c['id'], 'caseShowsPattern')
        syms = names(c['id'], 'caseShowsSymptom')
        by_title = bool(COUGH.search(c['name']))
        by_diag = any(COUGH.search(d) for d in diag)
        by_sym = any(COUGH.search(s) for s in syms)
        herb_edges = [e for e in es if e['type'] == 'caseUsesHerb']
        recs.append(dict(id=c['id'], uid=case_uid(pids[0]) if pids else '', pid=pids[0] if pids else '',
                         title=c['name'], diag=diag, pats=pats, syms=syms,
                         signs=[(byid[e['object_id']]['name'], byid[e['object_id']]['attrs'].get('modality'))
                                for e in es if e['type'] == 'caseShowsSign'],
                         prins=names(c['id'], 'caseAppliesPrinciple'), formulas=names(c['id'], 'caseUsesFormula'),
                         herb_edges=herb_edges, by_title=by_title, by_diag=by_diag, by_sym=by_sym))
    return kg, nodes, edges, passages, byid, recs


def herbs_of(rec):
    """一案的规范化单味药集合、成药集合，以及逐条用药记录（含剂量）。"""
    singles, patents, rows = set(), set(), []
    for e in rec['herb_edges']:
        raw = e['object_name']
        sent = e['source_sentence'] or ''
        # 抽取伪影：「青盐陈皮」被拆出「青盐」；「苏梗通」被拆出「苏梗」
        if raw == '青盐' and '青盐陈皮' in sent:
            continue
        if raw == '苏梗' and '苏梗通' in sent:
            continue
        std, note, is_patent = H.normalize(raw)
        dose, kind = parse_dose(sent, [raw, std, raw[-2:]])
        suspect = DOSE_SUSPECT.get((std, dose))
        fresh, daishui, ban = usage_flags(sent, raw)
        rows.append(dict(raw=raw, std=std, note=note, patent=is_patent, dose=None if suspect else dose,
                         dose_raw=dose, dose_kind=kind, suspect=suspect or '', fresh=fresh, daishui=daishui,
                         ban=ban, place=raw in H.PLACE_LABELLED, sentence=sent, passage_id=e['passage_id']))
        (patents if is_patent else singles).add(std)
    return singles, patents, rows


def select(recs):
    """纳入：医案标题或诊断含「咳」「嗽」；排除：图谱中无用药关系者。"""
    cand = [r for r in recs if r['by_title'] or r['by_diag']]
    included = [r for r in cand if r['herb_edges']]
    excluded = [r for r in cand if not r['herb_edges']]
    extended = [r for r in recs if (r['by_title'] or r['by_diag'] or r['by_sym']) and r['herb_edges']]
    return cand, included, excluded, extended
