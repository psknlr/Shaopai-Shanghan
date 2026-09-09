# 绍派伤寒 · 越医知识图谱 — QC Audit

**Built by** 医哲未来人工智能研究院 (IMPFAI) · https://impfai.github.io/

> 第一部分为上游随图谱交付的质检口径，照录其 meta 与自报数字；
> 第二部分「本仓库附注」记录导入本站时的实测复核与差异。本文件对应 **V6**（18,151 / 22,700）。

## 一、上游交付口径

**Sources（八种）**
- 《浙派中医丛书》专题系列·绍派伤寒, 沈钦荣主编 (2021)
- 《越医文化》十章 + 目录 + 后记
- 《何廉臣医案》660 则
- 《越中名医传》下篇 + 越中名医传补
- 《越醫雜詠》
- 《赵晴初医论》
- 《俞根初临证经验集要》沈钦荣编著（学派奠基人专著，十章）
- 《绍派伤寒史料图片研究》陶建华总审／沈钦荣、林怡冰编著（图片史料图录，204 幅）

### Graph

| | |
|---|---|
| Nodes | **18,151** |
| Edges | **22,700** |
| Ontology classes defined / populated | 16 / 15 |
| Object properties defined / used | 39 / 32 |
| Evidence verbatim | 22199/22700 (97.8%) |

`Dosage` is the one defined-but-unpopulated class: dose and unit are carried as
attributes on `Herb` (parsed to a numeric amount, including the 钱半 = 1.5 钱 idiom)
rather than reified as separate nodes.

### Extraction coverage

| Layer | Extracted / routed | Coverage |
|---|---|---|
| lineage | 544 / 544 | 100.0% |
| diagnostic | 330 / 333 | 99.1% |
| pattern | 776 / 793 | 97.9% |
| materia | 1,215 / 1,464 | 83.0% |
| case | 657 / 660 | 99.5% |
| culture | 1,802 / 2,407 | 74.9% |

Coverage is *passages extracted* over *passages routed to that layer*. **Every shortfall is a
per-frame LLM token-ceiling stop, not an exhausted corpus.** Counts drawn from a partial layer —
above all 越医文化 at 74.9% and 本草方剂 at 83.0% — are lower bounds and must never be read as
"absent from the text".

### Identity merge（本版新增）

上游 meta 的 `identity_merge` 原文：

> 繁/簡 variants collapsed via opencc t2s on (class, name); physician name variants merged only
> where the corpus itself attests the identity via the 「X…名Y」 pattern. Conflicting attributes
> resolved by counting corpus support, not by mention frequency — 何廉臣 birth_year set to 1860
> (3 passages) over 1861 (1).

| 项 | 数 |
|---|---|
| 繁简异写组 script_variant_groups | 89 |
| 医家别名对 name_variant_pairs | 5 |
| 合并节点数 nodes_merged | 93 |

### Cross validation

上游 meta 的 `cross_validation_note` 原文：

> MiniMax-M3 was requested by the user as a second engine. api.minimaxi.com is allowlisted, but the
> API key was only ever supplied as chat text, which cannot be used without copying it into the
> transcript, artifact lineage and execution log. No MiniMax call was made; every edge remains
> agreement="single_engine".

### Node classes

| Class | 中文 | Count |
|---|---|---|
| DiagnosticSign | 诊法征象 | 2,597 |
| Doctrine | 学术观点 | 2,522 |
| Symptom | 症状 | 2,216 |
| Pattern | 证候 | 2,044 |
| TreatmentPrinciple | 治法 | 1,940 |
| Disease | 病证 | 1,524 |
| Herb | 中药 | 1,379 |
| Formula | 方剂 | 1,280 |
| Work | 著作 | 758 |
| Physician | 医家 | 671 |
| CaseRecord | 医案 | 657 |
| Place | 地域 | 309 |
| Institution | 机构团体 | 137 |
| HerbProperty | 药性 | 80 |
| MedicalFamily | 医学世家 | 37 |

### Relations (top 18 of 32 used)

