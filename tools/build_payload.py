#!/usr/bin/env python3
"""
从 data/ 重建站点内嵌数据。

  python3 tools/build_payload.py

读取 data/shaopai_kg.json、data/layout_positions.json，
生成 explorer.html 的内嵌图谱与 index.html 的预览子集；
再以 explorer.html 为模板生成特殊版本页面（EDITIONS，目前为 v1.html「V1 两书版」）。

新增节点若无坐标，用「固定已有节点、只松弛新节点」的力导向布局求解：
既让新节点贴近其已有邻居，又保证既有坐标一字不动——
上游承诺「每次渲染可复现」，重排全图会毁掉这个性质。
"""
import json, math, re, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PV_CAP = 8          # 内嵌副本每节点保留的出处条数；完整出处在 data/shaopai_kg.json
sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_upstream import corpus_of  # noqa: E402  章节根 → 来源文献键，与导入口径一致

# 特殊版本：同一份 explorer.html 代码，只注入指定几部书的子图，另存为独立页面。
# books 为 corpus 键，顺序即页面下拉框的顺序。
EDITIONS = [{
    'id': 'v1', 'file': 'v1.html', 'label': 'V1', 'name': '两书版',
    'books': ['ygc_jingyao', 'hlc_yian'],
    # 本图谱没有《三订通俗伤寒论》原书语料；以引其为出处、辑述俞根初学说与六经方药的
    # 《俞根初临证经验集要》代之，书名如实注明，关系出处仍标该书章节与段落。
    'book_zh': {'ygc_jingyao': '《三订通俗伤寒论》（据《俞根初临证经验集要》）',
                'hlc_yian': '《何廉臣医案》'},
    'book_short': {'ygc_jingyao': '三订通俗伤寒论', 'hlc_yian': '何廉臣医案'},
    'subtitle': '三订通俗伤寒论 × 何廉臣医案',
    'all_books': '两书合览',
}]


def load():
    kg = json.loads((DATA / 'shaopai_kg.json').read_text(encoding='utf-8'))
    pos = {}
    p = DATA / 'layout_positions.json'
    if p.exists():
        pos = {k: tuple(v) for k, v in json.loads(p.read_text(encoding='utf-8')).items()}
    comp = components(kg)
    # kg 自带坐标作为兜底
    for n in kg['nodes']:
        if n['id'] not in pos and n.get('x') is not None:
            pos[n['id']] = (n['x'], n['y'])
    return kg, pos, comp


def components(kg):
    """连通分量：按大小降序编号，0 为巨分量。"""
    return components_of({n['id'] for n in kg['nodes']},
                         ((e['subject_id'], e['object_id']) for e in kg['edges']))


def components_of(ids, pairs):
    adj = collections.defaultdict(set)
    for s, o in pairs:
        if s in ids and o in ids and s != o:
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
    return {i: k for k, c in enumerate(comps) for i in c}


