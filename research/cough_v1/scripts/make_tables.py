"""绍派伤寒辨治咳嗽用药规律 · 论文表格（三线表 7 张）与图表题注。

  python3 scripts/analysis.py && python3 scripts/make_tables.py && node scripts/make_docx.js

输出：
  tables/T1–T7_*.csv      每表一份（UTF-8 BOM，Excel 可直接打开）
  tables/tables.md        Markdown 版，便于在 GitHub 上核对
  tables/tables.json      表格结构（供 make_docx.js 生成 Word 三线表）
  figures/legends.json    图题（中英文）与图注（供 make_docx.js）
  LEGENDS.md              图表题注汇总
  SUMMARY.md              主要结果摘要（供撰写结果部分参考）
  .build/fig300/*.png     Word 内嵌用 300 dpi 缩样（不入库）
表中数字全部取自 results/results.json，与图同源。单元格内 {sup:x} 为上标注释号。
"""
import csv, json, re, statistics, collections
from pathlib import Path
from PIL import Image

import common as C

OUT = C.OUT
R = json.loads((OUT / 'results/results.json').read_text(encoding='utf-8'))
S = R['summary']
N = S['included']
TAB = OUT / 'tables'
TAB.mkdir(exist_ok=True)
HERB = {h['herb']: h for h in R['herbs']}

# 聚类组合的配伍意义（参考释义，待专家核对）；以组成为键，组成变化时须同步修订，否则脚本报错
CLUSTER_NOTES = {frozenset(k): v for k, v in {
    ('石斛', '金橘'): '理气化痰，养胃生津',
    ('桑白皮', '白薇'): '泻肺平喘，清退虚热',
    ('旋覆花', '牛蒡子', '紫苏子'): '疏风利咽，降气化痰',
    ('桑叶', '瓜蒌子', '甜杏仁', '白前', '竹茹', '紫菀', '胖大海', '苦杏仁', '款冬花', '蛤壳', '陈皮', '马兜铃'):
        '清肺化痰，肃肺止咳（核心组合）',
    ('前胡', '半夏', '甘草', '茯苓', '薏苡仁', '远志'): '燥湿化痰，健脾渗湿（含二陈汤之半夏、茯苓、甘草）',
    ('瓜蒌皮', '连翘'): '清热散结，宽胸化痰',
    ('桑枝', '淡竹叶', '滑石', '菊花'): '清利湿热，疏风通络',
    ('血见愁', '郁金'): '凉血宁络，行气解郁',
}.items()}


def pct(a, b, d=1):
    return round(100.0 * a / b, d) if b else 0.0


def fnum(x):
    """剂量数字：整数不带小数，其余保留至多两位。"""
    return f'{x:g}' if abs(x - round(x, 2)) < 1e-9 else f'{x:.2f}'


def plain(s):
    """单元格可为字符串或行列表（Word 中每行一段，避免药名与星号被折开）；CSV、Markdown 中连排。"""
    if isinstance(s, list):
        s = ''.join(s)
    return re.sub(r'\{sup:([^}]+)\}', lambda m: f'[{m.group(1)}]', s) if isinstance(s, str) else s


def md(s):
    if isinstance(s, list):
        s = ''.join(s)
    return re.sub(r'\{sup:([^}]+)\}', r'<sup>\1</sup>', s).replace('|', '\\|')


def lines_of(items, per=2, sep='、'):
    """每行 per 项，行末保留顿号。"""
    rows = [sep.join(items[i:i + per]) for i in range(0, len(items), per)]
    return [r + sep for r in rows[:-1]] + rows[-1:]


TABLES = []


def table(tid, key, title, title_en, columns, rows, notes):
    TABLES.append(dict(id=tid, key=key, title=title, title_en=title_en,
                       columns=[dict(h=h, align=a, mm=w) for h, a, w in columns], rows=rows, notes=notes))
    assert abs(sum(w for _, _, w in columns) - 170) < 0.01, (tid, sum(w for _, _, w in columns))


def grp(t):
    return {'group': t}


