#!/usr/bin/env python3
"""
从 data/ 重建站点内嵌数据。

  python3 tools/build_payload.py

读取 data/shaopai_kg.json、data/layout_positions.json，
生成 explorer.html 的内嵌图谱与 index.html 的预览子集。

新增节点若无坐标，用「固定已有节点、只松弛新节点」的力导向布局求解：
既让新节点贴近其已有邻居，又保证既有坐标一字不动——
上游承诺「每次渲染可复现」，重排全图会毁掉这个性质。
"""
import json, math, re, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PV_CAP = 8          # 内嵌副本每节点保留的出处条数；完整出处在 data/shaopai_kg.json


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
    ids = {n['id'] for n in kg['nodes']}
    adj = collections.defaultdict(set)
    for e in kg['edges']:
        s, o = e['subject_id'], e['object_id']
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
    关系  s o t · n 支撑次数 · l 层 · ev 原文 · ch 章节路径 · pid 段落编号 · v 逐字
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
             'n': e.get('n_support', 1), 'l': layer,
             'ev': e.get('source_sentence') or p.get('source_sentence', ''),
             'ch': e.get('chapter_path') or p.get('chapter_path', ''),
             'v': bool(e.get('evidence_verbatim', p.get('evidence_verbatim')))}
        pid = e.get('passage_id') or p.get('passage_id')
        if pid:
            o['pid'] = pid
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
           'MedicalFamily', 'Dosage']


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

    cc = collections.Counter(n['c'] for n in payload['nodes'])
    print(f'节点 {len(payload["nodes"]):,}  关系 {len(payload["edges"]):,}'
          f'  新布局 {n_new}  内嵌 {len(body.encode())/1024/1024:.2f} MB'
          f'  预览 {len(pv["n"])} 节点 / {len(pv["e"])} 关系')
    for k, v in cc.most_common():
        print(f'  {k:18s} {v:6,d}')


if __name__ == '__main__':
    main()
