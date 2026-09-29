#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出「沈钦荣门诊医案」本地查阅文件——不随网站公开，只在持有者本机的浏览器里读取。

  U=path/to/upstream_delivery
  python3 tools/export_modern_cases.py --explorer $U/shaopai_explorer.html \\
      --nodes-csv $U/nodes.csv --edges-csv $U/edges.csv --ontology $U/ontology_spec.json \\
      --corpus $U/corpus_yueyi.json --out ~/shaopai_modern_cases.local.json

然后打开图谱浏览器 explorer.html（或 explorer.html?cases）→ 顶栏「沈钦荣医案」→ 选择这个文件。
文件只由浏览器本地读取，不上传任何服务器；勾选「记住」时存于本浏览器的 IndexedDB，可随时清除。
载入后可用 explorer.html?case=case-YYYY-NNN 直达某案。

- 去标识化与 import_upstream.py --include-modern-cases 同一套规则（tools/deidentify.py）：行内患者
  抬头改写为「患者（性别，年龄）」、住院号删除、日历日期只留年份、逐次就诊日期改为跨度天数、
  90 岁以上合并。写盘前对输出的每一个字符串字段做严格核验（患者抬头、完整日期、月日、住院号、
  身份证号、手机号、运行时推导出的姓名），任何残留都会中止、不写文件。
