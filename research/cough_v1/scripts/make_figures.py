"""绍派伤寒辨治咳嗽用药规律 · 论文插图（10 幅）。

  python3 scripts/analysis.py && python3 scripts/make_figures.py [fig01 fig05 ...]

输出 figures/figNN_*.{pdf,png,tif}：PDF 为矢量（文字可编辑，TrueType 嵌入），PNG/TIFF 为 600 dpi。
"""
import json, math, collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, Rectangle, PathPatch, Arc
from matplotlib.path import Path as MPath
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import dendrogram

import style as S
import common as C

S.setup()
OUT = C.OUT / 'figures'
R = json.loads((C.OUT / 'results/results.json').read_text(encoding='utf-8'))
N = R['summary']['included']
FREQ = {h['herb']: h['n'] for h in R['herbs']}
KEY_CAT = '化痰止咳平喘药'

# 聚类组配色：三大组着色（前三色两两通过 CVD 校验），其余小组灰色，并以 C1–C8 文字标号作第二编码
CLUSTERS = R['cluster']['clusters']
CL_OF = {h: i for i, c in enumerate(CLUSTERS) for h in c}
BIG = sorted(range(len(CLUSTERS)), key=lambda i: -len(CLUSTERS[i]))[:3]
CL_COLOR = {i: S.SERIES[BIG.index(i)] if i in BIG else S.DEEMPH for i in range(len(CLUSTERS))}
TYPE_SHORT = {'专病': '专病', '虚劳': '虚劳', '肝火': '肝火', '湿热': '湿热', '风邪': '风邪', '肺热': '肺热', '痰饮': '痰饮', '未明': '未明'}


def cl_label(i):
    return f'C{i + 1}'


def vlabel(s):
    """中文竖排标签：字头朝上，一字一行。"""
    return '\n'.join(s)


def wrap_tokens(tokens, width, sep='、'):
    """按词整体折行（不在药名中间断开）；width 以字数计。"""
    lines, cur = [], ''
    for t in tokens:
        cand = t if not cur else cur + sep + t
        if len(cand) > width and cur:
            lines.append(cur + sep)
            cur = t
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def blue_cmap():
    return LinearSegmentedColormap.from_list('blue', S.BLUE_RAMP)


def hgrid(ax, axis='x'):
    ax.grid(axis=axis, color=S.GRID, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)


def tip(ax, x, y, s, dx=0.6, **kw):
    ax.text(x + dx, y, s, va='center', ha='left', fontsize=6.5, color=S.INK2, **kw)


def clean_left(ax):
    ax.tick_params(axis='y', length=0)
    ax.spines['left'].set_visible(False)


def rbox(ax, x, y, w, h, fc='white', ec=S.AXIS, lw=0.7, r=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw))


def arrow(ax, x1, y1, x2, y2, color=S.INK2, lw=0.7):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='-|>', lw=lw, color=color, shrinkA=0, shrinkB=0, mutation_scale=7))


