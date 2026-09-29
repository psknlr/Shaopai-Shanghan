"""咳嗽医案用药规律统计：全部结果写入 results/（JSON 供作图，CSV 供核对与制表）。

  python3 scripts/analysis.py
"""
import csv, json, math, re, itertools, statistics, collections
import numpy as np
import networkx as nx
from scipy.cluster.hierarchy import linkage, fcluster, cophenet, dendrogram
from scipy.spatial.distance import pdist, squareform
from scipy.stats import fisher_exact, spearmanr

import common as C
import herb_reference as H

RES = C.OUT / 'results'
SUP = C.OUT / 'supplementary'
RES.mkdir(exist_ok=True)
SUP.mkdir(exist_ok=True)

HIGH_FREQ_PCT = 10          # 高频药物：使用频率 ≥ 10%
RULE_MIN_SUP, RULE_MIN_CONF = 0.20, 0.70
NET_MIN_CO = 13             # 网络边：共现 ≥ 13 案（≈10%）
MAIN_TYPE_MIN_N = 10        # 组间比较只纳入 n ≥ 10 的病机类别
LOUVAIN_SEED = 7

# 俞根初方证：图谱 formulaTreats 关系中主治含咳、嗽、痰、喘、肺者，再逐条判读与咳嗽的关系和来源性质
YU_KEY = re.compile(r'[咳嗽]|痰|喘|肺')
YU_COUGH = re.compile(r'[咳嗽]|咯痰')
YU_WIN = 80                 # 段落中方名前后 80 字内论及咳嗽、咯痰者，亦视为直接论治咳嗽
YU_MODERN = re.compile(r'\[J\]|［J］|\[J］|［J\]|教授|医生|医师|名中医|\d+例|\d+\s*g\b|\d+\s*克')
YU_ALIAS = {'小青龙': '小青龙汤'}      # 图谱中同一方剂的两种写法
# 仅字面命中「痰、喘、肺」而主治不属肺系咳喘者（人工判读，理由写入附表 S6）
YU_NOT_LUNG = {
    ('抵当汤', '产后伤寒身热恶露为热搏不下烦闷胀喘狂言'): '产后蓄血证，喘为兼症',
    ('桃仁承气汤', '产后伤寒身热恶露为热搏不下烦闷胀喘狂言'): '产后蓄血证，喘为兼症',
    ('柴胡枳桔汤', '伤寒兼疟之痰疟（肺胃'): '痰疟',
    ('柴胡达原饮', '伤寒兼疟之痰疟（膜原'): '痰疟',
    ('越婢加半夏汤', '伤寒兼疟之痰疟（肺胃'): '痰疟',
    ('犀羚三汁饮', '痰瘀'): '清宣包络痰瘀（神志病）',
    ('玳瑁郁金汤', '痰火'): '清宣包络痰火（神志病）',
    ('玳瑁郁金汤', '痰迷清窍'): '痰迷清窍、神识昏蒙（神志病）',
    ('柴胡陷胸汤', '痰浊'): '痰浊瘀阻型胸痹',
    ('蒿芩清胆汤', '痰浊'): '少阳胆经郁热夹痰湿',
    ('新加白虎汤', '肝胃心肺'): '清肝胃、辛凉心肺，非专主肺系',
}
# 理法互证：俞根初论述（逐字节录，运行时核对为段落原文子串）↔ 何廉臣咳嗽医案统计
YU_HE = [
    ('dose', '用药轻灵，剂量多在三钱内', [('ygc0210', '从俞氏一般经验来说，药量多在三钱之内')]),
    ('fresh', '喜用鲜药，煎汤代水', [('ygc0210', '俞氏常用之鲜品，有鲜生姜、鲜竹茹、鲜葱白、鲜石斛、鲜枇杷叶、鲜茉莉花、鲜荷叶、鲜冬瓜皮、鲜银花、鲜薄荷、鲜茅根等'),
                                  ('ygc0231', '煎汤代水：鲜淡竹茹、鲜枇杷叶、活水芦笋、鲜茅根')]),
    ('wind', '伤风咳嗽，轻宣肺气', [('ygc0390', '此方是俞根初在三拗汤的基础上加荆芥穗、桔梗、薄荷、金橘饼、生甘草、大蜜枣而成'),
                                ('ygc0392', '先与新加三拗汤减轻麻黄、重加牛蒡微散风寒以解表')]),
    ('phlegm', '夹痰饮咳嗽，化痰降逆', [('ygc0392', '寒伤肺而夹痰饮者，头痛发热，恶寒无汗，鼻鸣气喘，咳嗽多痰，清白稀薄'),
                                   ('ygc0392', '轻则新加三拗汤增姜、夏、橘红，重则小青龙汤')]),
    ('pulse', '夹痰火咳嗽，右浮滑、左弦', [('ygc0431', '风伤肺而夹痰火者'), ('ygc0431', '痰多黄浊稠粘'),
                                     ('ygc0431', '右寸浮滑，左手弦缓者'), ('ygc0431', '治疗轻则葱豉桔梗汤加杏仁、橘红，重则越婢加半夏汤')]),
    ('liver', '清肝保肺，宁络止血', [('ygc0886', '以桑丹泻白汤清肝保肺'),
                                ('ygc1001', '胁痛咳血者，桑丹泻白汤加地锦（五钱）、竹沥、梨汁（各两瓢，冲），泻火清金以保肺')]),
    ('dry', '燥痰便闭，润降化痰', [('ygc0665', '秋燥伤寒，若犹痰多、便闭、腹痛者，则用五仁橘皮汤，加全瓜蒌（四钱，生姜四分拌，捣极烂）、干薤白（四枚，白酒洗捣）、紫菀（四钱）、前胡（二钱）')]),
    ('yin', '阴虚咳嗽，滋阴润肺', [('ygc0350', '为阴虚体感冒风温，及冬温咳嗽，咽干痰结之良剂')]),
    ('transform', '失治传变，防成劳损', [('ygc0390', '失治误治，往往延久不愈，酿成肺病，轻变痰饮痰火，重变肺胀肺痨')]),
]


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def write_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def ranked(counter):
    """按计数降序、名称升序排列（显式并列规则，结果不随哈希种子变化）。"""
    return sorted(counter.items(), key=lambda x: (-x[1], x[0]))


