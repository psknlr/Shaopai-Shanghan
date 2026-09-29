# 绍派伤寒辨治咳嗽用药规律研究 · 论文图表（V1 两书版）

**越医·绍派伤寒数智传承智能体 —— 绍派伤寒辨治咳嗽用药规律研究**

本目录是论文用的图、表与可复现脚本，**不在站点任何页面中链接**（站点从 `main` 部署后，文件可按路径直接访问，但页面上没有入口）。
全部数字由脚本从知识图谱计算，图与表同源；改动数据或规则后重跑即可同步更新。

## 快速查看

| 文件 | 内容 |
| --- | --- |
| [`cough_v1_figures_tables.docx`](cough_v1_figures_tables.docx) | 图表合编本（Word）：图 10 幅（300 dpi 缩样，图题在下）＋表 7 张（三线表，表题在上），附说明与目录 |
| [`tables/cough_v1_tables.docx`](tables/cough_v1_tables.docx) | 七张三线表单行本（可编辑 Word，宋体/Times New Roman，小五号） |
| [`SUMMARY.md`](SUMMARY.md) | 主要结果摘要（12 条，供撰写「结果」部分参考） |
| [`LEGENDS.md`](LEGENDS.md) | 图题、表题（中英文）与图注 |
| [`tables/tables.md`](tables/tables.md) | 七张表的 Markdown 版（在 GitHub 上直接核对） |

## 数据范围

- **V1 两书版知识图谱**：`data/shaopai_kg.json` 中来源文献为《俞根初临证经验集要》（`ygc_jingyao`）与《何廉臣医案》（`hlc_yian`）的全部关系，
  即站点 `v1.html` 的同一子图（8,226 个节点，17,498 条关系；脚本载入时校验）。《俞根初临证经验集要》在 V1 中代表俞根初《三订通俗伤寒论》一系的理法。
- **不含** 2022–2026 年现代病案，本目录也不含任何现代病案信息。
- **研究对象**：《何廉臣医案》657 案中，案名或诊断含「咳」「嗽」者为候选（127 例）；排除图谱中无用药关系者 2 例（原文有方，抽取缺失：案226、案343），
  纳入 125 例。统计单位为医案，复诊医案合并各诊用药。敏感性分析另纳入症状兼见咳嗽者，共 216 例。

## 方法与参数

| 环节 | 做法 | 参数/依据 |
| --- | --- | --- |
| 药名规范 | 原书 268 种写法 → 188 味规范药名（制法、产地等修饰归并）；丸散成药 14 种单列 | 《中华人民共和国药典》（2020 年版）；对照见附表 S1 |
| 性味归经与功效 | 逐药标注四气、五味、归经、功效分类 | 药典 2020（马兜铃据 2015 版）＞《中药学》“十四五”教材＞《中华本草》；见附表 S3 |
| 剂量 | 原文剂量折算为钱（1 两 = 10 钱，1 分 = 0.1 钱）；枚、片等计数单位不折算；疑误 1 条剔除 | 1,436 条可折算记录 |
| 用药特色 | 丸散成药、相拌同煎、标注产地、鲜药、先煎代水 | 相拌、鲜药、代水按医案原文段落判读（图谱关系句多只截取单味药） |
| 频次与高频药 | 使用频率 = 用该药的医案数 / 125 | 高频：≥ 10%（≥ 13 例），33 味 |
| 关联规则 | Apriori，事务为医案 | 最小支持度 20%，最小置信度 70%，提升度 > 1 |
| 共现网络 | 高频药两两共现 | 共现 ≥ 13 案的边；Louvain 模块度 0.138（过低，不作社区解释） |
| 层次聚类 | Jaccard 距离，类平均法（UPGMA） | k 按平均轮廓系数取 8；共表型相关系数 0.813 |
| 病机归类 | 案名、诊断、证候关键词，自上而下先命中者为准 | 8 类，规则见附表 S4 |
| 治法要素 | 治法表述关键词，一案可多项 | 10 项，规则见附表 S4 |
| 组间比较 | 单侧 Fisher 精确检验，Benjamini–Hochberg 校正 | 仅比较 n ≥ 10 的 5 类 |
| 四诊 | 伴随症状、痰象、舌象、脉象（分左右手） | 症、舌、脉与药物的提升度 |
| 俞根初方证 | 图谱 `formulaTreats` 中主治含咳、嗽、痰、喘、肺者逐条判读 | 42 条 → 肺系咳喘 31 条；区分俞氏原论与书中引录的现代文献；见附表 S6 |
| 理法互证 | 俞根初论述节录（运行时逐字核对为原文子串）对照何氏医案统计 | 9 项，见表 7 |
| 稳健性 | 扩展纳入 216 例 | 前 20 味重合与 Spearman 相关，见附表 S5 |

结果可复现：统计中的全部并列排序均有显式规则，不同 `PYTHONHASHSEED` 下输出逐字节一致。

## 目录结构