# ============================================================ 图1 技术路线与医案筛选流程
def fig01():
    s = R['summary']
    fig = plt.figure(figsize=(S.FULL_W, 12.8 * S.CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    def box(x, y, w, h, lines, fc='white', ec=S.AXIS, lw=0.7, size=7.5, bold_first=False, color=S.INK):
        rbox(ax, x, y, w, h, fc, ec, lw)
        if isinstance(lines, str):
            lines = [lines]
        gap = 3.05 * size / 7.5
        y0 = y + h / 2 + gap * (len(lines) - 1) / 2
        for k, t in enumerate(lines):
            ax.text(x + w / 2, y0 - k * gap, t, ha='center', va='center', fontsize=size, color=color,
                    fontweight='bold' if (bold_first and k == 0) else 'normal')

    box(12, 64.5, 76, 9.3,
        [f'V1 两书版知识图谱　{s["v1_nodes"]:,} 节点 · {s["v1_edges"]:,} 关系',
         '俞根初（《俞根初临证经验集要》）1,156 条关系　｜　《何廉臣医案》657 案 · 16,342 条关系'],
        fc=S.BLUE_RAMP[0], ec=S.ACCENT, lw=0.9, size=7.8, bold_first=True)
    # 左列：医案筛选
    box(3, 51.5, 42, 8.5, ['智能体检索：案名或诊断含「咳」「嗽」',
                           f'候选医案 {s["candidates"]} 例（案名 {s["cand_title"]} 例、诊断 {s["cand_diag"]} 例，两者兼有 {s["cand_both"]} 例）'],
        size=7.2)
    box(3, 39.5, 42, 7.8, [f'纳入医案 {s["included"]} 例', f'（敏感性分析：扩展纳入兼见咳嗽症状者 {s["extended"]} 例）'],
        ec=S.ACCENT, lw=0.9, size=7.3, bold_first=True)
    box(3, 23.5, 42, 12.5, ['规范化与要素提取',
                            f'原书药名 {s["raw_spellings"]} 种写法 → 规范药名 {s["distinct_herbs"]} 味',
                            f'丸散成药 {s["patent_kinds"]} 种单列；剂量 {R["dose"]["n"]:,} 条（折算为钱）',
                            '病机 8 类 · 治法要素 10 项 · 舌、脉（分左右）、痰象'], size=7.2, bold_first=True)
    arrow(ax, 30, 64.5, 24, 60)
    arrow(ax, 24, 51.5, 24, 47.3)
    ax.plot([24, 48.5], [49.4, 49.4], color=S.INK2, lw=0.7)
    arrow(ax, 44.9, 49.4, 48.5, 49.4)
    box(48.5, 45.2, 18.5, 8.4, [f'排除 {len(s["excluded"])} 例', '图谱无用药关系', '（原文有方，抽取缺失）'], size=6.5,
        color=S.INK2)
    arrow(ax, 24, 39.5, 24, 36)
    # 右列：俞根初
    y = R['yu']
    pref = ['新加三拗汤', '葱豉桔梗汤', '越婢加半夏汤', '小青龙汤', '葳蕤汤', '桑丹泻白汤', '陷胸承气汤', '加味凉膈煎']
    forms = sorted(y['formulas_orig'], key=lambda f: (pref.index(f) if f in pref else len(pref), f))
    box(70, 23.5, 27, 36.5,
        ['俞根初理法', '（据《俞根初临证经验集要》）', '',
         f'肺系咳喘方证 {y["rows"]} 条 · 方剂 {len(y["formulas"])} 首', f'（直接论治咳嗽 {y["rows_direct"]} 条）', '',
         f'俞氏原论方 {len(forms)} 首：'] + wrap_tokens(forms, 12) +
        ['', f'理法互证 {len(R["yu_he"])} 项（表 7）'], size=6.8, bold_first=True)
    arrow(ax, 70, 64.5, 83.5, 60)
    # 分析模块
    mods = ['频次 · 功效\n性味归经', '剂量与\n用药特色', '关联规则\n（Apriori）', '共现网络\n层次聚类', '病机—治法\n—用药', '四诊特征\n症药关联']
    w, gap, x0 = 13.2, 1.55, 3
    xs = [x0 + i * (w + gap) for i in range(6)]
    for i, (xx, m) in enumerate(zip(xs, mods)):
        rbox(ax, xx, 9.8, w, 8.6, fc=S.BLUE_RAMP[0], ec=S.BLUE_RAMP[3])
        ax.text(xx + w / 2, 16.6, '①②③④⑤⑥'[i], ha='center', va='center', fontsize=7.4)
        ax.text(xx + w / 2, 12.9, m, ha='center', va='center', fontsize=7.0, linespacing=1.35)
    arrow(ax, 24, 23.5, 24, 20.6)
    ax.plot([xs[0] + w / 2, xs[-1] + w / 2], [20.6, 20.6], color=S.INK2, lw=0.7)
    for xx in xs:
        arrow(ax, xx + w / 2, 20.6, xx + w / 2, 18.4)
        arrow(ax, xx + w / 2, 9.8, xx + w / 2, 7.2)
    # 俞根初 → 结论（理法互证）
    lane = 94.6
    ax.plot([lane, lane], [23.5, 7.2], color=S.INK2, lw=0.7)
    arrow(ax, lane, 8.5, lane, 7.2)
    ax.text(lane - 0.8, 15.5, '理法\n互证', ha='right', va='center', fontsize=6.6, color=S.INK2, linespacing=1.2)
    rbox(ax, 3, 0.8, 94, 6.4, fc='white', ec=S.ACCENT, lw=0.9)
    ax.text(50, 4.0, '咳嗽用药规律与辨治特点：核心药物 · 药对 · 药物组合 · 病机用药　→　数智传承智能体知识库'
                     '（结论逐条回溯至原文段落编号）', ha='center', va='center', fontsize=7.4, fontweight='bold')
    S.save(fig, OUT, 'fig01_research_framework')


# ============================================================ 图2 高频药物频次与功效分类
def fig02():
    top = R['herbs'][:30]
    fig = plt.figure(figsize=(S.FULL_W, 11.8 * S.CM))
    axA = fig.add_axes([0.085, 0.07, 0.43, 0.87])
    axB = fig.add_axes([0.715, 0.34, 0.265, 0.60])
    y = np.arange(len(top))[::-1]
    col = [S.ACCENT if h['cat'] == KEY_CAT else S.DEEMPH for h in top]
    axA.barh(y, [h['pct'] for h in top], color=col, height=0.62, zorder=2)
    for yy, h in zip(y, top):
        tip(axA, h['pct'], yy, f"{h['n']}")
    axA.set_yticks(y, [h['herb'] for h in top])
    axA.set_xlim(0, 62)
    axA.set_ylim(-0.7, len(top) - 0.3)
    axA.set_xlabel(f'使用频率/%（n = {N}；柱端数字为医案数）')
    clean_left(axA)
    hgrid(axA)
    axA.legend(handles=[Rectangle((0, 0), 1, 1, fc=S.ACCENT), Rectangle((0, 0), 1, 1, fc=S.DEEMPH)],
               labels=['化痰止咳平喘药', '其他功效类别'], loc='lower right', handlelength=1.0, handleheight=0.8)
    S.panel(axA, 'A', x=-0.12)

    cats = [c for c in R['categories'] if c['cat'] != '未归类']
    main = [c for c in cats if c['pct'] >= 2.0]
    rest = [c for c in cats if c['pct'] < 2.0]
    rows = main + [dict(cat='其他', pct=round(sum(c['pct'] for c in rest), 1))]
    un = next((c for c in R['categories'] if c['cat'] == '未归类'), None)
    if un:
        rows.append(dict(cat='未归类（待考）', pct=un['pct']))
    yb = np.arange(len(rows))[::-1]
    axB.barh(yb, [r['pct'] for r in rows], color=[S.ACCENT if r['cat'] == KEY_CAT else S.DEEMPH for r in rows],
             height=0.62, zorder=2)
    for yy, r in zip(yb, rows):
        tip(axB, r['pct'], yy, f"{r['pct']:.1f}", dx=0.8)
    axB.set_yticks(yb, [r['cat'] for r in rows])
    axB.set_xlim(0, 50)
    axB.set_xlabel(f'占药次比例/%（{R["summary"]["herb_uses"]:,} 药次）')
    clean_left(axB)
    hgrid(axB)
    S.panel(axB, 'B', x=-0.42)
    note = wrap_tokens([c['cat'] for c in rest], 16)
    fig.text(0.60, 0.215, '其他：' + '\n　　　'.join(note), fontsize=6.3, color=S.INK2, va='top', ha='left', linespacing=1.4)
    S.save(fig, OUT, 'fig02_herb_frequency_efficacy')


# ============================================================ 图3 四气五味归经
def fig03():
    p = R['properties']
    fig, axes = plt.subplots(1, 3, figsize=(S.FULL_W, 6.6 * S.CM), gridspec_kw=dict(width_ratios=[5, 7, 12], wspace=0.26))
    data = [('四气', p['qi']), ('五味', p['wei']), ('归经', sorted(p['gui'], key=lambda x: -x['pct']))]
    for k, (ax, (title, rows)) in enumerate(zip(axes, data)):
        rows = [r for r in rows if r['uses'] > 0]
        x = np.arange(len(rows))
        ax.bar(x, [r['pct'] for r in rows], color=S.ACCENT, width=0.62, zorder=2)
        for xx, r in zip(x, rows):
            ax.text(xx, r['pct'] + 1.2, f"{r['pct']:.1f}", ha='center', va='bottom', fontsize=6.0, color=S.INK2)
        ax.set_xticks(x, [vlabel(r['k']) for r in rows], linespacing=0.95)
        ax.tick_params(axis='x', length=0)
        ax.set_ylim(0, 92 if title == '归经' else 64)
        ax.set_title(title, fontsize=8, pad=4)
        hgrid(ax, 'y')
        if k == 0:
            ax.set_ylabel('占药次比例/%')
        S.panel(ax, 'ABC'[k], x=-0.08 if k else -0.22)
    fig.text(0.5, -0.07, f'统计 {p["covered_uses"]:,} 药次（占全部单味药药次 {p["coverage_pct"]}%，性味待考者未计）；'
             '一药多味、多经者分别计入，故五味、归经合计超过 100%。', ha='center', fontsize=6.4, color=S.INK2)
    S.save(fig, OUT, 'fig03_nature_flavor_meridian')


# ============================================================ 图4 用量分布与用药特色
def fig04():
    d = R['dose']
    rows = sorted([x for x in d['by_herb'] if x['herb'] in R['high_freq']], key=lambda x: (x['median'], x['q3']))
    fig = plt.figure(figsize=(S.FULL_W, 12.0 * S.CM))
    axA = fig.add_axes([0.08, 0.075, 0.50, 0.82])
    axB = fig.add_axes([0.745, 0.33, 0.235, 0.36])
    rng = np.random.default_rng(3)
    for i, x in enumerate(rows):
        v = np.array(x['values'])
        jit = rng.uniform(-0.18, 0.18, len(v))
        axA.scatter(v, i + jit, s=4, color=S.ACCENT, alpha=0.35, lw=0, zorder=2)
        axA.plot([x['q1'], x['q3']], [i, i], color=S.INK, lw=2.2, solid_capstyle='butt', zorder=3, alpha=0.5)
        axA.plot([x['median']] * 2, [i - 0.32, i + 0.32], color=S.INK, lw=1.1, zorder=4)
    axA.set_xscale('log', base=2)
    ticks = [0.25, 0.5, 1, 2, 4, 8, 16, 32]
    axA.set_xticks(ticks, ['0.25', '0.5', '1', '2', '4', '8', '16', '32'])
    axA.minorticks_off()
    vmax = max(max(x['values']) for x in rows)
    axA.set_xlim(0.2, max(24, vmax * 1.25))           # 须容下最大值（鲜刮竹茹五两 = 50 钱）
    axA.set_yticks(range(len(rows)), [x['herb'] for x in rows])
    axA.set_ylim(-0.7, len(rows) - 0.3)
    clean_left(axA)
    axA.axvline(3, color=S.MUTED, lw=0.6, zorder=1)
    hgrid(axA)
    axA.set_xlabel('单次处方剂量/钱（对数坐标；1 钱 ≈ 3 g）')
    axA.legend(handles=[Line2D([0], [0], marker='o', ls='', color=S.ACCENT, alpha=0.5, ms=3),
                        Line2D([0], [0], color=S.INK, lw=2.2, alpha=0.5), Line2D([0], [0], color=S.INK, lw=1.1),
                        Line2D([0], [0], color=S.MUTED, lw=0.6)],
               labels=['单条剂量记录', '四分位间距', '中位数', '3 钱参考线'], loc='lower left', bbox_to_anchor=(0.0, 1.0),
               ncol=4, handlelength=1.4, columnspacing=1.0, borderaxespad=0.3)
    S.panel(axA, 'A', x=-0.1, y=1.03)

    fig.text(0.625, 0.93, '剂量概况', fontsize=7.6, fontweight='bold', va='top')
    hv = dict(d['heavy'])
    fig.text(0.625, 0.885,
             f'全部单味药剂量记录 {d["n"]:,} 条\n中位数 {d["median"]:.1f} 钱（P25–P75：{d["q1"]:.1f}–{d["q3"]:.1f} 钱）\n'
             f'≤2 钱 {d["le2"]}%　≤3 钱 {d["le3"]}%　>5 钱 {d["gt5"]}%\n'
             f'>5 钱的 {d["heavy_n"]} 条中，蛤壳 {hv.get("蛤壳", 0)}、石决明 {hv.get("石决明", 0)} 条\n'
             f'（介石类），其次为桑枝 {hv.get("桑枝", 0)}、冬瓜皮 {hv.get("冬瓜皮", 0)}、鲜地黄 {hv.get("地黄", 0)} 条',
             fontsize=6.6, color=S.INK2, va='top', linespacing=1.55)
    f = sorted(R['features'], key=lambda x: x['pct'])
    yb = np.arange(len(f))
    axB.barh(yb, [x['pct'] for x in f], color=S.ACCENT, height=0.6, zorder=2)
    for yy, x in zip(yb, f):
        tip(axB, x['pct'], yy, f"{x['cases']}（{x['pct']:.1f}%）", dx=1.5)
    axB.set_yticks(yb, [x['k'] for x in f])
    axB.set_xlim(0, 100)
    axB.set_xlabel(f'医案占比/%（n = {N}）')
    clean_left(axB)
    hgrid(axB)
    S.panel(axB, 'B', x=-0.5, y=1.04)
    notes = {x['k']: x['note'] for x in R['features']}
    lines = ['示例']
    for k in ['使用鲜药', '标注产地（道地）']:
        toks = notes[k].split('、')
        lines += wrap_tokens(toks, 17)
        lines[-len(wrap_tokens(toks, 17))] = f'{k.split("（")[0]}：' + lines[-len(wrap_tokens(toks, 17))]
    lines += ['相拌同煎：如「保和丸三钱拌滑石四钱」', '　　　　　「旋覆花二钱拌辰砂一钱」']
    fig.text(0.625, 0.235, '\n'.join(lines), fontsize=6.2, color=S.INK2, va='top', ha='left', linespacing=1.45)
    S.save(fig, OUT, 'fig04_dose_and_features')


# ============================================================ 图5 高频药物共现网络（圆形布局，按聚类树叶序）
def fig05():
    nw = R['network']
    order = R['cluster']['order']
    groups = []
    for h in order:
        if not groups or CL_OF[h] != CL_OF[groups[-1][-1]]:
            groups.append([])
        groups[-1].append(h)
    slots = len(order) + len(groups)          # 组间留一格空隙
    ang = {}
    k = 0
    for g in groups:
        for h in g:
            ang[h] = math.pi / 2 - 2 * math.pi * (k + 0.5) / slots
            k += 1
        k += 1
    pos = {h: (math.cos(a), math.sin(a)) for h, a in ang.items()}

    fig = plt.figure(figsize=(S.FULL_W, 12.2 * S.CM))
    ax = fig.add_axes([0.0, 0.02, 0.66, 0.96])
    ws = [e['w'] for e in nw['edges']]
    wmin, wmax = min(ws), max(ws)

    def ew(w):
        t = (w - wmin) / (wmax - wmin)
        return 0.35 + 2.6 * t, 0.22 + 0.55 * t
    for e in sorted(nw['edges'], key=lambda e: e['w']):
        a, b = e['a'], e['b']
        (x1, y1), (x2, y2) = pos[a], pos[b]
        same = CL_OF[a] == CL_OF[b] and CL_OF[a] in BIG
        lw, al = ew(e['w'])
        path = MPath([(x1 * 0.96, y1 * 0.96), ((x1 + x2) * 0.18, (y1 + y2) * 0.18), (x2 * 0.96, y2 * 0.96)],
                     [MPath.MOVETO, MPath.CURVE3, MPath.CURVE3])
        ax.add_patch(PathPatch(path, fc='none', ec=CL_COLOR[CL_OF[a]] if same else '#6f6e69', lw=lw, alpha=al,
                               zorder=1, capstyle='round'))
    strength = {n['herb']: n['strength'] for n in nw['nodes']}
    degree = {n['herb']: n['degree'] for n in nw['nodes']}
    top_core = sorted(strength, key=lambda h: -strength[h])[:6]
    for h in order:
        x, y = pos[h]
        ax.scatter([x], [y], s=18 + 3.2 * FREQ[h], color=CL_COLOR[CL_OF[h]], edgecolors='white', linewidths=1.0, zorder=3)
        a = ang[h]
        ca, sa = math.cos(a), math.sin(a)
        kw = dict(fontsize=7.3 if h in top_core else 6.9, fontweight='bold' if h in top_core else 'normal', color=S.INK)
        if abs(ca) < 0.5:                      # 上下两段：竖排，避免相邻药名横向重叠
            ax.text(1.14 * ca, 1.14 * sa, vlabel(h), ha='center', va='bottom' if sa > 0 else 'top', linespacing=0.95, **kw)
        else:
            ax.text(1.14 * ca, 1.14 * sa, h, ha='left' if ca > 0 else 'right', va='center', **kw)
    # 分组弧线（节点与药名之间）与组号（圈内）
    for g in groups:
        c = CL_OF[g[0]]
        a0 = math.degrees(ang[g[0]]) + 360 / slots * 0.42
        a1 = math.degrees(ang[g[-1]]) - 360 / slots * 0.42
        ax.add_patch(Arc((0, 0), 2.16, 2.16, theta1=a1, theta2=a0, color=CL_COLOR[c] if c in BIG else S.MUTED, lw=1.8))
        am = math.radians((a0 + a1) / 2)
        ax.text(0.86 * math.cos(am), 0.86 * math.sin(am), cl_label(c), ha='center', va='center', fontsize=7,
                fontweight='bold' if c in BIG else 'normal', color=S.INK2, zorder=5,
                path_effects=[pe.withStroke(linewidth=2.4, foreground='white')])
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')

    lx = fig.add_axes([0.67, 0.05, 0.32, 0.9])
    lx.set_xlim(0, 1)
    lx.set_ylim(0, 1)
    lx.axis('off')
    yy = 0.97
    lx.text(0, yy, '节点颜色 · 层次聚类分组（图 6）', fontsize=7.4, fontweight='bold', va='top')
    yy -= 0.058
    for i in BIG:
        lx.scatter([0.03], [yy - 0.012], s=40, color=CL_COLOR[i])
        lx.text(0.08, yy, f'{cl_label(i)}　{"、".join(CLUSTERS[i][:4])}等 {len(CLUSTERS[i])} 味', fontsize=6.6, va='top')
        yy -= 0.045
    lx.scatter([0.03], [yy - 0.012], s=40, color=S.DEEMPH)
    lx.text(0.08, yy, '其余小组（C1–C3、C6、C8）', fontsize=6.6, va='top')
    yy -= 0.085
    lx.text(0, yy, '节点大小 · 使用频次（案）', fontsize=7.4, fontweight='bold', va='top')
    yy -= 0.075
    for k, v in enumerate([15, 35, 65]):
        lx.scatter([0.07 + k * 0.25], [yy], s=18 + 3.2 * v, color='white', edgecolors=S.INK2, linewidths=0.6)
        lx.text(0.07 + k * 0.25, yy - 0.045, str(v), fontsize=6.6, ha='center', va='top')
    yy -= 0.115
    lx.text(0, yy, '连线 · 共现频次（案）', fontsize=7.4, fontweight='bold', va='top')
    yy -= 0.058
    for k, v in enumerate([wmin, round((wmin + wmax) / 2), wmax]):
        lw, al = ew(v)
        lx.plot([0.02 + k * 0.25, 0.17 + k * 0.25], [yy, yy], color='#6f6e69', lw=lw, alpha=al)
        lx.text(0.095 + k * 0.25, yy - 0.025, str(int(v)), fontsize=6.6, ha='center', va='top')
    yy -= 0.07
    lx.text(0, yy, f'仅画共现 ≥ {nw["min_co"]} 案（≥ 10%）的药对，共 {len(nw["edges"])} 条；\n组内连线用该组颜色。',
            fontsize=6.4, color=S.INK2, va='top', linespacing=1.45)
    yy -= 0.1
    lx.text(0, yy, '核心药物 · 加权度前 6（加粗）', fontsize=7.4, fontweight='bold', va='top')
    yy -= 0.052
    for h in top_core:
        lx.text(0.03, yy, f'{h}', fontsize=6.7, va='top')
        lx.text(0.3, yy, f'度 {degree[h]}　加权度 {strength[h]}', fontsize=6.6, va='top', color=S.INK2)
        yy -= 0.04
    S.save(fig, OUT, 'fig05_cooccurrence_network')


# ============================================================ 图6 层次聚类
def _members(Z, k, n):
    if k < n:
        return [k]
    a, b = int(Z[k - n, 0]), int(Z[k - n, 1])
    return _members(Z, a, n) + _members(Z, b, n)


def fig06():
    cl = R['cluster']
    Z = np.array(cl['Z'])
    labels = cl['labels']
    fig = plt.figure(figsize=(S.FULL_W, 15.2 * S.CM))
    axD = fig.add_axes([0.02, 0.14, 0.2, 0.8])
    axH = fig.add_axes([0.28, 0.14, 0.60, 0.8])
    axC = fig.add_axes([0.955, 0.40, 0.013, 0.3])
    n = len(labels)

    def link_color(k):
        cs = {CL_OF[labels[m]] for m in _members(Z, k, n)}
        return CL_COLOR[cs.pop()] if len(cs) == 1 else S.MUTED
    dn = dendrogram(Z, labels=labels, orientation='left', ax=axD, link_color_func=link_color, no_labels=True,
                    above_threshold_color=S.MUTED)
    for coll in axD.collections:
        coll.set_linewidth(0.8)
    axD.invert_yaxis()
    axD.set_yticks([])
    for sp in ['left', 'right', 'top']:
        axD.spines[sp].set_visible(False)
    axD.spines['bottom'].set_color(S.AXIS)
    axD.set_xlabel('Jaccard 距离', fontsize=7)
    axD.tick_params(axis='x', labelsize=6.5)
    order = dn['ivl']
    M = np.array(cl['jaccard_sim'])
    idx = [labels.index(h) for h in order]
    M = M[np.ix_(idx, idx)]
    np.fill_diagonal(M, np.nan)
    cmap = blue_cmap()
    cmap.set_bad('white')
    im = axH.imshow(M, cmap=cmap, vmin=0, vmax=0.6, aspect='auto', interpolation='nearest')
    axH.set_xticks(range(n), [vlabel(h) for h in order], fontsize=6.4, linespacing=0.92)
    axH.set_yticks(range(n), order, fontsize=6.8)
    axH.tick_params(length=0)
    for sp in axH.spines.values():
        sp.set_visible(False)
    groups = []
    start = 0
    for i in range(1, n + 1):
        if i == n or CL_OF[order[i]] != CL_OF[order[i - 1]]:
            groups.append((start, i - 1, CL_OF[order[i - 1]]))
            start = i
    for a, b, c in groups:
        axH.add_patch(Rectangle((a - 0.5, a - 0.5), b - a + 1, b - a + 1, fill=False, ec=S.INK, lw=0.8))
        axH.text(n - 0.5 + 0.6, (a + b) / 2, cl_label(c), fontsize=7, va='center', ha='left', color=S.INK,
                 fontweight='bold' if c in BIG else 'normal')
    cb = fig.colorbar(im, cax=axC)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6.5, length=2)
    cb.set_label('Jaccard 相似系数', fontsize=7)
    fig.text(0.01, 0.955, 'A', fontsize=9, fontweight='bold', family='Liberation Serif', va='bottom')
    fig.text(0.035, 0.955, '聚类树状图', fontsize=7.4, color=S.INK, va='bottom')
    fig.text(0.25, 0.955, 'B', fontsize=9, fontweight='bold', family='Liberation Serif', va='bottom')
    fig.text(0.275, 0.955, '高频药物两两共现相似度（按树状图叶序排列，方框示分组）', fontsize=7.4, color=S.INK, va='bottom')
    fig.text(0.02, 0.012, f'{len(labels)} 味高频药物（使用频率 ≥ 10%）；Jaccard 距离、类平均法（UPGMA）；共表型相关系数 {cl["cophenetic"]:.3f}；'
             f'按平均轮廓系数确定分组数 k = {cl["k"]}。', fontsize=6.4, color=S.INK2)
    S.save(fig, OUT, 'fig06_hierarchical_clustering')


# ============================================================ 图7 病机类别 × 治法 × 用药
def fig07():
    T = R['types']
    main = T['main']
    fig = plt.figure(figsize=(S.FULL_W, 17.5 * S.CM))
    axA = fig.add_axes([0.2, 0.70, 0.27, 0.23])
    axB = fig.add_axes([0.2, 0.09, 0.27, 0.49])
    axC = fig.add_axes([0.62, 0.09, 0.27, 0.84])
    axCb = fig.add_axes([0.925, 0.32, 0.012, 0.25])
    order = T['order']
    y = np.arange(len(order))[::-1]
    vals = [T['n'][t] for t in order]
    axA.barh(y, vals, color=[S.ACCENT if t in main else S.DEEMPH for t in order], height=0.62, zorder=2)
    for yy, v in zip(y, vals):
        tip(axA, v, yy, f'{v}（{100 * v / N:.1f}%）', dx=0.5)
    axA.set_yticks(y, [T['zh'][t].split('（')[0] for t in order])
    axA.set_xlim(0, 42)
    axA.set_xlabel('医案数/例')
    clean_left(axA)
    hgrid(axA)
    axA.legend(handles=[Rectangle((0, 0), 1, 1, fc=S.ACCENT), Rectangle((0, 0), 1, 1, fc=S.DEEMPH)],
               labels=['纳入比较（n ≥ 10）', '例数少，未比较'], loc='lower left', bbox_to_anchor=(-0.02, 1.0), ncol=2,
               handlelength=1.0, columnspacing=1.0, borderaxespad=0.2)
    S.panel(axA, 'A', x=-0.55, y=1.1)
    cmap = blue_cmap()
    coln = [f'{TYPE_SHORT[t]}\n(n={T["n"][t]})' for t in main]

    def heat(ax, rows, cellmap, marks=None):
        M = np.array([[cellmap[(r, t)]['pct'] for t in main] for r in rows])
        im = ax.imshow(M, cmap=cmap, vmin=0, vmax=100, aspect='auto')
        for i, r in enumerate(rows):
            for j, t in enumerate(main):
                v = M[i, j]
                txt = f'{v:.0f}' + (marks.get((r, t), '') if marks else '')
                ax.text(j, i, txt, ha='center', va='center', fontsize=6.2, color='white' if v > 55 else S.INK)
        ax.set_xticks(range(len(main)), coln, fontsize=6.8)
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(rows)), rows, fontsize=7)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_xticks(np.arange(-0.5, len(main)), minor=True)
        ax.set_yticks(np.arange(-0.5, len(rows)), minor=True)
        ax.grid(which='minor', color='white', linewidth=1.2)
        ax.tick_params(which='minor', length=0)
        return im
    pc = {(c['el'], c['type']): c for c in R['type_prin']['cells']}
    heat(axB, R['type_prin']['elements'], pc)
    S.panel(axB, 'B', x=-0.55, y=1.08)
    hc = {(c['herb'], c['type']): c for c in R['type_herb']['cells']}
    marks = {k: ('**' if c['q'] < 0.05 else '*') for k, c in hc.items() if c['p'] < 0.05}
    im = heat(axC, R['type_herb']['herbs'], hc, marks)
    S.panel(axC, 'C', x=-0.22, y=1.035)
    cb = fig.colorbar(im, cax=axCb)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6.5, length=2)
    cb.set_label('该类医案中的比例/%', fontsize=7)
    fig.text(0.2, 0.045, '列名为病机类别简称（全称见 A）。B：含该治法要素的医案比例（一案可含多项）；C：该药的使用率。', fontsize=6.3, color=S.INK2)
    fig.text(0.2, 0.022, '* 单侧 Fisher 精确检验 P < 0.05（该药在本类医案中的使用率高于其余医案）；** 经 Benjamini–Hochberg 校正 q < 0.05。',
             fontsize=6.3, color=S.INK2)
    S.save(fig, OUT, 'fig07_pathogenesis_principle_herb')