| Property | 中文 | Count |
|---|---|---|
| `caseUsesHerb` | 医案用药 | 8,486 |
| `caseShowsSymptom` | 医案见症 | 3,233 |
| `caseShowsSign` | 医案见象 | 1,875 |
| `proposes` | 主张 | 1,278 |
| `caseAppliesPrinciple` | 医案治法 | 1,109 |
| `signIndicates` | 征象提示 | 859 |
| `formulaTreats` | 方剂主治 | 767 |
| `caseDiagnosedAs` | 医案诊断 | 702 |
| `caseShowsPattern` | 医案辨证 | 434 |
| `authored` | 撰写 | 430 |
| `caseUsesFormula` | 医案用方 | 429 |
| `treatedByPrinciple` | 治法对应 | 428 |
| `manifestsAs` | 表现为 | 370 |
| `patternOfDisease` | 病之证候 | 360 |
| `subPatternOf` | 子证候 | 296 |
| `statedIn` | 载于 | 275 |
| `principleRealizedBy` | 治法用方 | 227 |
| `physicianOfPlace` | 籍贯 | 203 |

### Disease layer

1,524 Disease nodes; 416 of them are linked to at least one
of the 657 case records from 《何廉臣医案》.

Only **255/660 (38.6%)** of case titles contain a canonical 病名. The
remainder name a *pattern* (湿热阻中, 气虚头汗, 肝阳犯胃) — that is 何廉臣's titling convention, not a
lexicon gap, and those titles become `Pattern` nodes rather than being forced into `Disease`.

| Disease | Cases | Signature herbs (co-occurrence across its cases) |
|---|---|---|
| 咳嗽 | 37 | 瓜蒌仁、光杏仁、冬桑叶、竹茹、新会皮、紫菀 |
| 湿热 | 25 | 滑石、竹叶、瓜蒌仁、广郁金、枳实、佩兰叶 |
| 湿温 | 19 | 滑石、山栀、竹叶、苏薄荷、苏叶梗、青连翘 |
| 湿热兼风 | 13 | 滑石、佩兰叶、西茵陈、广郁金、竹叶、苏薄荷 |
| 湿热夹食 | 13 | 滑石、佛手片、竹叶、莱菔子、打鸡金、打延胡 |
| 暑湿夹食 | 11 | 竹叶、山栀、桑枝、佩兰叶、青蒿、滑石 |

These pairings are recovered from the text, not asserted from doctrine, and they land where a reader
of the school would expect: 疟 with 草果仁, 肝风 with 明天麻 and 石决明, 湿温 with 滑石 and 山栀.

### Diagnostic modalities

| Modality | Signs |
|---|---|
| 脉诊 | 876 |
| 舌诊 | 760 |
| 问诊 | 420 |
| 望诊 | 283 |
| 腹诊 | 148 |
| 目诊 | 89 |
| 闻诊 | 21 |

### Known issues and limitations（上游）

1. 单引擎抽取：MiniMax 交叉验证从未运行，所有边 agreement="single_engine"，不构成交叉验证结果。
2. 越医文化层仅覆盖 1802/2407 段（74.9%）、本草方剂层 1215/1464 段（83.0%），停在每帧 LLM token 上限而非内容耗尽；两层导出的任何计数都是下界，不可读作"文中没有"。
3. 部分续跑子任务在重试轮对目录/残句类段落追加了「无内容也须输出空数组 JSON」的指令（首轮提示词未改），否则模型返回中文说明而非 JSON。此为对既定提示词的偏离，已记录。
4. 医案层原始 pid 由 case_no 生成，而 case_no 在各门重新编号（660 则仅 369 个值），导致首轮 400 则中 230 个 pid 冲突、结果互相覆盖。已改为顺序键 hlc<seq>c<case_no>，并用 evidence 逐字匹配把首轮留存的 222 条无歧义归位（222/222 唯一命中）。
5. 7087 个节点没有任何已抽取关系（多为单次出现的症状/治法短语）；它们在星系图中被省略，但保留在 CSV/JSON/RDF 中。
6. 医案标题中只有 255/660 条含规范病名，其余命名的是证候（如"湿热阻中""气虚头汗"）——这是何廉臣的命题习惯，不是词表缺口。
7. 道地药材前缀（广/川/杭/建/云/西）与陈/真/原等品质标记刻意不做归并：广郁金与郁金、川贝与贝母在中药中并非同一味药。仅归并明确的炮制前缀（生/炒/炙/焦/飞/鲜等）。
8. 22370 条边仅有单次原文支持（占 98.5%），未经第二处文献印证。