def q(x, p):
    return float(np.percentile(x, p, method='linear'))


def main():
    kg, nodes, edges, passages, byid, recs = C.build()
    cand, inc, exc, ext = C.select(recs)
    N = len(inc)
    R = {}

    # ------------------------------------------------ 逐案整理
    cases = []
    for r in inc:
        singles, patents, rows = C.herbs_of(r)
        typ, hit = C.classify(r['title'], r['diag'], r['pats'])
        p = passages.get(r['pid'], {})
        n_visits = max(1, len(re.findall(r'[二三四五六七八九十]诊', p.get('text', ''))) + 1) if p else 1
        syms = {C.SYM_MERGE.get(s, s) for s in r['syms']}
        tongue, pulse = set(), collections.defaultdict(set)
        for name, mod in r['signs']:
            if name.startswith('脉') or mod == '脉诊':
                for side, fs in C.pulse_sides(name).items():
                    pulse[side] |= fs
            elif '舌' in name or '苔' in name or mod == '舌诊':
                tongue |= C.tongue_feats(name)
        sputum_text = ' '.join([r['title']] + [s for s in r['syms'] if re.search('[咳嗽痰]', s)])
        sputum = {k for k, rx in C.SPUTUM_RULES if re.search(rx, sputum_text)}
        blood = bool(re.search(r'血|带红', ' '.join([r['title']] + r['diag'] + r['syms'])))
        cases.append(dict(
            id=r['id'], uid=r['uid'], pid=r['pid'], title=r['title'], by_title=r['by_title'], by_diag=r['by_diag'],
            diag=r['diag'], pats=r['pats'], type=typ, type_hit=hit, n_visits=n_visits,
            herbs=sorted(singles), patents=sorted(patents), rows=rows,
            prins=r['prins'], prin_el=sorted(C.prin_elements(r['prins'])), formulas=r['formulas'],
            syms=sorted(syms), sputum=sorted(sputum), tongue=sorted(tongue),
            pulse={k: sorted(v) for k, v in pulse.items()}, blood=blood))
    T = [set(c['herbs']) for c in cases]

    # ------------------------------------------------ 表1 基本特征
    nh = [len(c['herbs']) for c in cases]
    rows_all = [x for c in cases for x in c['rows']]
    single_rows = [x for x in rows_all if not x['patent']]
    visits = collections.Counter(c['n_visits'] for c in cases)
    R['summary'] = dict(
        v1_nodes=C.V1_EXPECT[0], v1_edges=C.V1_EXPECT[1], hlc_cases=sum(1 for r in recs),
        candidates=len(cand), cand_title=sum(r['by_title'] for r in cand), cand_diag=sum(r['by_diag'] for r in cand),
        cand_both=sum(r['by_title'] and r['by_diag'] for r in cand),
        excluded=[dict(uid=r['uid'], title=r['title'], reason='图谱中无用药关系（原文有方，抽取缺失）') for r in exc],
        included=N, inc_title_only=sum(c['by_title'] and not c['by_diag'] for c in cases),
        inc_diag_only=sum(c['by_diag'] and not c['by_title'] for c in cases),
        inc_both=sum(c['by_title'] and c['by_diag'] for c in cases),
        visits=dict(sorted(visits.items())), multi_visit=sum(v for k, v in visits.items() if k > 1),
        herbs_mean=round(statistics.mean(nh), 2), herbs_sd=round(statistics.stdev(nh), 2),
        herbs_median=statistics.median(nh), herbs_q1=q(nh, 25), herbs_q3=q(nh, 75), herbs_min=min(nh), herbs_max=max(nh),
        raw_spellings=len({x['raw'] for x in single_rows}), distinct_herbs=len(set().union(*T)),
        herb_uses=sum(nh),
        patent_cases=sum(1 for c in cases if c['patents']), patent_kinds=len({p for c in cases for p in c['patents']}),
        patent_uses=sum(len(c['patents']) for c in cases),
        dose_rows=len(single_rows), dose_weight=sum(1 for x in single_rows if x['dose'] is not None),
        dose_count=sum(1 for x in single_rows if x['dose_kind'] == 'count'),
        dose_suspect=[dict(raw=x['raw'], dose=x['dose_raw'], note=x['suspect']) for x in single_rows if x['suspect']],
        extended=len(ext),
    )

    # ------------------------------------------------ 药物频次与药性
    freq = collections.Counter(h for t in T for h in t)
    raw_of = collections.defaultdict(collections.Counter)
    for c in cases:
        for x in c['rows']:
            if not x['patent']:
                raw_of[x['std']][x['raw']] += 1
    hf_min = math.ceil(N * HIGH_FREQ_PCT / 100)

    def prop(h):
        return H.PROPS.get(h)

    def cat(h):
        p = prop(h)
        if p:
            return p['cat'], p['sub']
        return H.CAT_UNRESOLVED.get(h, ('未归类', ''))

    herb_rows = []
    for rank, (h, n) in enumerate(sorted(freq.items(), key=lambda x: (-x[1], x[0])), 1):
        p = prop(h) or {}
        herb_rows.append(dict(rank=rank, herb=h, n=n, pct=pct(n, N), cat=cat(h)[0], sub=cat(h)[1],
                              qi=p.get('qi', ''), wei='、'.join(p.get('wei', [])), gui='、'.join(p.get('gui', [])),
                              tox=p.get('tox', ''), src=H.SRC_ZH.get(p.get('src', ''), ''), note=p.get('note', '') or H.UNRESOLVED.get(h, ''),
                              raw='、'.join(f'{k}（{v}）' if len(raw_of[h]) > 1 else k for k, v in raw_of[h].most_common())))
    R['herbs'] = herb_rows
    R['high_freq_min'] = hf_min
    high = [r['herb'] for r in herb_rows if r['n'] >= hf_min]
    R['high_freq'] = high
    write_csv(RES / 'herb_frequency.csv', ['序号', '规范药名', '频次（案）', '频率/%', '功效大类', '功效亚类', '四气', '五味', '归经', '毒性', '原书写法（次）', '依据', '备注'],
              [[r['rank'], r['herb'], r['n'], r['pct'], r['cat'], r['sub'], r['qi'], r['wei'], r['gui'], r['tox'], r['raw'], r['src'], r['note']] for r in herb_rows])

    # 功效分类（以药次计）
    cat_uses, cat_kinds = collections.Counter(), collections.defaultdict(set)
    for h, n in freq.items():
        k = cat(h)[0]
        cat_uses[k] += n
        cat_kinds[k].add(h)
    tot = sum(freq.values())
    R['categories'] = [dict(cat=k, uses=v, pct=pct(v, tot), kinds=len(cat_kinds[k]),
                            top='、'.join(sorted(cat_kinds[k], key=lambda h: (-freq[h], h))[:5])) for k, v in ranked(cat_uses)]

    # 四气五味归经（以药次计，仅计性味明确者）
    qi, wei, gui = collections.Counter(), collections.Counter(), collections.Counter()
    qi_k, wei_k, gui_k = collections.Counter(), collections.Counter(), collections.Counter()
    covered = 0
    for h, n in freq.items():
        p = prop(h)
        if not p:
            continue
        covered += n
        g = H.QI_GROUP[p['qi']]
        qi[g] += n
        qi_k[g] += 1
        for w in {H.wei_base(w) for w in p['wei']}:
            wei[w] += n
            wei_k[w] += 1
        for x in p['gui']:
            gui[x] += n
            gui_k[x] += 1
    R['properties'] = dict(
        covered_uses=covered, total_uses=tot, coverage_pct=pct(covered, tot),
        excluded=[dict(herb=h, n=n, why=H.UNRESOLVED.get(h, '性味待核')) for h, n in ranked(freq) if not prop(h)],
        qi=[dict(k=k, uses=qi[k], pct=pct(qi[k], covered), kinds=qi_k[k]) for k in H.QI_ORDER],
        wei=[dict(k=k, uses=wei[k], pct=pct(wei[k], covered), kinds=wei_k[k]) for k in H.WEI_ORDER],
        gui=[dict(k=k, uses=gui[k], pct=pct(gui[k], covered), kinds=gui_k[k]) for k in H.GUI_ORDER if gui[k]],
        qi_detail=dict(ranked(collections.Counter(prop(h)['qi'] for h in freq if prop(h)))),
    )
    # 附表 S3：性味归经功效对照
    write_csv(SUP / 'S3_herb_properties.csv', ['规范药名', '频次', '四气', '五味', '归经', '毒性', '功效大类', '功效亚类', '依据', '备注'],
              [[r['herb'], r['n'], r['qi'], r['wei'], r['gui'], r['tox'], r['cat'], r['sub'], r['src'], r['note']] for r in herb_rows])

    # ------------------------------------------------ 剂量与用药特色
    by_herb_dose = collections.defaultdict(list)
    for x in single_rows:
        if x['dose'] is not None:
            by_herb_dose[x['std']].append(x['dose'])
    dose_stats = []
    for h in high:
        d = by_herb_dose.get(h, [])
        if len(d) >= 5:
            dose_stats.append(dict(herb=h, n=len(d), median=statistics.median(d), q1=q(d, 25), q3=q(d, 75),
                                   min=min(d), max=max(d), values=sorted(d)))
    all_d = [x['dose'] for x in single_rows if x['dose'] is not None]
    R['dose'] = dict(
        by_herb=dose_stats, n=len(all_d), median=statistics.median(all_d), q1=q(all_d, 25), q3=q(all_d, 75),
        le2=pct(sum(1 for v in all_d if v <= 2), len(all_d)), le3=pct(sum(1 for v in all_d if v <= 3), len(all_d)),
        gt5=pct(sum(1 for v in all_d if v > 5), len(all_d)),
        heavy_n=sum(1 for v in all_d if v > 5),
        heavy=collections.Counter(x['std'] for x in single_rows if x['dose'] is not None and x['dose'] > 5).most_common(8),
        by_cat={k: statistics.median(v) for k, v in _group(single_rows, lambda x: cat(x['std'])[0]).items() if len(v) >= 20},
    )
    write_csv(RES / 'dose_by_herb.csv', ['规范药名', '剂量记录数', '中位数/钱', 'P25/钱', 'P75/钱', '最小/钱', '最大/钱'],
              [[d['herb'], d['n'], d['median'], d['q1'], d['q3'], d['min'], d['max']] for d in dose_stats])

    def case_has(fn):
        return sum(1 for c in cases if any(fn(x) for x in c['rows']))
    # 相拌、鲜药、煎汤代水按医案原文段落判读：图谱用药关系的原文句多只截取该药本身（如「飞滑石四钱」），
    # 「拌」「鲜」「煎汤代水」等修饰常落在句外，逐句判读会漏计
    def ptext(c):
        return passages.get(c['pid'], {}).get('text', '')
    BAN_RX, DAISHUI_RX = re.compile('拌'), re.compile('代水|煎汤代')
    fresh_by_case = {c['id']: {x['std'] for x in c['rows'] if not x['patent']
                               and (x['fresh'] or re.search('鲜' + re.escape(x['raw']), ptext(c)))} for c in cases}
    fresh_herbs = collections.Counter(h for v in fresh_by_case.values() for h in v)
    examples = ['保和丸三钱拌滑石四钱', '旋覆花二钱拌辰砂一钱', '先用鲜冬瓜皮三两 桑枝二两 煎汤代水']
    for ex_ in examples:
        assert any(ex_ in ptext(c) for c in cases), ex_
    R['features'] = [
        dict(k='丸散成药入煎', cases=sum(1 for c in cases if c['patents']), rows=R['summary']['patent_uses'],
             note='、'.join(f'{k}（{v}）' for k, v in collections.Counter(p for c in cases for p in c['patents']).most_common(6))),
        dict(k='药物相拌同煎', cases=sum(1 for c in cases if BAN_RX.search(ptext(c))), rows=sum(len(BAN_RX.findall(ptext(c))) for c in cases),
             note=f'如「{examples[0]}」「{examples[1]}」'),
        dict(k='标注产地（道地）', cases=case_has(lambda x: x['place']), rows=sum(1 for x in single_rows if x['place']),
             note='、'.join(k for k, _ in collections.Counter(x['raw'] for x in single_rows if x['place']).most_common(8))),
        dict(k='使用鲜药', cases=sum(1 for v in fresh_by_case.values() if v), rows=sum(len(v) for v in fresh_by_case.values()),
             note='、'.join(f'鲜{k}（{v}）' for k, v in ranked(fresh_herbs)[:6])),
        dict(k='先煎代水', cases=sum(1 for c in cases if DAISHUI_RX.search(ptext(c))), rows=sum(len(DAISHUI_RX.findall(ptext(c))) for c in cases),
             note=f'如「{examples[2]}」'),
    ]
    for f in R['features']:
        f['pct'] = pct(f['cases'], N)

    # ------------------------------------------------ 关联规则（Apriori）
    def sup(s):
        return sum(1 for t in T if s <= t) / N
    L1 = [h for h, v in freq.items() if v / N >= RULE_MIN_SUP]
    L2 = [frozenset(p) for p in itertools.combinations(sorted(L1), 2) if sup(frozenset(p)) >= RULE_MIN_SUP]
    L2set = set(L2)
    L3 = sorted({a | b for a, b in itertools.combinations(L2, 2) if len(a | b) == 3
                 and all(frozenset(x) in L2set for x in itertools.combinations(a | b, 2)) and sup(a | b) >= RULE_MIN_SUP}, key=sorted)
    rules = []
    for s in L2 + L3:
        for k in range(1, len(s)):
            for ant in itertools.combinations(sorted(s), k):
                ant = frozenset(ant)
                con = s - ant
                conf = sup(s) / sup(ant)
                lift = conf / sup(con)
                if conf >= RULE_MIN_CONF and lift > 1:
                    rules.append(dict(ant=sorted(ant, key=lambda h: (-freq[h], h)), con=sorted(con, key=lambda h: (-freq[h], h)),
                                      n=round(sup(s) * N), support=round(sup(s) * 100, 1), confidence=round(conf * 100, 1), lift=round(lift, 2)))
    rules.sort(key=lambda r: (-r['confidence'], -r['support'], -r['lift']))
    R['rules'] = rules
    R['itemsets'] = dict(L1=len(L1), L2=len(L2), L3=len(L3),
                         pairs=[dict(items=sorted(s, key=lambda h: (-freq[h], h)), n=round(sup(s) * N), support=round(sup(s) * 100, 1))
                                for s in sorted(L2, key=lambda s: -sup(s))])
    write_csv(RES / 'association_rules.csv', ['前项', '后项', '案数', '支持度/%', '置信度/%', '提升度'],
              [['+'.join(r['ant']), '+'.join(r['con']), r['n'], r['support'], r['confidence'], r['lift']] for r in rules])

    # ------------------------------------------------ 共现网络与社区
    co = collections.Counter()
    for t in T:
        for a, b in itertools.combinations(sorted(t & set(high)), 2):
            co[(a, b)] += 1
    G = nx.Graph()
    for h in high:
        G.add_node(h, freq=freq[h])
    for (a, b), w in co.items():
        if w >= NET_MIN_CO:
            G.add_edge(a, b, weight=w)
    comms = nx.community.louvain_communities(G, weight='weight', seed=LOUVAIN_SEED)
    comms = sorted([sorted(c, key=lambda h: (-freq[h], h)) for c in comms], key=lambda c: (-len(c), -freq[c[0]], c[0]))
    strength = dict(G.degree(weight='weight'))
    degree = dict(G.degree())
    btw = nx.betweenness_centrality(G, weight=lambda u, v, d: 1.0 / d['weight'])
    R['network'] = dict(
        min_co=NET_MIN_CO, nodes=[dict(herb=h, freq=freq[h], degree=degree[h], strength=strength[h], betweenness=round(btw[h], 4),
                                        community=next(i for i, c in enumerate(comms) if h in c)) for h in G.nodes],
        edges=[dict(a=a, b=b, w=d['weight']) for a, b, d in G.edges(data=True)],
        communities=comms, modularity=round(nx.community.modularity(G, comms, weight='weight'), 3),
        isolated=[h for h in G.nodes if degree[h] == 0],
    )
    write_csv(RES / 'network_nodes.csv', ['药物', '频次', '度', '加权度', '介数中心性', '社区'],
              [[n['herb'], n['freq'], n['degree'], n['strength'], n['betweenness'], n['community'] + 1]
               for n in sorted(R['network']['nodes'], key=lambda n: -n['strength'])])

    # ------------------------------------------------ 层次聚类（Jaccard 距离，平均联接）
    X = np.array([[1 if h in t else 0 for h in high] for t in T], dtype=bool)
    Dv = pdist(X.T, metric='jaccard')
    Z = linkage(Dv, method='average')
    coph, _ = cophenet(Z, Dv)
    Dm = squareform(Dv)
    sil = {}
    for k in range(3, 11):
        lab = fcluster(Z, k, criterion='maxclust')
        sil[k] = _silhouette(Dm, lab)
    best_k = max(sil, key=sil.get)
    lab = fcluster(Z, best_k, criterion='maxclust')
    dn = dendrogram(Z, labels=high, no_plot=True)
    clusters = collections.defaultdict(list)
    for h, l in zip(high, lab):
        clusters[int(l)].append(h)
    order = dn['ivl']
    cl_list = sorted(clusters.values(), key=lambda c: order.index(c[0]))
    R['cluster'] = dict(method='Jaccard 距离，类平均法（UPGMA）', cophenetic=round(float(coph), 3),
                        silhouette={k: round(v, 3) for k, v in sil.items()}, k=best_k,
                        clusters=[sorted(c, key=lambda h: (-freq[h], h)) for c in cl_list], order=order, Z=Z.tolist(), labels=high,
                        jaccard_sim=(1 - Dm).round(3).tolist())

    # ------------------------------------------------ 病机类别 × 治法 × 用药
    type_n = collections.Counter(c['type'] for c in cases)
    main_types = [t for t in C.TYPE_ORDER if type_n[t] >= MAIN_TYPE_MIN_N and t != '未明']
    R['types'] = dict(order=C.TYPE_ORDER, zh=C.TYPE_ZH, n={t: type_n[t] for t in C.TYPE_ORDER}, main=main_types,
                      rules=[dict(key=k, zh=z, rx=rx) for k, z, rx in C.TYPE_RULES])
    heat_herbs = []
    for t in main_types:
        sub = [c for c in cases if c['type'] == t]
        f = collections.Counter(h for c in sub for h in c['herbs'])
        for h, _ in f.most_common(8):
            if h not in heat_herbs:
                heat_herbs.append(h)
    heat_herbs.sort(key=lambda h: -freq[h])
    cells = []
    for h in heat_herbs:
        for t in main_types:
            a = sum(1 for c in cases if c['type'] == t and h in c['herbs'])
            b = type_n[t] - a
            c_ = sum(1 for c in cases if c['type'] != t and h in c['herbs'])
            d = (N - type_n[t]) - c_
            orr, p = fisher_exact([[a, b], [c_, d]], alternative='greater')
            cells.append(dict(herb=h, type=t, n=a, pct=pct(a, type_n[t]), p=p))
    _bh(cells)
    for c in cells:                                 # 保留 6 位有效数字（更多位数无统计意义）
        c['p'], c['q'] = float(f"{c['p']:.6g}"), float(f"{c['q']:.6g}")
    R['type_herb'] = dict(herbs=heat_herbs, types=main_types, cells=cells)
    pcells = []
    for el in C.PRIN_ORDER:
        for t in main_types:
            a = sum(1 for c in cases if c['type'] == t and el in c['prin_el'])
            pcells.append(dict(el=el, type=t, n=a, pct=pct(a, type_n[t])))
    R['type_prin'] = dict(elements=C.PRIN_ORDER, types=main_types, cells=pcells,
                          overall={el: sum(1 for c in cases if el in c['prin_el']) for el in C.PRIN_ORDER},
                          cases_with_prin=sum(1 for c in cases if c['prins']))
    tab6 = []
    for t in C.TYPE_ORDER:
        sub = [c for c in cases if c['type'] == t]
        if not sub:
            continue
        f = collections.Counter(h for c in sub for h in c['herbs'])
        pe = collections.Counter(e for c in sub for e in c['prin_el'])
        tab6.append(dict(type=t, zh=C.TYPE_ZH[t], n=len(sub), pct=pct(len(sub), N),
                         herbs='、'.join(f'{h}（{pct(v, len(sub)):.0f}%）' for h, v in f.most_common(8)),
                         prins='、'.join(f'{e}（{v}）' for e, v in pe.most_common(3)),
                         examples='；'.join(c['title'] for c in sub[:3])))
    R['type_table'] = tab6

    # ------------------------------------------------ 四诊：伴随症状、痰象、舌象、脉象
    sym_c = collections.Counter(s for c in cases for s in c['syms'] if not re.search('[咳嗽痰]', s))
    R['symptoms'] = [dict(k=k, n=v, pct=pct(v, N)) for k, v in sym_c.most_common(16)]
    R['sputum'] = [dict(k=k, n=sum(1 for c in cases if k in c['sputum']), pct=pct(sum(1 for c in cases if k in c['sputum']), N)) for k in C.SPUTUM_ORDER]
    tongue_cases = sum(1 for c in cases if c['tongue'])
    tc = collections.Counter(f for c in cases for f in c['tongue'])
    R['tongue'] = dict(cases=tongue_cases, feats=[dict(k=k, n=v, pct=pct(v, tongue_cases)) for k, v in tc.most_common() if v >= 3])
    pulse_cases = sum(1 for c in cases if c['pulse'])
    sides = {'右': collections.Counter(), '左': collections.Counter(), '双手': collections.Counter()}
    for c in cases:
        for side, fs in c['pulse'].items():
            sides[side].update(fs)
    R['pulse'] = dict(cases=pulse_cases, side_cases={s: sum(1 for c in cases if s in c['pulse']) for s in sides},
                      feats=[dict(k=f, right=sides['右'][f], left=sides['左'][f], both=sides['双手'][f])
                             for f in C.PULSE_FEATS if sides['右'][f] + sides['左'][f] + sides['双手'][f] >= 3])
    R['blood_cases'] = sum(1 for c in cases if c['blood'])

    # ------------------------------------------------ 症、舌、脉 × 药物（提升度）
    feats = {}
    for s in [x['k'] for x in R['symptoms'][:8]]:
        feats[s] = {c['id'] for c in cases if s in c['syms']}
    for k in ['痰黄', '痰白', '痰中带血', '咯痰不爽', '干咳少痰']:
        feats[k] = {c['id'] for c in cases if k in c['sputum']}
    for k in ['舌红', '苔腻', '苔黄', '苔白', '苔滑']:
        feats[k] = {c['id'] for c in cases if k in c['tongue']}
    for side, f in [('右', '滑'), ('右', '浮'), ('左', '弦'), ('左', '数'), ('右', '滞'), ('左', '滞')]:
        feats[f'{side}脉{f}'] = {c['id'] for c in cases if f in c['pulse'].get(side, [])}
    feats = {k: v for k, v in feats.items() if len(v) >= 8}
    lift_herbs = high[:20]
    lcells = []
    for k, ids in feats.items():
        for h in lift_herbs:
            nh_ = freq[h]
            both = sum(1 for c in cases if c['id'] in ids and h in c['herbs'])
            lift = (both / len(ids)) / (nh_ / N) if both else 0.0
            lcells.append(dict(feat=k, herb=h, n=both, nf=len(ids), lift=round(lift, 2)))
    R['feat_herb'] = dict(features=[dict(k=k, n=len(v)) for k, v in feats.items()], herbs=lift_herbs, cells=lcells)

    # ------------------------------------------------ 俞根初（《俞根初临证经验集要》）治咳方证
    ygc_p = C.load_ygc()
    ygc = []
    for e in edges:
        if e['corpus'] == 'ygc_jingyao' and e['type'] == 'formulaTreats' and YU_KEY.search(byid[e['object_id']]['name']):
            f_raw, t = byid[e['subject_id']]['name'], byid[e['object_id']]['name']
            f = YU_ALIAS.get(f_raw, f_raw)
            sent = (e['source_sentence'] or '').replace('\n', ' ')
            text = ygc_p[e['passage_id']]['text']
            i = text.find(f_raw)
            win = text[max(0, i - YU_WIN):i + len(f_raw) + YU_WIN] if i >= 0 else ''
            if (f, t) in YU_NOT_LUNG:
                rel, why = '非肺系（仅字面命中，不计）', YU_NOT_LUNG[(f, t)]
            elif YU_COUGH.search(t + sent):
                rel, why = '直接论治咳嗽', '主治或原文句含咳、嗽'
            elif YU_COUGH.search(win):
                rel, why = '直接论治咳嗽', f'段落中方名前后 {YU_WIN} 字内论及咳嗽或咯痰'
            else:
                rel, why = '肺系痰喘病证', '主治含肺、痰、喘'
            kind = '书中引录的现代临床文献' if YU_MODERN.search(text) else '俞氏原论及方论'
            ygc.append(dict(formula=f, formula_raw=f_raw, target=t, relevance=rel, why=why, kind=kind,
                            chapter=e['chapter_path'], pid=e['passage_id'], sentence=sent))
    rel_order = ['直接论治咳嗽', '肺系痰喘病证', '非肺系（仅字面命中，不计）']
    ygc.sort(key=lambda x: (rel_order.index(x['relevance']), x['kind'] != '俞氏原论及方论', x['formula'], x['pid']))
    lung = [x for x in ygc if x['relevance'] != rel_order[2]]
    props_ygc = [dict(subject=byid[e['subject_id']]['name'], rel=e['type'], obj=byid[e['object_id']]['name'], pid=e['passage_id'],
                      sentence=(e['source_sentence'] or '').replace('\n', ' '))
                 for e in edges if e['corpus'] == 'ygc_jingyao' and re.search('[咳嗽]', byid[e['subject_id']]['name'] + byid[e['object_id']]['name'])]
    he_formulas = collections.Counter(f for c in cases for f in c['formulas'])
    lung_f = sorted({x['formula'] for x in lung})
    R['yu'] = dict(formula_target=ygc, other=props_ygc, candidates=len(ygc),
                   rows=len(lung), rows_direct=sum(1 for x in lung if x['relevance'] == rel_order[0]),
                   formulas=lung_f, formulas_orig=sorted({x['formula'] for x in lung if x['kind'] == '俞氏原论及方论'}),
                   formulas_excluded=sorted({x['formula'] for x in ygc} - set(lung_f)),
                   used_by_he=sorted(f for f in lung_f if he_formulas.get(f)),
                   he_prin_top=collections.Counter(p for c in cases for p in c['prins']).most_common(15))
    write_csv(SUP / 'S6_yu_formula_indications.csv', ['方剂', '图谱写法', '主治（图谱宾语）', '与咳嗽的关系', '判读依据', '来源性质', '章节路径', '段落编号', '原文句'],
              [[x['formula'], x['formula_raw'], x['target'], x['relevance'], x['why'], x['kind'], x['chapter'], x['pid'], x['sentence']] for x in ygc])

    # ------------------------------------------------ 理法互证：俞根初论述 ↔ 何廉臣咳嗽医案
    def fr(h):
        return f'{h} {freq.get(h, 0)} 例（{pct(freq.get(h, 0), N)}%）'
    tsub = {t: [c for c in cases if c['type'] == t] for t in C.TYPE_ORDER}
    tcell = {(x['el'], x['type']): x['n'] for x in R['type_prin']['cells']}

    def th(t, h):
        n_ = sum(1 for c in tsub[t] if h in c['herbs'])
        return f'{h} {pct(n_, len(tsub[t])):.0f}%'
    ttab = {x['type']: x for x in R['type_table']}
    feat = {x['k']: x for x in R['features']}
    pr = {x['k']: x for x in R['pulse']['feats']}
    sc = R['pulse']['side_cases']
    spu = {x['k']: x for x in R['sputum']}
    d = R['dose']
    prin_n = dict(R['yu']['he_prin_top'])
    xiao = [c for c in cases if '小青龙汤' in c['formulas']]
    ban_xia = raw_of['半夏']
    pear = sum(1 for c in cases if {'梨', '梨皮'} & set(c['herbs']))
    co_gz = sum(1 for c in cases if {'瓜蒌子', '紫菀'} <= set(c['herbs']))
    lao = [c for c in cases if re.search(r'肺痨|成痨', passages.get(c['pid'], {}).get('text', ''))]
    warn = next((c for c in cases if '防变咳血肺痨' in passages.get(c['pid'], {}).get('text', '')), None)
    he_ev = {
        'dose': f'单味药剂量记录 {d["n"]:,} 条，中位数 {d["median"]:.1f} 钱（P25–P75：{d["q1"]:.1f}–{d["q3"]:.1f} 钱），'
                f'≤3 钱者占 {d["le3"]}%（图 4A）',
        'fresh': f'使用鲜药 {feat["使用鲜药"]["cases"]} 例（{feat["使用鲜药"]["pct"]}%），如{feat["使用鲜药"]["note"]}；'
                 f'先煎代水 {feat["先煎代水"]["cases"]} 例（{feat["先煎代水"]["pct"]}%）',
        'wind': f'{fr("牛蒡子")}；新加三拗汤所加诸药中，金橘（金橘脯）{freq.get("金橘", 0)} 例、甘草 {freq.get("甘草", 0)} 例、'
                f'桔梗 {freq.get("桔梗", 0)} 例、薄荷 {freq.get("薄荷", 0)} 例；麻黄仅 {freq.get("麻黄", 0)} 例',
        'phlegm': f'痰饮痰阻 {len(tsub["痰饮"])} 例：{th("痰饮", "苦杏仁")}、{th("痰饮", "半夏")}、{th("痰饮", "陈皮")}，'
                  f'化痰豁痰 {tcell[("化痰豁痰", "痰饮")]} 例、肃肺降气 {tcell[("肃肺降气", "痰饮")]} 例；'
                  f'半夏原书多作竹沥半夏（{ban_xia.get("竹沥半夏", 0)} 处，姜半夏 {ban_xia.get("姜半夏", 0)} 处）；'
                  f'明用小青龙汤仅 {len(xiao)} 例（{"、".join(c["title"] for c in xiao)}），干姜 {freq.get("干姜", 0)} 例、细辛 {freq.get("细辛", 0)} 例、'
                  f'五味子 {freq.get("五味子", 0)} 例',
        'pulse': f'右脉滑 {pr["滑"]["right"]}/{sc["右"]} 例（{pct(pr["滑"]["right"], sc["右"])}%）、浮 {pr["浮"]["right"]}/{sc["右"]} 例；'
                 f'左脉弦 {pr["弦"]["left"]}/{sc["左"]} 例（{pct(pr["弦"]["left"], sc["左"])}%）、数 {pr["数"]["left"]}/{sc["左"]} 例；'
                 f'痰稠粘 {spu["痰稠粘"]["n"]} 例（{spu["痰稠粘"]["pct"]}%）（图 8）',
        'liver': f'肝火犯肺 {len(tsub["肝火"])} 例（{ttab["肝火"]["pct"]}%），含清肝平肝要素者 {tcell[("清肝平肝", "肝火")]} 例；'
                 f'「清肝保肺」为出现最多的治法表述（{prin_n.get("清肝保肺", 0)} 例）；痰中带血 {spu["痰中带血"]["n"]} 例（{spu["痰中带血"]["pct"]}%）；'
                 f'血见愁 {freq.get("血见愁", 0)} 例（地锦草等之异名，基原待考）、梨（肉、皮）{pear} 例',
        'dry': f'{fr("瓜蒌子")}，居用药首位；{fr("紫菀")}、{fr("前胡")}；瓜蒌子与紫菀同用 {co_gz} 例',
        'yin': f'虚劳咳嗽 {len(tsub["虚劳"])} 例：{th("虚劳", "石斛")}、{th("虚劳", "甜杏仁")}、{th("虚劳", "柿霜")}；'
               f'含润燥养阴要素 {tcell[("润燥养阴", "虚劳")]} 例、补益扶正 {tcell[("补益扶正", "虚劳")]} 例；未见葳蕤（玉竹）',
        'transform': f'病机归类中虚劳咳嗽（劳嗽、肺痨）{len(tsub["虚劳"])} 例、痰饮痰阻 {len(tsub["痰饮"])} 例、痰热肺热 {len(tsub["肺热"])} 例；'
                     f'医案原文言及肺痨、成痨者 {len(lao)} 例' + (f'，如{warn["title"]}「防变咳血肺痨」' if warn else ''),
    }
    yu_he = []
    for key, theme, quotes in YU_HE:
        for pid, q_ in quotes:
            assert q_ in ygc_p[pid]['text'], (pid, q_)
        yu_he.append(dict(key=key, theme=theme, quotes=[dict(pid=p_, text=q_, chapter=ygc_p[p_]['section']) for p_, q_ in quotes],
                          he=he_ev[key]))
    R['yu_he'] = yu_he

    # ------------------------------------------------ 典型医案（证据链示例）
    def score(c):
        return (c['type'] == '肝火', bool(c['diag']), bool(c['pats']), len(c['prins']) > 0, 10 <= len(c['herbs']) <= 12,
                len(c['tongue']) > 0, len(c['pulse']) > 0, -abs(len(c['herbs']) - 11))
    ex = max(cases, key=score)
    ex_edges = [e for e in edges if e['subject_id'] == ex['id']]
    R['example'] = dict(uid=ex['uid'], title=ex['title'], type=ex['type'], pid=ex['pid'],
                        text=passages.get(ex['pid'], {}).get('text', ''),
                        edges=[dict(rel=e['type'], obj=byid[e['object_id']]['name'], pid=e['passage_id'],
                                    sentence=(e['source_sentence'] or '').replace('\n', ' '), verbatim=e.get('evidence_verbatim'),
                                    found=e.get('evidence_in_passage'), engine=e.get('engine'), agreement=e.get('agreement'),
                                    chapter=e.get('chapter_path'), layer=e.get('layer'), subject=e.get('subject_name'))
                               for e in ex_edges])

    # ------------------------------------------------ 敏感性分析：扩展纳入（兼见咳嗽症状者）
    Te = [C.herbs_of(r)[0] for r in ext]
    fe = collections.Counter(h for t in Te for h in t)
    top_main = [h for h, _ in ranked(freq)[:20]]
    top_ext = [h for h, _ in ranked(fe)[:20]]
    union = sorted(set(top_main) | set(top_ext))
    rho, pval = spearmanr([freq[h] / N for h in union], [fe[h] / len(Te) for h in union])
    R['sensitivity'] = dict(n_ext=len(Te), overlap20=len(set(top_main) & set(top_ext)), rho=round(float(rho), 3), p=float(pval),
                            rows=[dict(herb=h, main=pct(freq[h], N), ext=pct(fe[h], len(Te)),
                                       rank_main=top_main.index(h) + 1 if h in top_main else None,
                                       rank_ext=top_ext.index(h) + 1 if h in top_ext else None) for h in union])

    # ------------------------------------------------ 附表 S1、S2、S4
    s1 = collections.Counter()
    notes = {}
    for c in cases:
        for x in c['rows']:
            s1[(x['raw'], x['std'], x['patent'])] += 1
            notes[(x['raw'], x['std'], x['patent'])] = x['note']
    write_csv(SUP / 'S1_herb_name_normalization.csv', ['原书写法', '规范名', '类别', '出现次数', '说明'],
              [[raw, std, '成药' if pat else '单味药', n, notes[(raw, std, pat)] if notes[(raw, std, pat)] != '成药' else ''] for (raw, std, pat), n in
               sorted(s1.items(), key=lambda x: (x[0][2], x[0][1], -x[1]))])
    write_csv(SUP / 'S2_included_cases.csv', ['编号', '原书案名', '纳入依据', '诊断', '证候', '病机类别', '命中词', '诊次', '药味数', '单味药', '成药', '治法'],
              [[c['uid'], c['title'], '标题+诊断' if c['by_title'] and c['by_diag'] else ('标题' if c['by_title'] else '诊断'),
                '、'.join(c['diag']), '、'.join(c['pats']), C.TYPE_ZH[c['type']], c['type_hit'], c['n_visits'], len(c['herbs']),
                '、'.join(c['herbs']), '、'.join(c['patents']), '；'.join(c['prins'])] for c in sorted(cases, key=lambda c: c['uid'])])
    write_csv(SUP / 'S4_rules_type_and_principle.csv', ['规则类别', '名称', '关键词（正则）', '说明'],
              [['病机类别', z, rx, f'优先级 {i + 1}（先命中者为准）'] for i, (k, z, rx) in enumerate(C.TYPE_RULES)] +
              [['病机类别', C.TYPE_OTHER[1], '（未命中以上任何一类）', '']] +
              [['治法要素', k, rx, '一案可同时含多项'] for k, rx in C.PRIN_RULES])
    write_csv(SUP / 'S5_sensitivity_extended.csv', ['药物', '主分析频率/%（n=125）', '扩展纳入频率/%', '主分析排名', '扩展排名'],
              [[r['herb'], r['main'], r['ext'], r['rank_main'] or '', r['rank_ext'] or ''] for r in R['sensitivity']['rows']])

    R['cases'] = [{k: v for k, v in c.items() if k != 'rows'} for c in cases]
    (RES / 'results.json').write_text(json.dumps(R, ensure_ascii=False, indent=1, default=_json), encoding='utf-8')
    _report(R)