# ============================================================ 表1 纳入医案的基本特征
v = {int(k): n for k, n in S['visits'].items()}
unparsed = S['dose_rows'] - S['dose_weight'] - S['dose_count'] - len(S['dose_suspect'])
rows = [
    grp('数据来源'),
    ['知识图谱', f'V1 两书版：{S["v1_nodes"]:,} 个节点，{S["v1_edges"]:,} 条关系（《俞根初临证经验集要》《何廉臣医案》）'],
    ['医案总数', f'《何廉臣医案》{S["hlc_cases"]} 案'],
    grp('医案筛选'),
    ['候选医案', f'{S["candidates"]} 例：案名含「咳」或「嗽」{S["cand_title"]} 例，诊断含「咳」或「嗽」{S["cand_diag"]} 例，两者兼有 {S["cand_both"]} 例'],
    ['排除', f'{len(S["excluded"])} 例：图谱中无用药关系（原文有方，抽取缺失；'
             + '、'.join(x['title'] for x in S['excluded']) + '）'],
    ['纳入医案', f'{N} 例：案名与诊断均命中 {S["inc_both"]} 例，仅案名 {S["inc_title_only"]} 例，仅诊断 {S["inc_diag_only"]} 例'],
    ['敏感性分析样本', f'{S["extended"]} 例（另纳入诊断或症状兼见咳嗽者）'],
    grp('诊次与处方'),
    ['诊次', f'单诊 {v.get(1, 0)} 例（{pct(v.get(1, 0), N)}%），复诊 {S["multi_visit"]} 例（{pct(S["multi_visit"], N)}%）：'
             f'二诊 {v.get(2, 0)} 例，三诊 {v.get(3, 0)} 例，四诊及以上 {sum(n for k, n in v.items() if k >= 4)} 例'],
    ['每案用药味数{sup:a}', f'{S["herbs_mean"]:.2f} ± {S["herbs_sd"]:.2f} 味；中位数 {S["herbs_median"]:g} 味'
                        f'（P25–P75：{S["herbs_q1"]:g}–{S["herbs_q3"]:g} 味）；范围 {S["herbs_min"]}–{S["herbs_max"]} 味'],
    ['单味药', f'原书写法 {S["raw_spellings"]} 种，规范为 {S["distinct_herbs"]} 味；累计 {S["herb_uses"]:,} 药次{{sup:a}}'],
    ['丸散成药', f'{S["patent_kinds"]} 种，见于 {S["patent_cases"]} 例（{pct(S["patent_cases"], N)}%），共 {S["patent_uses"]} 次；单列统计'],
    ['剂量记录', f'单味药用药记录 {S["dose_rows"]:,} 条：可折算为钱者 {S["dose_weight"]:,} 条（{pct(S["dose_weight"], S["dose_rows"])}%），'
             f'以枚、片等计数者 {S["dose_count"]} 条，存疑剔除 {len(S["dose_suspect"])} 条{{sup:b}}，未能解析 {unparsed} 条'],
    grp('四诊与治法记录'),
    ['舌诊', f'{R["tongue"]["cases"]} 例（{pct(R["tongue"]["cases"], N)}%）'],
    ['脉诊', f'{R["pulse"]["cases"]} 例（{pct(R["pulse"]["cases"], N)}%）；分记右脉 {R["pulse"]["side_cases"]["右"]} 例、'
           f'左脉 {R["pulse"]["side_cases"]["左"]} 例'],
    ['治法', f'{R["type_prin"]["cases_with_prin"]} 例（{pct(R["type_prin"]["cases_with_prin"], N)}%）'],
    grp('分析口径'),
    ['高频药物', f'使用频率 ≥ 10%（≥ {R["high_freq_min"]} 例），共 {len(R["high_freq"])} 味'],
    ['统计单位', '医案（复诊医案合并各诊用药，同一药物只计一次）'],
]
table('1', 'T1_case_characteristics', '纳入医案的基本特征', 'Characteristics of the included cough cases',
      [('项目', 'l', 34), ('结果', 'l', 136)], rows,
      ['注：a 以医案为单位，复诊医案合并各诊用药后计数，丸散成药不计入；药次为各案规范药名数之和。',
       f'b {S["dose_suspect"][0]["note"]}。' if S['dose_suspect'] else 'b 无。',
       '数据来源：越医·绍派伤寒数智传承智能体 V1 两书版知识图谱（与站点 v1.html 同一子图）。'])