## 二、本仓库附注（导入复核）

以下由 `tools/import_upstream.py` 在导入时实测重算，机器可读版见 `qc_audit.json`。

### 数据来源与出处深度

本仓库的 `data/` 与站点页面由上游随图谱交付的**自包含浏览器内嵌载荷**还原，而非上游完整 `shaopai_kg.json`：

- 每条关系 1 条原文与章节路径、`evidence_verbatim` 标记与支撑次数；**无段落编号**（`passage_id` 为空）。
- 每个节点最多 3 条章节路径与 1 条原文，另带出处总数 `n_provenance`。
- 本副本重建的 A-Box 为 369,226 三元组；段落编号与多条出处若补齐，三元组数还会增加。

完整出处以上游 `shaopai_kg.json` 为准，取得后以 `--kg` 重新导入即可。
载荷字段名在两代交付间有变（关系原文键 V6 用 `ev`、V5 用 `e`），导入脚本两者兼容。

### 复核结果

| 检查项 | 上游自报 | 本副本实测 |
|---|---|---|
| 节点 / 关系 | 18,151 / 22,700 | 18,151 / 22,700 |
| 类已有实例 / 关系已用 | 15/16 · 32/39 | 15/16 · 32/39 |
| 定义域 / 值域违例 | 0 | **0** |
| 悬空端点 | 0 | **0** |
| 自环 | 0 | **0**（V5 曾有 3 条 `subPatternOf` 自环，本版已消失） |
| 同主语、同宾语、同类型的重复关系 | — | **0**（V5 曾有 10 组，本版已消失） |
| 无原文句的关系 | — | 20（仅有章节路径） |
| 逐字原文证据 | 22,199 (97.8%) | 22,199 (97.8%) |
| 仅一处文献支撑 | 22,370 (98.5%) | 22,370 (98.5%) |
| 最大连通分量 | — | 9,471（另有 637 个大小 ≥ 2 的卫星分量） |
| 无关系节点 | 7,087 | 7,087（有边节点占 61.0%） |
| 病证与医案相连 | 416 | 416（有诊断的医案 625/657） |
| 病证 × 用药前 6 行 | 见上表 | 案数与共现药物逐行一致 |

**本版数据质量较 V5 明显改善**：自环、重复关系均归零，繁简异写已在上游归并。

### 与 V5 交付的差异（按节点 ID 比对）

| 项 | 数 |
|---|---|
| V5 节点仍在本版（ID 不变） | 16,103 |
| V5 节点在本版消失（并入其繁简/别名正体） | 88 |
| 本版新增节点 | 2,048 |
| V5 关系仍在本版 | 21,243 |
| V5 关系在本版消失 | 98（多为并入正体后的重复边） |
| 本版新增关系 | 1,457 |

消失的 88 个节点全部是被归并的异体，例如 `会稽`→`會稽`、`葉天士`→`叶天士`、`胃鈍`→`胃钝`；
医家别名并入正体后以 `aliases` 保留（何廉臣 ← 何炳元，张景岳 ← 张介宾 / 張介賓 / 張景岳），
故在浏览器中检索异体名仍能命中正体节点。

### 基数

`statedIn` / `belongsToChannel` / `subPatternOf` / `derivesFrom` / `institutionAtPlace`
在上游 1.0.0 本体中声明为 `0..1`，本次交付中分别有 11 / 3 / 2 / 14 / 2 个主语带多条出边
（例：一条学术观点同时载于多部著作；小柴胡汤同时「源自」5 部书）。
上游自报全部关系通过校验，故导入时按交付数据把五者记为 `0..*`；
仍为 `0..1` 的三条关系（`caseByPhysician` `diseaseSubtypeOf` 及其余）实测 0 例超限。