def layout_new(kg, pos, iters=320, seed=7):
    """为缺坐标的节点求位置；已有坐标全部锁定。"""
    ids = [n['id'] for n in kg['nodes']]
    new = [i for i in ids if i not in pos]
    if not new:
        return pos, 0
    idset = set(ids)
    adj = collections.defaultdict(set)
    for e in kg['edges']:
        s, o = e['subject_id'], e['object_id']
        if s in idset and o in idset and s != o:
            adj[s].add(o); adj[o].add(s)

    # 新节点初值：有已定位邻居的落在邻居质心附近；
    # 无锚点的成团放到既有内容**下方**，而不是一路向右延伸——
    # 后者会让画布越拉越宽，全景视图里满是空白。
    xs_ = [p[0] for p in pos.values()] or [0.0]
    ys_ = [p[1] for p in pos.values()] or [0.0]
    right = max(xs_)
    cy0 = (min(ys_) + max(ys_)) / 2
    rnd = _Rand(seed)
    P = dict(pos)
    loose = [i for i in new if not any(j in pos for j in adj[i])]
    rad = 0.35 + 0.55 * math.sqrt(max(len(loose), 1) / 60)
    li = 0
    for i in new:
        anchors = [P[j] for j in adj[i] if j in P]
        if anchors:
            ax = sum(a[0] for a in anchors) / len(anchors)
            ay = sum(a[1] for a in anchors) / len(anchors)
            P[i] = (ax + rnd.uni(-.06, .06), ay + rnd.uni(-.06, .06))
        else:
            ang = li * 2.399963229728653     # 黄金角
            r = rad * math.sqrt((li + 1) / max(len(loose), 1))
            P[i] = (right + rad + 0.3 + r * math.cos(ang), cy0 + r * math.sin(ang))
            li += 1

    newset = set(new)
    k_rep = 0.0016
    for it in range(iters):
        t = 0.09 * (1 - it / iters) + 0.004
        disp = {i: [0.0, 0.0] for i in new}
        # 斥力只在新节点之间算（O(n²) 但 n 有限），避免把已有布局挤变形
        for a in range(len(new)):
            ia = new[a]; xa, ya = P[ia]
            for b in range(a + 1, len(new)):
                ib = new[b]; xb, yb = P[ib]
                dx, dy = xa - xb, ya - yb
                d2 = dx * dx + dy * dy or 1e-9
                if d2 > .36:      # 远处忽略
                    continue
                f = k_rep / d2
                disp[ia][0] += dx * f; disp[ia][1] += dy * f
                disp[ib][0] -= dx * f; disp[ib][1] -= dy * f
        # 引力沿边；一端固定时全部位移给新节点
        for i in new:
            for j in adj[i]:
                if j not in P:
                    continue
                dx, dy = P[i][0] - P[j][0], P[i][1] - P[j][1]
                d = math.hypot(dx, dy) or 1e-9
                f = d * 0.045 * (1.0 if j in newset else 1.6)
                disp[i][0] -= dx / d * f; disp[i][1] -= dy / d * f
        for i in new:
            dx, dy = disp[i]
            d = math.hypot(dx, dy) or 1e-9
            s = min(d, t) / d
            P[i] = (P[i][0] + dx * s, P[i][1] + dy * s)
    return P, len(new)