- 只含网站未发布的部分：当代病案的全部关系，以及只由它引出的实体；已公开的实体只以 ID 引用。
- 新实体的坐标按公开布局求解（已公开节点固定不动，只松弛新节点），与网站图谱的几何一致。
- 默认拒绝写入仓库目录，避免误提交；*.local.json 已列入 .gitignore。
"""
import argparse, collections, json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_upstream as I  # noqa: E402
import deidentify as DI  # noqa: E402

FORMAT = 'shaopai-modern-cases'
CASE_FIELDS = [  # 医案摘要：关系类型 → 字段
    ('caseWesternDiagnosis', 'wd'), ('caseDiagnosedAs', 'tcm'), ('caseShowsPattern', 'pat'),
    ('caseAppliesPrinciple', 'prin'), ('caseUsesFormula', 'fml'), ('caseUsesHerb', 'herb'),
    ('caseUsesProcedure', 'proc'), ('caseUsesWesternDrug', 'drug'), ('caseHasExamination', 'exam'),
    ('caseShowsSymptom', 'sym'), ('caseShowsSign', 'sign'), ('caseComorbidity', 'com'),
]
SKIP = {'i', 's', 'o', 'pid', 'p'}       # 标识字段不参与隐私核验（十六进制散列会被误判为编号）


def place(new_ids, edges, pos, iters=240, seed=11):
    """为未公开的实体求坐标：已公开实体固定，新实体先落在已定位邻居的质心，再做局部松弛。"""
    import numpy as np
    rng = np.random.default_rng(seed)
    nbr = collections.defaultdict(set)
    for e in edges:
        s, o = e['subject_id'], e['object_id']
        if s != o:
            nbr[s].add(o); nbr[o].add(s)
    P = {k: tuple(v) for k, v in pos.items()}
    todo = list(new_ids)
    for _ in range(12):                       # 逐层外推：先放有已定位邻居的
        rest = []
        for i in todo:
            ps = [P[j] for j in nbr[i] if j in P]
            if ps:
                c = np.mean(ps, axis=0)
                P[i] = (float(c[0] + rng.normal(0, 0.012)), float(c[1] + rng.normal(0, 0.012)))
            else:
                rest.append(i)
        if not rest or len(rest) == len(todo):
            todo = rest; break
        todo = rest
    for k, i in enumerate(todo):              # 与图无连接的（理论上没有）：放到右下角
        P[i] = (1.2 + 0.02 * (k % 20), -1.2 - 0.02 * (k // 20))
    ids = list(new_ids)
    idx = {i: k for k, i in enumerate(ids)}
    X = np.array([P[i] for i in ids], dtype=float)
    pairs = [(idx[i], j) for i in ids for j in nbr[i]]
    src = np.array([a for a, _ in pairs], dtype=int)
    dst_new = np.array([idx.get(j, -1) for _, j in pairs], dtype=int)
    dst_fix = np.array([P[j] if j not in idx else (0.0, 0.0) for _, j in pairs], dtype=float)
    for it in range(iters):
        t = 0.02 * (1 - it / iters) + 0.001
        D = np.zeros_like(X)
        tgt = np.where(dst_new[:, None] >= 0, X[np.clip(dst_new, 0, None)], dst_fix)
        d = tgt - X[src]
        np.add.at(D, src, d * 0.08)                       # 沿边的引力
        diff = X[:, None, :] - X[None, :, :]              # 新实体之间的斥力（近距离才起作用）
        d2 = (diff ** 2).sum(-1) + np.eye(len(X))
        rep = np.where(d2 < 0.004, 2e-5 / d2, 0.0)
        D += (diff * rep[..., None]).sum(1)
        n = np.linalg.norm(D, axis=1, keepdims=True) + 1e-12
        X += D / n * np.minimum(n, t)
    return {i: (round(float(X[k, 0]), 4), round(float(X[k, 1]), 4)) for i, k in idx.items()}


def leaves(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k not in SKIP:
                yield from leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from leaves(v)
    elif isinstance(x, str) and x:
        yield x


def uniq(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--explorer', required=True, help='上游自包含浏览器 HTML（或其 JSON 载荷）')
    ap.add_argument('--nodes-csv'); ap.add_argument('--edges-csv')
    ap.add_argument('--ontology', help='上游 ontology_spec.json')
    ap.add_argument('--corpus', required=True, help='上游分段语料 corpus_yueyi.json（含当代病案段落）')
    ap.add_argument('--public', default=str(I.DATA / 'shaopai_kg.json'), help='网站发布的图谱（用于判断哪些实体已公开）')
    ap.add_argument('--layout', default=str(I.DATA / 'layout_positions.json'), help='网站发布的布局坐标')
    ap.add_argument('--out', default='shaopai_modern_cases.local.json')
    ap.add_argument('--allow-in-repo', action='store_true', help='允许写入仓库目录（不建议）')
    a = ap.parse_args()
    out = Path(a.out).expanduser().resolve()
    if (I.ROOT == out or I.ROOT in out.parents) and not a.allow_in_repo:
        sys.exit(f'拒绝写入仓库目录（{out}）：这是不公开的病案数据。请指定仓库外的路径，或确需时加 --allow-in-repo。')

    spec = json.loads(Path(a.ontology).read_text(encoding='utf-8')) if a.ontology else None
    corpus = json.loads(Path(a.corpus).read_text(encoding='utf-8'))
    kg = I.from_explorer(I.read_explorer_payload(a.explorer), {},
                         I.read_nodes_csv(a.nodes_csv) if a.nodes_csv else {},
                         I.read_edges_csv(a.edges_csv) if a.edges_csv else {}, spec)
    names = DI.names_from_headers(I.modern_texts(kg, corpus))      # 只在内存中，用于核验
    hits = collections.Counter(I.include_modern(kg))
    corpus_out = I.publish_corpus(corpus, True, hits)
    mpass = {p['pid']: p for p in corpus_out['passages'] if p.get('source') == I.MODERN_ROOT}
    I.check_evidence(kg, {pid: p.get('text', '') for pid, p in mpass.items()})

    public = json.loads(Path(a.public).read_text(encoding='utf-8'))
    pub_ids = {n['id'] for n in public['nodes']}
    layout = json.loads(Path(a.layout).read_text(encoding='utf-8'))
    N = {n['id']: n for n in kg['nodes']}
    medges = [e for e in kg['edges'] if e.get('corpus') == I.MODERN_CORPUS]
    ends = {x for e in medges for x in (e['subject_id'], e['object_id'])}
    new_ids = sorted(i for i in ends if i not in pub_ids)
    xy = place(new_ids, medges, layout)

    # ---- 实体（与 explorer.html 内嵌格式一致）
    out_nodes, case_nodes = [], []
    for i in new_ids:
        n = N[i]
        prov = [p for p in (n.get('provenance') or []) if I.is_modern_prov(p)]
        o = {'i': i, 'n': n['name'], 'c': n['cls'], 'm': n.get('n_mentions', 0),
             'x': xy[i][0], 'y': xy[i][1], 'k': -1}          # k（连通分量）由浏览器并入后重算
        if n['cls'] != 'CaseRecord':                 # 医案的编号、年份、病家、就诊跨度在 cases[] 里，界面单列摘要
            if n.get('aliases'):
                o['a'] = n['aliases']
            at = {k: v for k, v in (n.get('attrs') or {}).items() if v not in (None, '', [])}
            if at:
                o['at'] = at
        pv = [{'s': p.get('source_sentence') or '', 'c': p.get('chapter_path') or ''} for p in prov[:8]]
        o['pvn'] = len(prov)
        if pv:
            o['pv'] = pv
        out_nodes.append(o)
        if n['cls'] == 'CaseRecord':
            case_nodes.append(o)

    # ---- 关系
    out_edges = []
    for e in medges:
        o = {'s': e['subject_id'], 'o': e['object_id'], 't': e['type'], 'n': e.get('n_support', 1),
             'l': e.get('layer', 'modern_case'), 'cp': I.MODERN_CORPUS, 'ev': e.get('source_sentence') or '',
             'ch': e.get('chapter_path') or '', 'v': bool(e.get('evidence_verbatim'))}
        if e.get('passage_id'):
            o['pid'] = e['passage_id']
        if e.get('evidence_in_passage') is False:
            o['ip'] = 0
        if e.get('engine'):
            o['en'] = e['engine']
        out_edges.append(o)

    # ---- 医案摘要（浏览器的医案列表与检索用）
    by_case = collections.defaultdict(list)
    for e in medges:
        by_case[e['subject_id']].append(e)
    cases = []
    for o in case_nodes:
        es = by_case.get(o['i'], [])
        pids = collections.Counter(e.get('passage_id') for e in es if e.get('passage_id'))
        pid = pids.most_common(1)[0][0] if pids else None
        p = mpass.get(pid, {})
        rec = {'i': o['i'], 'n': o['n'], 'pid': pid, 'code': p.get('case_code'), 'year': p.get('year'),
               'sex': p.get('sex') or '', 'age': p.get('age') or '', 'visits': p.get('n_visits'),
               'span': p.get('visit_span_days'), 'title': p.get('title') or '', 'text': p.get('text') or ''}
        for t, k in CASE_FIELDS:
            rec[k] = uniq(N[e['object_id']]['name'] for e in es if e['type'] == t)
        cases.append(rec)                        # 去标识化的原文在 rec['text']，详情面板单列一卡
    cases.sort(key=lambda r: (str(r['code'] or ''), r['n']))

    doc = {'format': FORMAT, 'version': 1, 'deidentified': True,
           'note': '沈钦荣 2022—2026 年骨伤科门诊病案，已去标识化。不随网站公开，只供持有者本机查阅，请勿转发或上传。',
           'counts': {'cases': len(cases), 'nodes': len(out_nodes), 'edges': len(out_edges)},
           'redactions': dict(hits), 'names_checked': len(names),
           'nodes': out_nodes, 'edges': out_edges, 'cases': cases}

    # ---- 写盘前的严格核验：每个字符串字段
    problems = collections.Counter()
    for t in leaves(doc):
        for k, v in DI.residuals(t, names).items():
            problems[k] += v
    if problems:
        sys.exit(f'隐私核验未通过，未写入：{dict(problems)}')
    out.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'已写入 {out}（{out.stat().st_size / 1e6:.2f} MB）：{len(cases)} 则医案、{len(out_nodes)} 个未公开实体、'
          f'{len(out_edges)} 条关系；去标识化 {dict(hits)}；核验推导姓名 {len(names)} 个，残留 0')


if __name__ == '__main__':
    main()