# ============================================================ 图8 四诊特征
def fig08():
    fig = plt.figure(figsize=(S.FULL_W, 13.5 * S.CM))
    axA = fig.add_axes([0.09, 0.56, 0.36, 0.38])
    axB = fig.add_axes([0.61, 0.56, 0.36, 0.38])
    axC = fig.add_axes([0.09, 0.07, 0.36, 0.38])
    axD = fig.add_axes([0.61, 0.07, 0.36, 0.38])

    def bars(ax, rows, denom, xlabel, letter, xmax):
        y = np.arange(len(rows))[::-1]
        ax.barh(y, [100 * r['n'] / denom for r in rows], color=S.ACCENT, height=0.6, zorder=2)
        for yy, r in zip(y, rows):
            tip(ax, 100 * r['n'] / denom, yy, str(r['n']), dx=0.6)
        ax.set_yticks(y, [r['k'] for r in rows])
        ax.set_xlim(0, xmax)
        ax.set_xlabel(xlabel)
        clean_left(ax)
        hgrid(ax)
        S.panel(ax, letter, x=-0.2)
    bars(axA, R['symptoms'][:12], N, f'伴随症状 · 医案占比/%（n = {N}；柱端为例数）', 'A', 40)
    bars(axB, sorted(R['sputum'], key=lambda r: -r['n']), N, f'痰象 · 医案占比/%（n = {N}）', 'B', 40)
    tg = R['tongue']
    bars(axC, tg['feats'], tg['cases'], f'舌象 · 医案占比/%（有舌诊记录 {tg["cases"]} 例）', 'C', 60)
    pl = R['pulse']
    feats = sorted([f for f in pl['feats'] if f['right'] + f['left'] >= 5], key=lambda f: -(f['right'] + f['left']))
    y = np.arange(len(feats))[::-1]
    nr, nl = pl['side_cases']['右'], pl['side_cases']['左']
    axD.barh(y, [-100 * f['right'] / nr for f in feats], color=S.SERIES[1], height=0.6, zorder=2, label=f'右脉（{nr} 例）')
    axD.barh(y, [100 * f['left'] / nl for f in feats], color=S.SERIES[0], height=0.6, zorder=2, label=f'左脉（{nl} 例）')
    for yy, f in zip(y, feats):
        if f['right']:
            axD.text(-100 * f['right'] / nr - 2, yy, str(f['right']), ha='right', va='center', fontsize=6.3, color=S.INK2)
        if f['left']:
            axD.text(100 * f['left'] / nl + 2, yy, str(f['left']), ha='left', va='center', fontsize=6.3, color=S.INK2)
    axD.set_yticks(y, [f['k'] for f in feats])
    axD.axvline(0, color=S.AXIS, lw=0.6)
    axD.set_xlim(-100, 100)
    axD.set_xticks([-80, -40, 0, 40, 80], ['80', '40', '0', '40', '80'])
    axD.set_xlabel('脉象 · 占该侧有记录医案的比例/%')
    clean_left(axD)
    hgrid(axD)
    axD.legend(loc='lower left', bbox_to_anchor=(0.0, 1.0), ncol=2, handlelength=1.0, columnspacing=1.2, borderaxespad=0.2)
    S.panel(axD, 'D', x=-0.12, y=1.1)
    S.save(fig, OUT, 'fig08_four_diagnostics')