class _Rand:
    """确定性伪随机——布局必须可复现。"""
    def __init__(self, seed): self.s = seed & 0xFFFFFFFF
    def next(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF
    def uni(self, a, b): return a + (b - a) * self.next()


def compact(kg, pos, comp):
    """页面内嵌格式。字段名极短以控制体积；空字段一律省略。

    节点  i id · n 名称 · c 类 · m 提及次数 · x y 坐标 · k 连通分量 · a 别名 · at 属性
          pvn 出处总数 · pv [{s 原文, c 章节路径, p 段落编号, v 逐字}]
    关系  s o t · n 支撑次数 · l 层 · cp 来源文献 · ev 原文 · ch 章节路径 · pid 段落编号 · v 逐字
          en 引擎（仅当与 meta.engine_by_layer 推定值不同时给出）· d dn r cd 剂量/角色/条件
    """
    onto = kg['ontology']
    eng_by_layer = kg['meta'].get('engine_by_layer', {})
    nodes = []
    for n in kg['nodes']:
        xy = pos.get(n['id'])
        if not xy:
            continue
        o = {'i': n['id'], 'n': n['name'], 'c': n['cls'],
             'm': n.get('n_mentions', 0),
             'x': round(xy[0], 4), 'y': round(xy[1], 4),
             'k': comp.get(n['id'], -1)}
        if n.get('aliases'):
            o['a'] = n['aliases']
        at = {k: v for k, v in (n.get('attrs') or {}).items() if v not in (None, '', [])}
        if at:
            o['at'] = at
        pv = n.get('provenance') or []
        o['pvn'] = n.get('n_provenance', len(pv))
        if pv:
            lst = []
            for p in pv[:PV_CAP]:
                item = {}
                if p.get('source_sentence'):
                    item['s'] = p['source_sentence']
                if p.get('chapter_path'):
                    item['c'] = p['chapter_path']
                if p.get('passage_id'):
                    item['p'] = p['passage_id']
                if 'evidence_verbatim' in p:
                    item['v'] = bool(p['evidence_verbatim'])
                if item:
                    lst.append(item)
            if lst:
                o['pv'] = lst
        nodes.append(o)
    ids = {n['i'] for n in nodes}
    edges = []
    for e in kg['edges']:
        if e['subject_id'] not in ids or e['object_id'] not in ids:
            continue
        p = (e.get('provenance') or [{}])[0]
        layer = e.get('layer', '')
        o = {'s': e['subject_id'], 'o': e['object_id'], 't': e['type'],
             'n': e.get('n_support', 1), 'l': layer, 'cp': e.get('corpus', ''),
             'ev': e.get('source_sentence') or p.get('source_sentence', ''),
             'ch': e.get('chapter_path') or p.get('chapter_path', ''),
             'v': bool(e.get('evidence_verbatim', p.get('evidence_verbatim')))}
        pid = e.get('passage_id') or p.get('passage_id')
        if pid:
            o['pid'] = pid
        if e.get('evidence_in_passage') is False:      # 独立核验未在所引段落中找到原文
            o['ip'] = 0
        en = e.get('engine') or p.get('engine')
        if en and en != eng_by_layer.get(layer):
            o['en'] = en
        for k, short in (('dose', 'd'), ('dose_note', 'dn'), ('role', 'r'), ('condition', 'cd')):
            if e.get(k):
                o[short] = e[k]
        edges.append(o)
    meta = dict(kg['meta'])
    for k in ('derived_from',):
        meta.pop(k, None)
    return {'meta': meta,
            'onto': {'classes': {k: v['zh'] for k, v in onto['classes'].items()},
                     'props': {k: v['zh'] for k, v in onto['object_properties'].items()}},
            'nodes': nodes, 'edges': edges}


# 顺序即页面预览的配色下标（index.html 的 COL 数组），勿随意调整
CLS_IDX = ['Physician', 'Work', 'Doctrine', 'DiagnosticSign', 'Pattern',
           'Formula', 'Herb', 'TreatmentPrinciple', 'CaseRecord',
           'Disease', 'Symptom', 'HerbProperty', 'Institution', 'Place',
           'MedicalFamily', 'Dosage', 'WesternDiagnosis', 'Procedure', 'WesternDrug', 'Examination']


def preview(payload, cap=420):
    """主页预览子集：按度数取前 cap 个节点及其间的关系。医案标题冗长且数量多，
    只保留度数很高者，避免预览被 657 则医案淹没。"""
    deg = collections.Counter()
    for e in payload['edges']:
        deg[e['s']] += 1; deg[e['o']] += 1
    thr = {'Physician': 5, 'Work': 3, 'Doctrine': 2, 'DiagnosticSign': 2, 'Pattern': 2,
           'Formula': 3, 'Herb': 4, 'TreatmentPrinciple': 3, 'CaseRecord': 40,
           'Disease': 3, 'Symptom': 6, 'HerbProperty': 2, 'Institution': 2, 'Place': 3,
           'MedicalFamily': 2}
    keep = [n for n in payload['nodes'] if deg[n['i']] >= thr.get(n['c'], 2)]
    keep.sort(key=lambda n: -deg[n['i']])
    keep = keep[:cap]
    idx = {n['i']: k for k, n in enumerate(keep)}
    return {'n': [[n['n'], CLS_IDX.index(n['c']) if n['c'] in CLS_IDX else 0,
                   n['x'], n['y'], deg[n['i']]] for n in keep],
            'e': [[idx[e['s']], idx[e['o']]] for e in payload['edges']
                  if e['s'] in idx and e['o'] in idx]}


def edition_payload(payload, ed):
    """特殊版本的子图：只留 ed['books'] 的关系，及这些关系的端点、在这些书中有出处的节点。

    - 节点出处只留这几部书的条目；「提及次数」是全库统计、无法分书，故不带。
    - 连通分量按子图重算。有关系的节点沿用完整图谱坐标；子图中无关系的节点
      （孤点）按向日葵排布重铺成紧贴主体的一圈，密度与完整图谱的孤点圈相同。
    """
    books = set(ed['books'])
    edges = [e for e in payload['edges'] if e['cp'] in books]
    ends = {x for e in edges for x in (e['s'], e['o'])}
    nodes = []
    for n in payload['nodes']:
        pv = [p for p in n.get('pv', []) if corpus_of(p.get('c')) in books]
        if n['i'] not in ends and not pv:
            continue
        o = {k: v for k, v in n.items() if k not in ('m', 'pv', 'pvn')}
        if pv:
            o['pv'] = pv
        o['pvn'] = len(pv)
        nodes.append(o)
    comp = components_of({n['i'] for n in nodes}, ((e['s'], e['o']) for e in edges))
    for n in nodes:
        n['k'] = comp.get(n['i'], -1)

    # 孤点圈：以完整图谱孤点圈的面密度为准
    deg_full = collections.Counter()
    for e in payload['edges']:
        deg_full[e['s']] += 1; deg_full[e['o']] += 1
    core_full = [n for n in payload['nodes'] if deg_full[n['i']]]
    iso_full = [n for n in payload['nodes'] if not deg_full[n['i']]]
    cx0, cy0 = _center(core_full)
    r_iso = [math.hypot(n['x'] - cx0, n['y'] - cy0) for n in iso_full] or [1.0]
    rmax_core = max(math.hypot(n['x'] - cx0, n['y'] - cy0) for n in core_full)
    gap = max(min(r_iso) - rmax_core, 0.02)
    density = len(iso_full) / max(math.pi * (max(r_iso) ** 2 - min(r_iso) ** 2), 1e-9)

    core = [n for n in nodes if n['i'] in ends]
    iso = sorted((n for n in nodes if n['i'] not in ends),
                 key=lambda n: (CLS_IDX.index(n['c']) if n['c'] in CLS_IDX else 99, n['n'], n['i']))
    cx, cy = _center(core)
    r0 = max(math.hypot(n['x'] - cx, n['y'] - cy) for n in core) + gap
    r1 = math.sqrt(r0 ** 2 + len(iso) / density / math.pi)
    for k, n in enumerate(iso):
        r = math.sqrt(r0 ** 2 + (r1 ** 2 - r0 ** 2) * (k + 0.5) / len(iso))
        a = k * 2.399963229728653                  # 黄金角
        n['x'], n['y'] = round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)

    src = payload['meta']
    meta = {k: src[k] for k in ('title', 'ontology_version', 'year', 'layers', 'layers_zh',
                                'engine_by_layer', 'agreement', 'publisher', 'publisher_url') if k in src}
    meta['corpora_zh'] = dict(src.get('corpora_zh', {}), **ed['book_zh'])
    meta['corpora_short'] = ed['book_short']
    meta['n_nodes'], meta['n_edges'] = len(nodes), len(edges)
    by_book = collections.Counter(e['cp'] for e in edges)
    meta['edition'] = {
        'id': ed['id'], 'label': ed['label'], 'name': ed['name'], 'books': ed['books'],
        'subtitle': ed['subtitle'], 'all_books': ed['all_books'],
        'edges_by_book': {b: by_book[b] for b in ed['books']},
        'credit_html': '底本' + '与'.join(ed['book_zh'][b] for b in ed['books']),
        'about_html': about_v1(ed, by_book, payload['onto']['props'], edges),
    }
    return {'meta': meta, 'onto': payload['onto'], 'nodes': nodes, 'edges': edges}