# ============================================================ 表2 高频药物
rows = []
for h in R['high_freq']:
    x = HERB[h]
    raws = [re.sub(r'（\d+）$', '', r) for r in x['raw'].split('、')][:2]
    name = h + ('{sup:a}' if h == '马兜铃' else '') + ('{sup:b}' if h == '血见愁' else '') + \
        ('{sup:c}' if x['note'].startswith('教材未载') or '附药' in x['note'] else '')
    rows.append([str(x['rank']), name, '、'.join(raws), str(x['n']), f'{x["pct"]:.1f}', x['cat'], x['sub'] or '—',
                 x['qi'] or '—', x['wei'] or '—', x['gui'] or '—'])
table('2', 'T2_high_frequency_herbs', f'高频药物（使用频率 ≥ 10%）的使用频次与药性（n = {N}）',
      f'Frequency and properties of high-frequency herbs (used in ≥ 10% of cases; n = {N})',
      [('序号', 'c', 8), ('药物', 'l', 14), ('原书主要写法', 'l', 27), ('频次/例', 'c', 12), ('频率/%', 'c', 12),
       ('功效分类', 'l', 24), ('亚类', 'l', 18), ('四气', 'c', 8), ('五味', 'c', 18), ('归经', 'l', 29)], rows,
      ['注：药名依《中华人民共和国药典》（2020 年版）规范，原书写法与规范名对照见附表 S1；四气、五味、归经依《中华人民共和国药典》（2020 年版），'
       '药典未收载者依《中药学》（“十四五”规划教材）或《中华本草》，逐药依据见附表 S3；功效分类依《中药学》教材。',
       'a 马兜铃含马兜铃酸，有肾毒性，2020 年版药典已不再收载，性味归经据 2015 年版药典；本表仅作文献用药规律描述，不作临床用药推荐。',
       f'b 血见愁为地锦草、铁苋菜、山藿香等多种药物的异名，基原待考，未计入四气五味归经统计，功效暂按凉血止血归类。',
       'c 金橘（原书多作金橘脯）教材未载，按功效归类；甜杏仁为苦杏仁附药。'])

# ============================================================ 表3 剂量
rows = []
freq_rank = {h: i for i, h in enumerate(R['high_freq'])}
for k, d in enumerate(sorted(R['dose']['by_herb'], key=lambda d: freq_rank[d['herb']]), 1):
    mc = collections.Counter(d['values']).most_common()
    top = max(c for _, c in mc)
    modes = sorted(val for val, c in mc if c == top)
    rows.append([str(k), d['herb'], str(d['n']), fnum(d['median']), f'{fnum(d["q1"])}–{fnum(d["q3"])}',
                 f'{fnum(d["min"])}–{fnum(d["max"])}', '、'.join(fnum(m) for m in modes) + f'（{pct(top, d["n"])}%）'])
dd = R['dose']
table('3', 'T3_dose', '高频药物单次处方剂量', 'Single-prescription doses of high-frequency herbs',
      [('序号', 'c', 10), ('药物', 'l', 20), ('剂量记录/条', 'c', 22), ('中位数/钱', 'c', 22), ('P25–P75/钱', 'c', 26),
       ('范围/钱', 'c', 24), ('众数/钱（占比）', 'c', 46)], rows,
      [f'注：剂量以原书单位折算为钱（1 两 = 10 钱，1 分 = 0.1 钱），记录单位为处方（复诊各诊分别计），仅列剂量记录 ≥ 5 条的高频药物；'
       f'胖大海、金橘以枚计，未列入。全部 {dd["n"]:,} 条剂量记录的中位数为 {dd["median"]:g} 钱（P25–P75：{dd["q1"]:g}–{dd["q3"]:g} 钱），'
       f'≤ 3 钱者占 {dd["le3"]}%，> 5 钱者占 {dd["gt5"]}%。',
       '按现代临床习用折算 1 钱 ≈ 3 g；若按清代库平制，1 钱 ≈ 3.73 g。大剂量记录均经核对原文：桑枝 10–20 钱者均与冬瓜皮（子）同为'
       '「先用……煎汤代水」之品，竹茹最大值 50 钱为「鲜刮竹茹五两」。'])

# ============================================================ 表4 关联规则
rows = []
for k, r in enumerate(R['rules'], 1):
    rows.append([str(k), ' + '.join(r['ant']), ' + '.join(r['con']), str(r['n']), f'{r["support"]:.1f}',
                 f'{r["confidence"]:.1f}', f'{r["lift"]:.2f}'])