# ============================================================ 图9 症、舌、脉与药物关联
def fig09():
    fh = R['feat_herb']
    feats = [f['k'] for f in fh['features']]
    nfeat = {f['k']: f['n'] for f in fh['features']}
    herbs = fh['herbs']
    cell = {(c['feat'], c['herb']): c for c in fh['cells']}
    M = np.full((len(feats), len(herbs)), np.nan)
    for i, f in enumerate(feats):
        for j, h in enumerate(herbs):
            c = cell[(f, h)]
            if c['n'] >= 3:
                M[i, j] = math.log2(c['lift'])
    fig = plt.figure(figsize=(S.FULL_W, 14.0 * S.CM))
    ax = fig.add_axes([0.2, 0.09, 0.68, 0.74])
    cax = fig.add_axes([0.91, 0.3, 0.013, 0.36])
    cmap = LinearSegmentedColormap.from_list('div', ['#184f95', '#6da7ec', S.NEUTRAL_MID, '#e87574', '#b52f2f'])
    cmap.set_bad('white')
    im = ax.imshow(M, cmap=cmap, norm=TwoSlopeNorm(vcenter=0, vmin=-2, vmax=2), aspect='auto')
    for i, f in enumerate(feats):
        for j, h in enumerate(herbs):
            c = cell[(f, h)]
            if c['n'] >= 5 and c['lift'] >= 1.5:
                ax.text(j, i, f"{c['lift']:.1f}", ha='center', va='center', fontsize=5.8,
                        color='white' if c['lift'] >= 2 else S.INK)
    sym_set = {x['k'] for x in R['symptoms']}
    groups = [('伴随症状', [f for f in feats if f in sym_set]),
              ('痰象', [f for f in feats if f not in sym_set and ('痰' in f)]),
              ('舌象', [f for f in feats if f.startswith('舌') or f.startswith('苔')]),
              ('脉象', [f for f in feats if '脉' in f])]
    ax.set_yticks(range(len(feats)), [f'{f}（{nfeat[f]}）' for f in feats], fontsize=6.8)
    ax.set_xticks(range(len(herbs)), [vlabel(h) for h in herbs], fontsize=6.6, linespacing=0.92)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(herbs)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(feats)), minor=True)
    ax.grid(which='minor', color='white', linewidth=0.9)
    ax.tick_params(which='minor', length=0)
    for name, members in groups:
        if not members:
            continue
        i0, i1 = feats.index(members[0]), feats.index(members[-1])
        if i0 > 0:
            ax.axhline(i0 - 0.5, color=S.INK, lw=0.7)
        yc = 1 - (i0 + i1 + 1) / 2 / len(feats)
        ax.text(-0.215, yc, vlabel(name), transform=ax.transAxes, ha='center', va='center', fontsize=7.2,
                fontweight='bold', color=S.INK2, linespacing=1.0)
        ax.plot([-0.19, -0.19], [1 - i0 / len(feats) - 0.004, 1 - (i1 + 1) / len(feats) + 0.004], transform=ax.transAxes,
                color=S.AXIS, lw=0.8, clip_on=False)
    cb = fig.colorbar(im, cax=cax, ticks=[-2, -1, 0, 1, 2])
    cb.ax.set_yticklabels(['0.25', '0.5', '1', '2', '4'], fontsize=6.5)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2)
    cb.set_label('提升度（对数色阶）', fontsize=7)
    fig.text(0.2, 0.045, '提升度 = P(用药 | 具该特征) / P(用药)，> 1 表示具该特征的医案中更常用此药；共现 < 3 案者留白；', fontsize=6.3, color=S.INK2)
    fig.text(0.2, 0.022, '格内数值为提升度 ≥ 1.5 且共现 ≥ 5 案者；行名括号内为具该特征的医案数；药物为使用频率前 20 味。', fontsize=6.3, color=S.INK2)
    S.save(fig, OUT, 'fig09_feature_herb_lift')