def _center(nodes):
    xs = [n['x'] for n in nodes]; ys = [n['y'] for n in nodes]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def about_v1(ed, by_book, props, edges):
    """V1 两书版「使用说明 · 关于本版」。计数占位（hn / he / hgc / hiso）由页面脚本填入。"""
    def top(book, k=6):
        c = collections.Counter(e['t'] for e in edges if e['cp'] == book)
        return '、'.join(props.get(t, t) for t, _ in c.most_common(k))
    return (
        '<b>关于本版</b><br>'
        f'<b>{ed["label"]} {ed["name"]}</b>只收两部书的关系：<b>《三订通俗伤寒论》</b>与<b>《何廉臣医案》</b>，'
        '共 <b id="hn"></b> 个节点、<b id="he"></b> 条关系。顶栏「来源文献」可在两书之间切换，'
        '也可再按抽取层、关系类型与诊法模态筛选；点顶栏「完整图谱」返回全部八种文献。<br><br>'
        '<b>《三订通俗伤寒论》一侧</b>：本图谱尚未收入该书原文。本版取沈钦荣编著《俞根初临证经验集要》代之——'
        '该书以《三订通俗伤寒论》为引文出处，辑述俞根初生平、学术观点、诊法特色、用药心法，'
        '以及发汗、和解、攻下、温热、滋补、清凉六类方剂。'
        f'共 {by_book["ygc_jingyao"]:,} 条关系（{top("ygc_jingyao")}等），'
        '每条关系的出处仍如实标注《俞根初临证经验集要》的章节与段落编号。<br><br>'
        f'<b>《何廉臣医案》</b>：{by_book["hlc_yian"]:,} 条关系（{top("hlc_yian")}等）。<br><br>'
        '节点坐标沿用完整图谱：<b id="hgc"></b> 个节点的巨分量居中；在两书中有出处而尚无关系的 '
        '<b id="hiso"></b> 个节点铺在最外一圈，可点「孤点」隐藏。「提及次数」是全库统计、无法分书，本版不显示。<br><br>'
        '全部关系为单模型抽取，尚未交叉验证。本站仅供学术研究与文献检索之用，不作为临床诊疗依据。')