table('4', 'T4_association_rules', '高频药物关联规则（最小支持度 20%，最小置信度 70%）',
      'Association rules among herbs (minimum support 20%, minimum confidence 70%)',
      [('序号', 'c', 10), ('前项', 'l', 50), ('后项', 'l', 26), ('案数', 'c', 16), ('支持度/%', 'c', 24), ('置信度/%', 'c', 24),
       ('提升度', 'c', 20)], rows,
      [f'注：Apriori 算法，事务为医案（n = {N}），项为规范药名；频繁 1 项集 {R["itemsets"]["L1"]} 个、2 项集 {R["itemsets"]["L2"]} 个、'
       f'3 项集 {R["itemsets"]["L3"]} 个；仅列提升度 > 1 的规则，按置信度降序排列。',
       '支持度 = 前项与后项同现的医案数 / 总医案数；置信度 = 同现医案数 / 含前项的医案数；提升度 = 置信度 / 后项的支持度。'])

# ============================================================ 表5 聚类组合
cl = R['cluster']
lab = cl['labels']
sim = cl['jaccard_sim']
rows = []
for i, members in enumerate(cl['clusters']):
    note = CLUSTER_NOTES.get(frozenset(members))
    assert note, f'聚类组成已变化，请更新 CLUSTER_NOTES：{members}'
    idx = [lab.index(h) for h in members]
    pairs = [(a, b) for a in idx for b in idx if a < b]
    msim = statistics.mean(sim[a][b] for a, b in pairs) if pairs else float('nan')
    cats = collections.Counter(HERB[h]['cat'] for h in members)
    catx = '、'.join(f'{c} {n}' for c, n in sorted(cats.items(), key=lambda x: (-x[1], x[0])))
    rows.append([f'C{i + 1}', '、'.join(members), str(len(members)), f'{msim:.3f}', catx, note])
table('5', 'T5_herb_clusters', '高频药物层次聚类所得药物组合', 'Herb groups identified by hierarchical clustering',
      [('组合', 'c', 11), ('药物组成', 'l', 52), ('味数', 'c', 10), ('组内平均相似度', 'c', 20), ('功效类别构成', 'l', 42),
       ('配伍意义（参考）', 'l', 35)], rows,
      [f'注：{len(lab)} 味高频药物以 Jaccard 距离、类平均法（UPGMA）聚类，共表型相关系数 {cl["cophenetic"]:.3f}；'
       f'分组数按平均轮廓系数确定为 k = {cl["k"]}（k = 3–10 中最高，{cl["silhouette"][str(cl["k"])]:.3f}）。组合编号与图 5、图 6 一致，组内药物按使用频次排序。',
       '组内平均相似度为组内两两 Jaccard 相似系数的均值；配伍意义为依据药物功效的参考释义，待专家核对。'])

# ============================================================ 表6 病机类别
T = R['types']
sig = collections.defaultdict(list)
for c in sorted(R['type_herb']['cells'], key=lambda c: c['p']):
    if c['p'] < 0.05:
        sig[c['type']].append(c['herb'] + ('**' if c['q'] < 0.05 else '*'))
rows = []
for x in R['type_table']:
    t = x['type']
    rows.append([x['zh'], f'{x["n"]}（{x["pct"]:.1f}）', x['herbs'],
                 lines_of(sig[t]) if t in T['main'] and sig[t] else '—', x['prins']])
table('6', 'T6_pathogenesis', '不同病机类别咳嗽医案的核心用药与治法', 'Core herbs and treatment principles by pathogenesis category',
      [('病机类别', 'l', 28), ('例数（%）', 'c', 20), ('核心药物（该类医案使用率）', 'l', 56), ('特征用药', 'l', 32),
       ('主要治法要素（例）', 'l', 34)], rows,
      ['注：病机类别按医案案名、诊断与证候中的关键词归类，自上而下先命中者为准，规则见附表 S4；治法要素由医案治法表述按关键词提取，一案可含多项。',
       f'核心药物为该类医案使用率前 8 位。特征用药仅比较 n ≥ {10} 的 {len(T["main"])} 类，按 P 值升序列出：单侧 Fisher 精确检验比较该类与其余医案的使用率，'
       '* P < 0.05，** 经 Benjamini–Hochberg 校正 q < 0.05，各药在该类中的使用率见图 7C；「—」示例数少，未检验。'])