# ============================================================ 图10 典型医案：原文 → 图谱 → 分析要素
def fig10():
    ex = R['example']
    case = next(c for c in R['cases'] if c['uid'] == ex['uid'])
    fig = plt.figure(figsize=(S.FULL_W, 14.2 * S.CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 83)
    ax.axis('off')
    top = 80.5
    # ① 原文
    rbox(ax, 1.5, 5, 30.5, top - 5, r=1.0)
    ax.text(3, top - 2.5, '① 原文段落', fontsize=7.8, fontweight='bold', va='top')
    ax.text(3, top - 6.3, f'{ex["pid"]}　《何廉臣医案》', fontsize=6.8, color=S.INK2, va='top')
    ax.text(3, top - 9.6, ex['title'], fontsize=6.8, color=S.INK2, va='top')
    paras = ex['text'].split('\n')
    lines = []
    for chunk in paras[0].replace('。', '。\n').split('\n'):
        chunk = chunk.strip()
        while chunk:
            cut = 15
            while cut < len(chunk) and chunk[cut] in '，。、；：）」』':     # 避头：标点不置行首
                cut += 1
            lines.append(chunk[:cut])
            chunk = chunk[cut:]
    lines.append('')
    for p in paras[1:]:
        lines += wrap_tokens(p.split(' '), 15, sep='　')
    ax.text(3, top - 14.2, '\n'.join(lines), fontsize=7.2, va='top', linespacing=1.7)
    rec = next(e for e in ex['edges'] if e['rel'] == 'caseUsesHerb' and e['obj'] == '马兜铃')
    ry = 32.8
    ax.plot([3, 30.5], [ry + 2.2, ry + 2.2], color=S.GRID, lw=0.8)
    ax.text(3, ry, '一条关系的出处记录（示例）', fontsize=7.0, fontweight='bold', va='top')
    fields = [('主语', rec['subject']), ('关系', 'caseUsesHerb（医案用药）'), ('宾语', rec['obj']),
              ('原文句', rec['sentence']), ('段落编号', rec['pid']), ('章节路径', rec['chapter']),
              ('逐字引文', '是' if str(rec['verbatim']) == 'True' else '否'),
              ('段内核验', '通过' if str(rec['found']) == 'True' else '未通过'),
              ('抽取引擎', f'{rec["engine"]}（{rec["agreement"]}）')]
    yy = ry - 3.4
    for k, v in fields:
        ax.text(3.6, yy, k, fontsize=6.3, color=S.INK2, va='top')
        ax.text(10.8, yy, v, fontsize=6.3, va='top')
        yy -= 2.55
    # ② 图谱关系
    rbox(ax, 35, 5, 32.5, top - 5, fc=S.BLUE_RAMP[0], ec=S.BLUE_RAMP[3], r=1.0)
    ax.text(36.5, top - 2.5, f'② 图谱关系（{len(ex["edges"])} 条）', fontsize=7.8, fontweight='bold', va='top')
    nv = sum(1 for e in ex['edges'] if str(e['verbatim']) == 'True')
    nf = sum(1 for e in ex['edges'] if str(e['found']) == 'True')
    ax.text(36.5, top - 6.3, f'逐字引文 {nv}/{len(ex["edges"])}；段内核验 {nf}/{len(ex["edges"])}', fontsize=6.8, color=S.INK2, va='top')
    rel_zh = {'caseDiagnosedAs': '医案诊断', 'caseShowsPattern': '医案证候', 'caseShowsSymptom': '医案见症',
              'caseShowsSign': '医案见象（舌、脉）', 'caseAppliesPrinciple': '医案治法', 'caseUsesHerb': '医案用药（原书写法 · 剂量）'}
    yy = top - 11.2
    groups = collections.OrderedDict()
    for e in ex['edges']:
        groups.setdefault(e['rel'], []).append(e)
    for rel, es in groups.items():
        ax.text(36.5, yy, rel_zh.get(rel, rel), fontsize=7.0, fontweight='bold', color=S.ACCENT, va='top')
        yy -= 3.0
        if rel == 'caseUsesHerb':
            items = [e['sentence'].split('（')[0] for e in es]
            for k in range(0, len(items), 2):
                ax.text(38, yy, '　'.join(items[k:k + 2]), fontsize=6.9, va='top')
                yy -= 2.75
        else:
            ax.text(38, yy, '　'.join(e['obj'] for e in es), fontsize=6.9, va='top')
            yy -= 2.75
        yy -= 1.2
    # ③ 规范化与分析要素
    rbox(ax, 71, 5, 27.5, top - 5, r=1.0)
    ax.text(72.5, top - 2.5, '③ 规范化与分析要素', fontsize=7.8, fontweight='bold', va='top')
    herbs = sorted(case['herbs'], key=lambda h: -FREQ.get(h, 0))
    in_cl = collections.Counter(cl_label(CL_OF[h]) for h in herbs if h in CL_OF)
    low = [h for h in herbs if h not in CL_OF]
    items = [
        ('病机类别', [C.TYPE_ZH[case['type']].split('（')[0] + f'（命中「{case["type_hit"]}」）']),
        ('治法要素', case['prin_el']),
        ('舌象要素', case['tongue']),
        ('脉象要素', [f'右：{"、".join(case["pulse"].get("右", []))}　左：{"、".join(case["pulse"].get("左", []))}']),
        ('痰象要素', case['sputum'] or ['—']),
        (f'规范药名（{len(herbs)} 味）', herbs),
        ('聚类分组', [f'{k} × {v}' for k, v in sorted(in_cl.items())] + ([f'低频药 {"、".join(low)}'] if low else [])),
    ]
    yy = top - 7.0
    for k, v in items:
        ax.text(72.5, yy, k, fontsize=7.0, fontweight='bold', color=S.ACCENT, va='top')
        yy -= 3.0
        wl = wrap_tokens(v, 13)
        ax.text(74, yy, '\n'.join(wl), fontsize=6.9, va='top', linespacing=1.55)
        yy -= 2.7 * len(wl) + 1.6
    for x1, x2 in [(32, 35), (67.5, 71)]:
        ax.annotate('', xy=(x2, 43), xytext=(x1, 43), arrowprops=dict(arrowstyle='-|>', lw=0.9, color=S.INK2, mutation_scale=9))
    ax.text(50, 1.8, '同一医案从原文到分析要素的完整链路：每条关系保留段落编号、原文句与核验结果，统计结论可逐条回溯。',
            ha='center', fontsize=6.6, color=S.INK2)
    S.save(fig, OUT, 'fig10_evidence_chain_example')


if __name__ == '__main__':
    import sys
    which = sys.argv[1:] or [f'fig{i:02d}' for i in range(1, 11)]
    for w in which:
        globals()[w]()
        print('ok', w)