def render_edition(template, ed, payload):
    """以 explorer.html 为模板生成特殊版本页面：替换内嵌数据、标题、描述与加载页字样。"""
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    pat = re.compile(r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)
    m = pat.search(template)
    html = template[:m.start(2)] + body + template[m.end(2):]
    meta = payload['meta']
    books = '与'.join(ed['book_zh'][b] for b in ed['books'])
    subs = [
        (re.compile(r'<title>.*?</title>', re.S),
         f'<title>绍派伤寒知识图谱 {ed["label"]} {ed["name"]} · {ed["subtitle"]} | 沈钦荣名中医 × 医哲未来人工智能研究院</title>'),
        (re.compile(r'<meta name="description" content="[^"]*">'),
         f'<meta name="description" content="绍派伤寒知识图谱 {ed["label"]} {ed["name"]}：只收{books}两书的 '
         f'{meta["n_nodes"]:,} 个节点、{meta["n_edges"]:,} 条关系，每条关系附段落编号与原文，'
         '可按书、抽取层、关系类型与诊法模态检索，逐条核验原文出处。">'),
        (re.compile(r'<div class="s">KNOWLEDGE GRAPH</div>'),
         f'<div class="s">KNOWLEDGE GRAPH · {ed["label"]}</div>'),
    ]
    for rx, new in subs:
        html, k = rx.subn(lambda _m, new=new: new, html, count=1)
        if k != 1:
            sys.exit(f'模板缺少 {rx.pattern}，无法生成 {ed["file"]}')
    return html, len(body.encode())


def inject(path, script_id, text):
    p = ROOT / path
    s = p.read_text(encoding='utf-8')
    pat = re.compile(r'(<script id="%s" type="application/json">)(.*?)(</script>)' % script_id, re.S)
    m = pat.search(s)
    if not m:
        sys.exit(f'{path}: 未找到 <script id="{script_id}">')
    p.write_text(s[:m.start(2)] + text + s[m.end(2):], encoding='utf-8')


def main():
    kg, pos, comp = load()
    pos, n_new = layout_new(kg, pos)
    if n_new:
        (DATA / 'layout_positions.json').write_text(
            json.dumps({k: [round(v[0], 5), round(v[1], 5)] for k, v in pos.items()},
                       ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    payload = compact(kg, pos, comp)
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    inject('explorer.html', 'data', body)
    pv = preview(payload)
    inject('index.html', 'preview', json.dumps(pv, ensure_ascii=False, separators=(',', ':')))
    template = (ROOT / 'explorer.html').read_text(encoding='utf-8')
    for ed in EDITIONS:
        ep = edition_payload(payload, ed)
        html, size = render_edition(template, ed, ep)
        (ROOT / ed['file']).write_text(html, encoding='utf-8')
        print(f'{ed["file"]}（{ed["label"]} {ed["name"]}）：节点 {len(ep["nodes"]):,}  关系 {len(ep["edges"]):,}'
              f'  内嵌 {size/1024/1024:.2f} MB  {ep["meta"]["edition"]["edges_by_book"]}')

    cc = collections.Counter(n['c'] for n in payload['nodes'])
    print(f'节点 {len(payload["nodes"]):,}  关系 {len(payload["edges"]):,}'
          f'  新布局 {n_new}  内嵌 {len(body.encode())/1024/1024:.2f} MB'
          f'  预览 {len(pv["n"])} 节点 / {len(pv["e"])} 关系')
    for k, v in cc.most_common():
        print(f'  {k:18s} {v:6,d}')


if __name__ == '__main__':
    main()