# ============================================================ 表7 理法互证
rows = []
for x in R['yu_he']:
    quotes = '；'.join(f'「{q["text"]}」（{q["pid"]}）' for q in x['quotes'])
    rows.append([x['theme'], quotes, x['he']])
y = R['yu']
table('7', 'T7_yu_he_correspondence', '俞根初治咳理法与何廉臣咳嗽医案用药的对应（理法互证）',
      'Correspondence between Yu Genchu’s principles for cough and the medication patterns in He Lianchen’s cough cases',
      [('理法要点', 'l', 24), ('俞根初论述（节录）', 'l', 70), (f'何廉臣咳嗽医案中的对应（n = {N}）', 'l', 76)], rows,
      ['注：节录文字均出自《俞根初临证经验集要》，运行时逐字核对为语料段落原文；括号内为段落编号，可在图谱中回溯出处。'
       '右栏数字取自本研究统计（表 1–表 6、图 4、图 8）。两者为描述性对照，不作因果推断。',
       f'图谱中该书 formulaTreats 关系主治含咳、嗽、痰、喘、肺者 {y["candidates"]} 条，逐条判读后属肺系咳喘者 {y["rows"]} 条'
       f'（直接论治咳嗽 {y["rows_direct"]} 条），涉及方剂 {len(y["formulas"])} 首，其中出自俞氏原论及方论者 {len(y["formulas_orig"])} 首；'
       f'逐条判读结果与来源性质（原论或书中引录的现代临床文献）见附表 S6。'])