```
research/cough_v1/
├── README.md · SUMMARY.md · LEGENDS.md
├── cough_v1_figures_tables.docx      图表合编本
├── figures/   fig01–fig10 × {.pdf 矢量, .png 600 dpi, .tif 600 dpi LZW}；legends.json
├── tables/    T1–T7_*.csv · tables.md · tables.json · cough_v1_tables.docx
├── supplementary/
│   ├── S1_herb_name_normalization.csv   原书写法 → 规范药名
│   ├── S2_included_cases.csv            纳入医案清单（编号、原书案名、纳入依据、病机类别、用药、治法）
│   ├── S3_herb_properties.csv           性味归经、功效分类及依据
│   ├── S4_rules_type_and_principle.csv  病机类别与治法要素的关键词规则
│   ├── S5_sensitivity_extended.csv      敏感性分析
│   └── S6_yu_formula_indications.csv    《俞根初临证经验集要》方证逐条判读
├── results/   results.json（全部统计结果）· herb_frequency.csv · dose_by_herb.csv · association_rules.csv · network_nodes.csv
└── scripts/
    ├── common.py            V1 子图载入、医案筛选、剂量解析、病机与治法规则
    ├── herb_reference.py    药名规范表与性味归经功效参考表
    ├── analysis.py          全部统计 → results/、supplementary/
    ├── style.py             期刊作图样式（字体、字号、配色、导出）
    ├── make_figures.py      图 1–图 10
    ├── make_tables.py       表 1–表 7、图题图注、结果摘要
    └── make_docx.js         Word 三线表与图表合编本
```

## 图表清单

| 编号 | 题名 | 文件 |
| --- | --- | --- |
| 图 1 | 技术路线（医案筛选、俞根初方证、分析模块） | `fig01_research_framework` |
| 图 2 | 高频药物使用频次与功效分类 | `fig02_herb_frequency_efficacy` |
| 图 3 | 四气、五味、归经 | `fig03_nature_flavor_meridian` |
| 图 4 | 单次处方剂量分布与用药特色 | `fig04_dose_and_features` |
| 图 5 | 高频药物共现网络 | `fig05_cooccurrence_network` |
| 图 6 | 层次聚类（树状图 + Jaccard 热图） | `fig06_hierarchical_clustering` |
| 图 7 | 病机类别 × 治法要素 × 用药 | `fig07_pathogenesis_principle_herb` |
| 图 8 | 伴随症状、痰象、舌象、脉象（分左右） | `fig08_four_diagnostics` |
| 图 9 | 症、舌、脉与药物的提升度 | `fig09_feature_herb_lift` |
| 图 10 | 典型医案证据链（原文 → 图谱关系 → 分析要素） | `fig10_evidence_chain_example` |
| 表 1 | 纳入医案的基本特征 | `T1_case_characteristics` |
| 表 2 | 高频药物的使用频次与药性 | `T2_high_frequency_herbs` |
| 表 3 | 高频药物单次处方剂量 | `T3_dose` |
| 表 4 | 关联规则 | `T4_association_rules` |
| 表 5 | 层次聚类所得药物组合 | `T5_herb_clusters` |
| 表 6 | 不同病机类别的核心用药与治法 | `T6_pathogenesis` |
| 表 7 | 俞根初治咳理法与何廉臣咳嗽医案用药的对应（理法互证） | `T7_yu_he_correspondence` |

**图的规格**：通栏 17 cm；中文思源宋体（Noto Serif SC），数字与西文 Liberation Serif（与 Times New Roman 等宽）；正文 7.5 pt；
PDF 中字体以 TrueType 嵌入（文字可编辑、无 Type 3）；PNG、TIFF 为 600 dpi。配色为经色觉障碍校验的分类色板，热图为单色或双色发散色阶。

## 复现

```bash
# 依赖：Python 3.11（numpy、scipy、networkx、matplotlib、pillow）；Node.js 22 + docx 9
# 字体：Noto Serif SC（SIL OFL 1.1，可由 npm 包 @expo-google-fonts/noto-serif-sc 取得 TTF）放入 ~/.fonts；Liberation Serif（fonts-liberation）
cd research/cough_v1
python3 scripts/analysis.py          # 统计 → results/、supplementary/
python3 scripts/make_figures.py      # 图 → figures/（也可只重画某几幅：make_figures.py fig04 fig07）
python3 scripts/make_tables.py       # 表、图题、摘要 → tables/、LEGENDS.md、SUMMARY.md
npm install --no-save docx@9 && node scripts/make_docx.js   # Word → tables/cough_v1_tables.docx、cough_v1_figures_tables.docx
```

## 待专家核对

1. **药名规范**（附表 S1）：如「杜兜铃」「安南子」「川黄草」「青盐陈皮」等写法的归并；「苏梗通」「败叫子」「青海粉」等含义待考者未归类。
2. **性味归经与功效分类**（附表 S3）：药典未收载者依教材或《中华本草》；金橘（金橘脯）按功效归入理气药。
3. **血见愁**：地锦草、铁苋菜、山藿香等均有此异名，基原待考，未计入性味统计；表 7 中与俞根初「加地锦」的对应仅作提示。
4. **病机类别与治法要素规则**（附表 S4）：关键词规则为可复现的近似，逐案结果见附表 S2；「病机未明示」20 例未参与组间比较。
5. **聚类组合的配伍释义**（表 5）与 **方证判读**（附表 S6，含 11 条「非肺系、仅字面命中」的剔除理由）。
6. **马兜铃**：含马兜铃酸，有肾毒性，2020 年版药典已不收载；本研究只描述文献用药规律，不作临床用药推荐。

## 局限

- 图谱抽取存在遗漏：2 例原文有方而图谱无用药关系，已排除；图谱用药关系的原文句多只截取单味药，相拌、鲜药、煎汤代水等修饰已回到医案原文段落判读。
- 病机归类依赖原书用语，约六分之一医案未明示病机；归类为规则近似，非逐案辨证。
- 剂量为原书记载，1 钱折合克数随度量衡制度而异（现代习用 ≈ 3 g，清代库平制 ≈ 3.73 g）。
- 《俞根初临证经验集要》为今人编著，书中既有俞氏原论与何秀山按语，也引录现代临床文献，表 7 与附表 S6 已区分来源性质。
- 以上均为描述性统计，结论宜结合文献与专家判读。