### 层、来源文献与引擎

浏览器载荷不逐条给出这三项，导入时补出：

- **layer 抽取层**：按关系类型的语义唯一归层（`LAYER_OF_REL`）。
  **V6 起改变了规则**——V5 曾以「章节根优先」推定，把《赵晴初医论》的 162 条学术观点关系
  归入越医文化层；V6 改为纯语义归层，学术观点一律归谱系层，越医文化层只保留
  籍贯 / 世家 / 机构三类关系。故本版层分布与 V5 不可直接对比。
- **corpus 来源文献**：按章节根映射到八种文献之一（`CORPUS_OF_ROOT`），
  「第 N 章…」归《越医文化》。全部 22,700 条关系均成功映射，无遗漏。
- **engine 抽取引擎**：按上游声明取层默认值（谱系层 `builtin-sonnet`，其余五层 `builtin-haiku`）；
  上一版已收录的 21,243 条关系沿用其记录在案的引擎，其中 331 条六经归属与子证候关系
  带上游 V2 的 `builtin-haiku+vocab`（词表辅助）标注。

| 层 | 关系数 | | 来源文献 | 关系数 |
|---|---|---|---|---|
| 医案层 case | 16,268 | | 《何廉臣医案》 | 16,342 |
| 谱系层 lineage | 2,307 | | 《浙派中医丛书·绍派伤寒》 | 4,332 |
| 证候层 pattern | 2,203 | | 《俞根初临证经验集要》 | 1,156 |
| 诊法层 diagnostic | 1,364 | | 《越中名医传》 | 310 |
| 越医文化层 culture | 339 | | 《绍派伤寒史料图片研究》 | 227 |
| 本草方剂层 materia | 219 | | 《赵晴初医论》 | 162 |
| | | | 《越医文化》 | 87 |
| | | | 《越醫雜詠》 | 84 |

两个维度互不替代：`layer` 答「属于哪一层知识」，`corpus` 答「出自哪部书」。

### 两部新书的贡献

| | 《俞根初临证经验集要》 | 《绍派伤寒史料图片研究》 |
|---|---|---|
| 关系 | 1,156 | 227 |
| 主要关系类型 | 方剂主治 525 · 征象提示 262 · 治法用方 181 · 主张 85 · 源自 49 | 籍贯 53 · 撰写 38 · 载于 30 · 机构所在 24 · 师承 17 |
| 独有节点 | 1,556（证候 371 · 诊法征象 316 · 学术观点 266 · 方剂 249 · 治法 139 · 中药 127） | 488（学术观点 85 · 医家 84 · 病证 80 · 方剂 76 · 著作 58 · 地域 51 · 机构 50） |

前者把全图「方剂主治」由 242 条推到 767 条、「治法用方」由 46 条推到 227 条，
是本版新增「方治层」一节的依据；后者补的是医家、医籍与近代医事机构。

### 其他观察

1. 症状与诊法征象两类有 **439 个同名节点**并存（胸痛、腹痛、舌干……），是医案层与诊法层各自命名所致。
2. **繁简归并只作用于节点名称**：机构 `kind` 属性仍有 學校 10 / 学校 13、醫社 2 / 医社 23、
   藥鋪 3 / 药铺 6 等两写，尚未归并。
3. 证候性质 `nature` 有「湿|热」与「湿热」两种写法（48 / 42），主页统计时合并显示，数据未改。
4. 中药节点上的 `dose` / `unit` / `processing` 是原文所见的抽取值（如 滑石 4.0 钱 · 飞），非药典常规剂量。
5. 方剂的**逐味配伍**未随本次交付提供：1,280 首方剂中 517 首有边，但「药物组成」仅 41 条，
   `ingredientRole`（君臣佐使）、`hasDosage`、`addHerbIf`、`removeHerbIf` 四条关系仍无实例。
6. V3 / V4 由本仓库确定性解析器产出的本地层（366 节点 / 567 关系，含 41 首方剂的完整配伍与
   《通俗伤寒论》病证分类树）不在上游交付之内，自 V5 起未并入；见 README「版本沿革」。