# ============================================================ 输出：CSV、JSON、Markdown
for t in TABLES:
    with open(TAB / f'{t["key"]}.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow([f'表{t["id"]} {t["title"]}'])
        w.writerow([plain(c['h']) for c in t['columns']])
        for r in t['rows']:
            w.writerow([r['group']] if isinstance(r, dict) else [plain(c) for c in r])
        for n in t['notes']:
            w.writerow([plain(n)])
(TAB / 'tables.json').write_text(json.dumps(TABLES, ensure_ascii=False, indent=1), encoding='utf-8')

md_lines = ['# 绍派伤寒辨治咳嗽用药规律 · 论文表格', '',
            '> 由 `scripts/make_tables.py` 自 `results/results.json` 生成，请勿手改。Word 三线表见 `tables/cough_v1_tables.docx`。', '']
for t in TABLES:
    md_lines += [f'## 表{t["id"]} {t["title"]}', '', f'*Table {t["id"]} {t["title_en"]}*', '']
    md_lines.append('| ' + ' | '.join(md(c['h']) for c in t['columns']) + ' |')
    md_lines.append('| ' + ' | '.join({'l': ':--', 'c': ':-:', 'r': '--:'}[c['align']] for c in t['columns']) + ' |')
    for r in t['rows']:
        if isinstance(r, dict):
            md_lines.append(f'| **{md(r["group"])}** |' + ' |' * (len(t['columns']) - 1))
        else:
            md_lines.append('| ' + ' | '.join(md(c) for c in r) + ' |')
    md_lines.append('')
    md_lines += [md(n) + '  ' for n in t['notes']]
    md_lines.append('')
(TAB / 'tables.md').write_text('\n'.join(md_lines), encoding='utf-8')

# ============================================================ 图题与图注
P = R['properties']
NW = R['network']
FIGS = [
    ('fig01_research_framework', '基于 V1 两书版知识图谱的绍派伤寒咳嗽用药规律研究技术路线',
     'Research framework for mining the cough medication patterns of the Shaopai Shanghan school from the V1 two-book knowledge graph',
     f'左列为医案筛选与规范化流程，右列为《俞根初临证经验集要》中的肺系咳喘方证（判读规则与逐条结果见附表 S6）；'
     f'①–⑥为分析模块，结果分别见图 2–图 9 与表 2–表 6，理法互证见表 7。'),
    ('fig02_herb_frequency_efficacy', f'{N} 例咳嗽医案高频药物的使用频次与功效分类',
     f'Frequency of the most-used herbs and distribution of efficacy categories in {N} cough cases',
     f'A. 使用频次前 30 位药物，柱长为使用频率，柱端数字为医案数，蓝色为化痰止咳平喘药；'
     f'B. 各功效类别所占药次比例（共 {S["herb_uses"]:,} 药次），功效分类依《中药学》教材，未归类者为基原或功效待考药物。'),
    ('fig03_nature_flavor_meridian', '咳嗽医案用药的四气、五味与归经分布',
     'Four natures, five flavours and meridian tropism of the herbs used in the cough cases',
     f'以药次计，共 {P["covered_uses"]:,} 药次（占单味药药次的 {P["coverage_pct"]}%，性味待考者未计）；A. 四气（微寒、大寒并入寒，微温并入温）；'
     f'B. 五味；C. 归经。一药多味、多经者分别计入，故五味、归经合计超过 100%。'),
    ('fig04_dose_and_features', '高频药物单次处方剂量分布与用药特色',
     'Single-prescription doses of high-frequency herbs and characteristic medication practices',
     f'A. 每点为一条剂量记录（钱，以 2 为底的对数坐标），灰色粗线为四分位间距，黑色竖线为中位数，竖直参考线为 3 钱；'
     f'B. 五项用药特色的医案占比。1 钱 ≈ 3 g。逐药统计见表 3。'),
    ('fig05_cooccurrence_network', '高频药物共现网络',
     'Co-occurrence network of high-frequency herbs',
     f'{len(NW["nodes"])} 味高频药物按层次聚类树叶序环形排列，仅显示共现 ≥ {NW["min_co"]} 案的药对（{len(NW["edges"])} 条）；'
     f'节点大小示使用频次，连线粗细示共现医案数；Louvain 社区划分模块度仅 {NW["modularity"]:.3f}，故以层次聚类分组（C1–C8，见表 5）着色。'),
    ('fig06_hierarchical_clustering', '高频药物层次聚类',
     'Hierarchical clustering of high-frequency herbs',
     f'A. 聚类树状图（Jaccard 距离，类平均法）；B. 两两 Jaccard 相似系数热图，按树状图叶序排列，方框示按平均轮廓系数确定的 {cl["k"]} 个药物组合；'
     f'共表型相关系数 {cl["cophenetic"]:.3f}。'),
    ('fig07_pathogenesis_principle_herb', '不同病机类别咳嗽医案的治法与用药',
     'Treatment principles and herbs across pathogenesis categories of the cough cases',
     f'A. 按病机关键词归类的医案数（规则见附表 S4）；B. 各类医案中含该治法要素的比例；C. 各类医案中药物使用率。'
     f'* 单侧 Fisher 精确检验 P < 0.05；** 经 Benjamini–Hochberg 校正 q < 0.05；仅比较 n ≥ 10 的 {len(T["main"])} 类。'),
    ('fig08_four_diagnostics', '咳嗽医案的伴随症状、痰象、舌象与脉象',
     'Accompanying symptoms, sputum, tongue and pulse features of the cough cases',
     f'A. 伴随症状（前 12 项）；B. 痰象；C. 舌象（有舌诊记录 {R["tongue"]["cases"]} 例）；'
     f'D. 左、右脉象，分别以该侧有记录的医案为分母（右 {R["pulse"]["side_cases"]["右"]} 例，左 {R["pulse"]["side_cases"]["左"]} 例）。'),
    ('fig09_feature_herb_lift', '四诊特征与高频药物的关联（提升度）',
     'Associations between diagnostic features and high-frequency herbs (lift)',
     '提升度 = P（用药 | 具该特征）/ P（用药），色阶取对数，红示正关联、蓝示负关联；共现 < 3 案者留白；'
     '格内数字为提升度 ≥ 1.5 且共现 ≥ 5 案者；药物为使用频率前 20 位。'),
    ('fig10_evidence_chain_example', f'典型医案的证据链：从原文到图谱关系与分析要素（{R["example"]["title"]}）',
     'Evidence chain of a representative case: from source text to graph relations and analytical elements',
     f'① 原文段落（{R["example"]["pid"]}）；② 图谱中该案的 {len(R["example"]["edges"])} 条关系，均保留原文句、段落编号与段内核验结果；'
     f'③ 规范化后的分析要素。'),
]
legends = [dict(file=f, title=t, title_en=te, note=n) for f, t, te, n in FIGS]
(OUT / 'figures/legends.json').write_text(json.dumps(legends, ensure_ascii=False, indent=1), encoding='utf-8')

L = ['# 图表题注', '', '> 由 `scripts/make_tables.py` 生成。图题置于图下、表题置于表上；中英文题名可按目标期刊取舍。', '', '## 图', '']
for k, g in enumerate(legends, 1):
    L += [f'**图 {k}　{g["title"]}**  ', f'*Fig. {k}　{g["title_en"]}*  ', f'注：{g["note"]}  ',
          f'文件：`figures/{g["file"]}.pdf`（矢量）、`.png`/`.tif`（600 dpi）', '']
L += ['## 表', '']
for t in TABLES:
    L += [f'**表 {t["id"]}　{t["title"]}**  ', f'*Table {t["id"]}　{t["title_en"]}*  ', f'文件：`tables/{t["key"]}.csv`', '']
L += ['## 附表（supplementary/）', '',
      '| 编号 | 内容 |', '| --- | --- |',
      '| S1 | 原书药名写法与规范药名对照 |', '| S2 | 纳入医案清单（编号、原书案名、纳入依据、病机类别、用药、治法） |',
      '| S3 | 药物四气五味归经与功效分类及依据 |', '| S4 | 病机类别与治法要素的关键词规则 |',
      '| S5 | 敏感性分析：扩展纳入与主分析的药物频率对照 |', '| S6 | 《俞根初临证经验集要》方证逐条判读（与咳嗽的关系、来源性质） |', '']
(OUT / 'LEGENDS.md').write_text('\n'.join(L), encoding='utf-8')

# ============================================================ 主要结果摘要（供撰写结果部分参考）
TOP = R['herbs']
qi = {x['k']: x for x in P['qi']}
cold = qi['寒']['uses'] + qi['凉']['uses']
wei = sorted(P['wei'], key=lambda x: -x['pct'])
gui = sorted(P['gui'], key=lambda x: -x['pct'])
cats = [c for c in R['categories'] if c['cat'] != '未归类']
feats = sorted(R['features'], key=lambda x: -x['pct'])
pair = R['itemsets']['pairs'][0]
rule = R['rules'][0]
core = max(cl['clusters'], key=len)
bh = collections.defaultdict(list)
for c in R['type_herb']['cells']:
    if c['q'] < 0.05:
        bh[c['type']].append(c['herb'])
tzh = {x['type']: x['zh'].split('（')[0] for x in R['type_table']}
tn = {x['type']: x for x in R['type_table']}
pl = {x['k']: x for x in R['pulse']['feats']}
sc = R['pulse']['side_cases']
tg = {x['k']: x for x in R['tongue']['feats']}
blood = next(x for x in R['sputum'] if x['k'] == '痰中带血')
se = R['sensitivity']
heavy = dict(dd['heavy'])
order_t = sorted([t for t in T['order'] if t != '未明'], key=lambda t: -T['n'][t])
SUM = [
    '# 主要结果摘要', '',
    '> 由 `scripts/make_tables.py` 自 `results/results.json` 生成，供撰写「结果」部分参考；均为描述性统计，解释须结合专家判读。', '',
    f'1. **样本**：候选医案 {S["candidates"]} 例，纳入 {N} 例（排除 {len(S["excluded"])} 例）；单诊 {v.get(1, 0)} 例、复诊 {S["multi_visit"]} 例；'
    f'共用单味药 {S["distinct_herbs"]} 味、{S["herb_uses"]:,} 药次，每案 {S["herbs_mean"]:.2f} ± {S["herbs_sd"]:.2f} 味（表 1）。',
    f'2. **高频药物**：使用频率 ≥ 10% 者 {len(R["high_freq"])} 味，前 5 位为' +
    '、'.join(f'{h["herb"]}（{h["pct"]}%）' for h in TOP[:5]) + '（表 2，图 2A）。',
    f'3. **功效分类**：{cats[0]["cat"]}占 {cats[0]["pct"]}% 药次（{cats[0]["kinds"]} 味），其次为' +
    '、'.join(f'{c["cat"]} {c["pct"]}%' for c in cats[1:5]) + '（图 2B）。',
    f'4. **药性**：四气以寒（含微寒、大寒）为主，占 {qi["寒"]["pct"]}%，寒凉合计 {pct(cold, P["covered_uses"])}%，温 {qi["温"]["pct"]}%；'
    f'五味以' + '、'.join(f'{w["k"]}（{w["pct"]}%）' for w in wei[:3]) + '居前；归经以' +
    f'{gui[0]["k"]}（{gui[0]["pct"]}%）为主，次为' + '、'.join(f'{g["k"]}（{g["pct"]}%）' for g in gui[1:4]) + '（图 3）。',
    f'5. **剂量**：{dd["n"]:,} 条剂量记录中位数 {dd["median"]:.1f} 钱（P25–P75：{dd["q1"]:.1f}–{dd["q3"]:.1f} 钱），≤ 3 钱占 {dd["le3"]}%；'
    f'> 5 钱者 {dd["heavy_n"]} 条（{dd["gt5"]}%），以蛤壳（{heavy.get("蛤壳", 0)} 条）、石决明（{heavy.get("石决明", 0)} 条）等介石类及煎汤代水之品为主（表 3，图 4A）。',
    '6. **用药特色**（医案占比）：' + '、'.join(f'{f["k"]} {f["pct"]}%' for f in feats) + '（图 4B）。',
    f'7. **配伍**：最常见药对为{"—".join(pair["items"])}（{pair["n"]} 例，{pair["support"]}%）；关联规则 {len(R["rules"])} 条，'
    f'置信度最高者为{" + ".join(rule["ant"])} → {" + ".join(rule["con"])}（{rule["confidence"]}%，提升度 {rule["lift"]:.2f}）（表 4）。',
    f'8. **药物组合**：层次聚类得 {cl["k"]} 组，最大组合 C{cl["clusters"].index(core) + 1}（{"、".join(core)}）以清肺化痰、肃肺止咳为主（表 5，图 5–图 6）。',
    '9. **病机与用药**：' + '，'.join(f'{tzh[t]} {T["n"][t]} 例（{tn[t]["pct"]}%）' for t in order_t) +
    '；经 Benjamini–Hochberg 校正后仍显著的特征用药为' +
    '，'.join(f'{tzh[t]}—{"、".join(bh[t])}' for t in T['main'] if bh[t]) + '（表 6，图 7）。',
    f'10. **四诊**：苔腻（{tg["苔腻"]["pct"]}%）、舌红（{tg["舌红"]["pct"]}%）多见；右脉以滑（{pct(pl["滑"]["right"], sc["右"])}%）、'
    f'浮（{pct(pl["浮"]["right"], sc["右"])}%）为主，左脉以弦（{pct(pl["弦"]["left"], sc["左"])}%）、数（{pct(pl["数"]["left"], sc["左"])}%）为主，'
    f'呈「右滑左弦」格局；痰中带血 {blood["n"]} 例（{blood["pct"]}%）（图 8，图 9）。',
    f'11. **理法互证**：俞根初「药量多在三钱之内」与何氏医案 ≤ 3 钱占 {dd["le3"]}% 相合；俞氏论夹痰火咳嗽「右寸浮滑，左手弦缓」与何氏医案'
    f'「右滑左弦」相应；新加三拗汤「减轻麻黄」，而 {N} 例何氏咳嗽医案中麻黄仅见 {HERB["麻黄"]["n"] if "麻黄" in HERB else 0} 例（表 7）。',
    f'12. **稳健性**：扩展纳入 {se["n_ext"]} 例后，前 20 位药物重合 {se["overlap20"]} 味，频率 Spearman ρ = {se["rho"]}（P < 0.001）（附表 S5）。',
    '',
]
assert se['p'] < 0.001
(OUT / 'SUMMARY.md').write_text('\n'.join(SUM), encoding='utf-8')

# ============================================================ Word 内嵌用 300 dpi 缩样
b = OUT / '.build/fig300'
b.mkdir(parents=True, exist_ok=True)
for g in legends:
    im = Image.open(OUT / f'figures/{g["file"]}.png')
    w, h = im.size
    im.resize((w // 2, h // 2), Image.LANCZOS).save(b / f'{g["file"]}.png', dpi=(300, 300), optimize=True)

for t in TABLES:
    print(f'表{t["id"]} {t["title"]}：{len([r for r in t["rows"] if not isinstance(r, dict)])} 行')
print('图题', len(legends), '幅')
