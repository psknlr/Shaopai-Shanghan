# 论文图表包 · Scientific Data（Data Descriptor）

绍派伤寒知识图谱与语料的投稿用图表，按 Nature Portfolio / *Scientific Data* 规范制作。
全部数字在运行时由 `data/` 计算，图与表共用 `dataset.py`，不会互相矛盾。

## 内容

| 文件 | 说明 |
| --- | --- |
| `figures/fig1–fig6.pdf` | 矢量图，文字可编辑（TrueType 嵌入，未转曲）；稠密点云层以 800 dpi 栅格化嵌入 |
| `figures/fig1–fig6.tif` | 800 dpi，RGB，LZW 无损压缩——投稿首选位图 |
| `figures/fig1–fig6.png` | 800 dpi，RGB，与 TIFF 同像素，便于预览 |
| `tables/Tables.docx` | 五张三线表（可编辑 Word），每表一页 |
| `tables/Tables.pdf` | 上述 Word 的排版预览 |
| `tables/tables.tex` | 同内容的 LaTeX（booktabs + threeparttable；中文需 XeLaTeX + xeCJK） |
| `tables/table1–5.csv`、`tables.md` | 纯数据版（CSV 带 BOM，Excel 可直接打开中文） |
| `LEGENDS.md` | 六幅图的英文图注（每条 ≤ 300 词）与五张表的标题 |
| `QC_DISPLAY_ITEMS.md` | 按 nature-display-item-qc 清单逐项机器核查的报告 |

## 图表结构（Data Descriptor 的叙事，而非假设检验）

| | 内容 | 对应章节 |
| --- | --- | --- |
| Fig. 1 | 构建流程与溯源：六步流程；一段何廉臣医案 → 9 条关系 → 一条关系记录的全部出处字段 | Methods |
| Fig. 2 | 语料构成：八部书的字数、段落数、段落长度分布 | Data Records |
| Fig. 3 | 本体与构成：类级 schema 图、各类实体数、32 种关系的数量 | Data Records |
| Fig. 4 | 拓扑：全图（上游固定布局）、度分布、连通分量 | Data Records |
| Fig. 5 | 覆盖：书 × 层关系数、各层抽取覆盖率、21 位有生卒年医家的时间跨度 | Data Records |
| Fig. 6 | 技术验证：原文独立核验、上游逐字标记 × 独立核验、支撑次数、基数例外 | Technical Validation |
| Table 1 | 八部来源文献（书目信息、字符与段落、关系数） | Methods |
| Table 2 | 本体 20 类及实例数 | Data Records |
| Table 3 | 46 种关系：定义域 → 值域、声明基数、例外数、实例数 | Data Records |
| Table 4 | 数据文件清单（格式、大小、记录数） | Data Records |
| Table 5 | 技术验证汇总 | Technical Validation |

## 规格

- 宽度 183 mm（双栏），高度 74–168 mm（≤ 170 mm）；按最终印刷尺寸制作，保存时不裁切。
- Arial 5–7 pt；面板标签 8 pt 粗体小写 a、b、c；轴标题首字母大写、单位在括号内。
- 线宽 0.3–1 pt；白底，无网格、阴影、立体与渐变。
- 配色：Okabe–Ito 色盲友好色板；六个知识层的颜色顺序经 CVD 分离度脚本验证（相邻色对 ΔE ≥ 9.6），
  所有彩色标记均有直接标注或图例。
- 中文字形：Arial 不含汉字，图中汉字自动回退到 WenQuanYi Zen Hei（黑体）；排版时可统一换成
  思源黑体 / Noto Sans CJK。这是核查报告中唯一的提示项。

## 投稿前请人工确认

1. **书目信息**：Table 1 的「Responsibility」有几部书在交付材料中没有编者 / 出版年，表中留作「–」，
   请补齐（不要让我猜）。
2. **英文译名**：医家拼音已逐一核对；中药、证候与书名的英译（如 *Sichuan fritillary bulb*、
   *Essentials of Yu Genchu's clinical experience*）请合作者审定。
3. **来源标注**：图表中《俞根初临证经验集要》按实际书名标注；网站「V1 两书版」里对应一侧显示为
   《三订通俗伤寒论》（据《俞根初临证经验集要》），论文中请沿用实际书名。
4. **当代门诊病案**：131 则逐案记录不出现在任何图表中，只在 Fig. 1 与 Table 1 注脚说明已暂缓发布。

## 重建

```bash
pip install matplotlib numpy pillow pymupdf rdflib   # 另需 Arial 与一种中文无衬线字体
python3 paper/make_figures.py        # figures/：fig1–fig6 的 PDF、TIFF、PNG（可只重建某几幅：… fig3 fig5）
python3 paper/make_tables.py         # tables/：CSV、TeX、Markdown、tables.json
npm install docx && node paper/make_tables_docx.js   # tables/Tables.docx
python3 paper/make_legends.py        # LEGENDS.md
python3 paper/qc_display_items.py    # QC_DISPLAY_ITEMS.md
```

Fig. 3a 的类节点位置由模拟退火在 4 × 3 网格上求得（最小化加权交叉与边穿节点），
结果固定写在 `make_figures.py` 的 `NODE_XY` 中，保证每次重建一致；关系标签由贪心算法避让节点、
其他标签与其他边。