def _group(rows, key):
    g = collections.defaultdict(list)
    for x in rows:
        if x['dose'] is not None:
            g[key(x)].append(x['dose'])
    return g


def _silhouette(D, labels):
    labels = np.asarray(labels)
    s = []
    for i in range(len(labels)):
        same = labels == labels[i]
        same[i] = False
        if not same.any():
            s.append(0.0)
            continue
        a = D[i, same].mean()
        b = min(D[i, labels == l].mean() for l in set(labels) if l != labels[i])
        s.append((b - a) / max(a, b))
    return float(np.mean(s))


def _bh(cells):
    ps = sorted(range(len(cells)), key=lambda i: cells[i]['p'])
    m = len(cells)
    qv = [0.0] * m
    prev = 1.0
    for rank in range(m, 0, -1):
        i = ps[rank - 1]
        prev = min(prev, cells[i]['p'] * m / rank)
        qv[i] = prev
    for c, qq in zip(cells, qv):
        c['q'] = qq


def _json(o):
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(type(o))


def _report(R):
    s = R['summary']
    print(f"候选 {s['candidates']}（标题 {s['cand_title']}、诊断 {s['cand_diag']}、重合 {s['cand_both']}）→ 纳入 {s['included']}，排除 {len(s['excluded'])}")
    print(f"每案药味 {s['herbs_mean']}±{s['herbs_sd']}，中位 {s['herbs_median']}（{s['herbs_q1']}–{s['herbs_q3']}），{s['herbs_min']}–{s['herbs_max']}；"
          f"单味药 {s['distinct_herbs']} 种 / {s['herb_uses']} 药次；原书写法 {s['raw_spellings']} 种；成药 {s['patent_kinds']} 种、{s['patent_cases']} 案")
    print('诊次:', s['visits'], '| 高频药物（≥%d 案）%d 味' % (R['high_freq_min'], len(R['high_freq'])))
    print('功效:', [(c['cat'], c['uses'], c['pct']) for c in R['categories']])
    p = R['properties']
    print('性味覆盖 %.1f%%' % p['coverage_pct'], '| 四气', [(x['k'], x['pct']) for x in p['qi']], '| 五味', [(x['k'], x['pct']) for x in p['wei']])
    print('归经', [(x['k'], x['pct']) for x in p['gui']])
    d = R['dose']
    print(f"剂量：{d['n']} 条，中位 {d['median']} 钱（{d['q1']}–{d['q3']}），≤2 钱 {d['le2']}%，≤3 钱 {d['le3']}%，>5 钱 {d['gt5']}%")
    print('特色:', [(f['k'], f['cases'], f['pct']) for f in R['features']])
    print('规则 %d 条；频繁项集 L1 %d L2 %d L3 %d' % (len(R['rules']), R['itemsets']['L1'], R['itemsets']['L2'], R['itemsets']['L3']))
    for r in R['rules'][:8]:
        print('   ', '+'.join(r['ant']), '→', '+'.join(r['con']), r['support'], r['confidence'], r['lift'])
    nw = R['network']
    print('网络：节点 %d 边 %d 模块度 %.3f 社区 %s 孤立 %s' % (len(nw['nodes']), len(nw['edges']), nw['modularity'], nw['communities'], nw['isolated']))
    cl = R['cluster']
    print('聚类：cophenetic %.3f，k=%d，silhouette %s' % (cl['cophenetic'], cl['k'], cl['silhouette']))
    for c in cl['clusters']:
        print('   ', c)
    print('病机类别:', R['types']['n'], '| 主要类别', R['types']['main'])
    print('治法要素（案数）:', R['type_prin']['overall'], '| 有治法记录', R['type_prin']['cases_with_prin'])
    print('伴随症状:', [(x['k'], x['n']) for x in R['symptoms']])
    print('痰象:', [(x['k'], x['n']) for x in R['sputum']])
    print('舌象（%d 案）:' % R['tongue']['cases'], [(x['k'], x['n']) for x in R['tongue']['feats']])
    print('脉象（%d 案）:' % R['pulse']['cases'], R['pulse']['side_cases'], [(x['k'], x['right'], x['left'], x['both']) for x in R['pulse']['feats']])
    print('咳血/痰血案:', R['blood_cases'])
    y = R['yu']
    print(f"俞根初方证：初筛 {y['candidates']} 条 → 肺系咳喘 {y['rows']} 条（直接论治咳嗽 {y['rows_direct']}），"
          f"方剂 {len(y['formulas'])} 首（俞氏原论 {len(y['formulas_orig'])} 首：{'、'.join(y['formulas_orig'])}）；"
          f"排除 {'、'.join(y['formulas_excluded'])}；何氏医案同名使用 {y['used_by_he']}")
    for x in R['yu_he']:
        print('   理法互证', x['theme'], '|', x['he'])
    print('典型医案:', R['example']['uid'], R['example']['title'], R['example']['type'], len(R['example']['edges']), '条关系')
    se = R['sensitivity']
    print(f"敏感性：扩展 {se['n_ext']} 案，前20重合 {se['overlap20']}/20，Spearman ρ={se['rho']}（P={se['p']:.2g}）")


if __name__ == '__main__':
    main()
