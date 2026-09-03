# 绍派伤寒 · 越医知识图谱 — QC Audit

**Built by** 医哲未来人工智能研究院 (IMPFAI) · https://impfai.github.io/

> 第一部分为上游随图谱交付的质检报告，原文照录；第二部分「本仓库附注」记录导入本站时的实测复核与差异。

## 一、上游质检报告

**Sources**
- 《浙派中医丛书》专题系列·绍派伤寒, 沈钦荣主编 (2021)
- 《越医文化》十章 + 目录 + 后记
- 《何廉臣医案》660 则
- 《越中名医传》下篇 + 越中名医传补
- 《越醫雜詠》
- 《赵晴初医论》

### Graph

| | |
|---|---|
| Nodes | **16,191** |
| Edges | **21,351** |
| Ontology classes defined / populated | 16 / 15 |
| Object properties defined / used | 39 / 32 |
| Ontology violations | **0** |
| Evidence verbatim | 20907/21351 (97.9%) |
| RDF triples (T-Box + A-Box) | 416 + 331,361; union = 331,774 (see note) |

The two Turtle files sum to 331,777 triples but their union is 331,774: the 3 FOAF triples declaring the publisher organisation are asserted in both files so each stands alone, and deduplicate when loaded together. Not an arithmetic error.

`Dosage` is the one defined-but-unpopulated class: dose and unit are carried as
attributes on `Herb` (parsed to a numeric amount, including the 钱半 = 1.5 钱 idiom)
rather than reified as separate nodes.

### Extraction coverage

| Layer | Extracted / routed | Coverage |
|---|---|---|
| lineage | 407 / 407 | 100.0% |
| diagnostic | 281 / 284 | 98.9% |
| pattern | 776 / 793 | 97.9% |
| materia | 550 / 556 | 98.9% |
| case | 657 / 660 | 99.5% |
| culture | 1,475 / 1,874 | 78.7% |

Coverage is *passages extracted* over *passages routed to that layer*. **Every shortfall is a
per-frame LLM token-ceiling stop, not an exhausted corpus.** Counts drawn from a partial layer —
above all 越医文化 at 78.7% — are lower bounds and must never be read as
"absent from the text".

### Node classes

| Class | 中文 | Count |
|---|---|---|
| DiagnosticSign | 诊法征象 | 2,281 |
| Symptom | 症状 | 2,217 |
| Doctrine | 学术观点 | 2,172 |
| TreatmentPrinciple | 治法 | 1,801 |
| Pattern | 证候 | 1,674 |
| Disease | 病证 | 1,458 |
| Herb | 中药 | 1,254 |
| Formula | 方剂 | 962 |
| CaseRecord | 医案 | 657 |
| Work | 著作 | 647 |
| Physician | 医家 | 599 |
| Place | 地域 | 264 |
| Institution | 机构团体 | 90 |
| HerbProperty | 药性 | 80 |
| MedicalFamily | 医学世家 | 35 |

### Relations (top 18 of 32 used)

| Property | 中文 | Count |
|---|---|---|
| `caseUsesHerb` | 医案用药 | 8,486 |
| `caseShowsSymptom` | 医案见症 | 3,233 |
| `caseShowsSign` | 医案见象 | 1,875 |
| `proposes` | 主张 | 1,182 |
| `caseAppliesPrinciple` | 医案治法 | 1,109 |
| `caseDiagnosedAs` | 医案诊断 | 702 |
| `signIndicates` | 征象提示 | 607 |
| `caseShowsPattern` | 医案辨证 | 434 |
| `caseUsesFormula` | 医案用方 | 429 |
| `treatedByPrinciple` | 治法对应 | 428 |
| `authored` | 撰写 | 403 |
| `manifestsAs` | 表现为 | 370 |
| `patternOfDisease` | 病之证候 | 360 |
| `subPatternOf` | 子证候 | 299 |
| `formulaTreats` | 方剂主治 | 242 |
| `statedIn` | 载于 | 222 |
| `belongsToChannel` | 属于六经 | 161 |
| `physicianOfPlace` | 籍贯 | 152 |

### Disease layer

1,458 Disease nodes; 416 of them are linked to at least one
of the 657 case records from 《何廉臣医案》.

Only **255/660 (38.6%)** of case titles contain a canonical 病名. The
remainder name a *pattern* (湿热阻中, 气虚头汗, 肝阳犯胃) — that is 何廉臣's titling convention, not a
lexicon gap, and those titles become `Pattern` nodes rather than being forced into `Disease`.

| Disease | Cases | Signature herbs (co-occurrence across its cases) |
|---|---|---|
| 咳嗽 | 37 | 瓜蒌仁、光杏仁、冬桑叶、新会皮、竹茹、前胡 |
| 湿热 | 25 | 滑石、竹叶、瓜蒌仁、广郁金、枳实、佩兰叶 |
| 湿温 | 19 | 滑石、山栀、竹叶、苏薄荷、苏叶梗、青连翘 |
| 湿热兼风 | 13 | 滑石、佩兰叶、广郁金、西茵陈、苏薄荷、竹叶 |
| 湿热夹食 | 13 | 滑石、竹叶、莱菔子、佛手片、打鸡金、打延胡 |
| 湿热阻中 | 11 | 滑石、杜藿梗、佩兰叶、佛手片、广郁金、竹叶 |
| 疟 | 11 | 滑石、山栀、竹叶、草果仁、桑枝、苏叶梗 |
| 暑湿夹食 | 11 | 竹叶、山栀、桑枝、枳壳、青蒿、佩兰叶 |
| 暑湿兼风 | 10 | 滑石、广郁金、苏叶梗、冬桑叶、滁菊花、葱白 |
| 肝风 | 8 | 明天麻、石决明、竹茹、滁菊花、广郁金、冬桑叶 |
| 暑湿 | 7 | 竹叶、苏薄荷、滑石、冬桑叶、山栀、青蒿 |
| 肝阳犯胃 | 7 | 广郁金、竹茹、石决明、香附、姜炒川连、甘松 |

These pairings are recovered from the text, not asserted from doctrine, and they land where a reader
of the school would expect: 疟 with 草果仁, 肝风 with 明天麻 and 石决明, 湿温 with 滑石 and 山栀.

### Diagnostic modalities

| Modality | Signs |
|---|---|
| 脉诊 | 747 |
| 舌诊 | 617 |
| 问诊 | 418 |
| 望诊 | 279 |
| 腹诊 | 116 |
| 目诊 | 83 |
| 闻诊 | 21 |

### Integrity

- **0 domain/range/cardinality violations** across all 21,351 edges.
- 0 self-loops, 0 dangling endpoints.
- 20907/21351 (97.9%) of edges carry an evidence span that is a verbatim substring of its source
  passage; the 444 that are not are flagged `evidence_verbatim=false` in every export.
- 9,836 nodes carry at least one relation; 6,355 do not.

### Known issues and limitations

1. 单引擎抽取：MiniMax 交叉验证从未运行（凭据始终未通过 Customize → Credentials 提供），故所有边 agreement="single_engine"，不构成交叉验证结果。
2. 越医文化层仅覆盖 1475/1874 段（78.7%），停在每帧 LLM token 上限而非内容耗尽；该层导出的任何计数都是下界，不可读作"文中没有"。
3. 部分续跑子任务在重试轮对目录/残句类段落追加了「无内容也须输出空数组 JSON」的指令（首轮提示词未改），否则模型返回中文说明而非 JSON。此为对既定提示词的偏离，已记录。
4. 医案层原始 pid 由 case_no 生成，而 case_no 在各门重新编号（660 则仅 369 个值），导致首轮 400 则中 230 个 pid 冲突、结果互相覆盖。已改为顺序键 hlc<seq>c<case_no>，并用 evidence 逐字匹配把首轮留存的 222 条无歧义归位（222/222 唯一命中）。
5. 6355 个节点没有任何已抽取关系（多为单次出现的症状/治法短语）；它们在星系图中被省略，但保留在 CSV/JSON/RDF 中。
6. 医案标题中只有 255/660 条含规范病名，其余命名的是证候（如"湿热阻中""气虚头汗"）——这是何廉臣的命题习惯，不是词表缺口。
7. 道地药材前缀（广/川/杭/建/云/西）与陈/真/原等品质标记刻意不做归并：广郁金与郁金、川贝与贝母在中药中并非同一味药。仅归并明确的炮制前缀（生/炒/炙/焦/飞/鲜等）。
8. 21092 条边仅有单次原文支持（占 98.8%），未经第二处文献印证。

### Verification queries

`example_queries.cypher` ships both Cypher and SPARQL forms. Note the SPARQL gotcha documented there:
every Chinese literal in the Turtle files carries an `@zh` language tag, so a plain `"腹诊"` will not
match — write `"腹诊"@zh`.

## 二、本仓库附注（导入复核）

以下由 `tools/import_upstream.py` 在导入时实测重算，机器可读版见 `qc_audit.json`。

### 数据来源与出处深度

本仓库的 `data/` 与站点页面由上游随图谱交付的**自包含浏览器内嵌载荷**还原，而非上游完整 `shaopai_kg.json`：

- 每条关系 1 条原文与章节路径、`evidence_verbatim` 标记与支撑次数；**无段落编号**（`passage_id` 为空）。
- 每个节点最多 3 条章节路径与 1 条原文，另带出处总数 `n_provenance`。
- 上游自报 A-Box 331,361 三元组；本副本重建的 A-Box 为 322,924 三元组，差额即段落编号与多条出处所致。

完整出处以上游 `shaopai_kg.json` 为准，取得后以 `--kg` 重新导入即可。

### 复核结果

| 检查项 | 上游自报 | 本副本实测 |
|---|---|---|
| 节点 / 关系 | 16,191 / 21,351 | 16,191 / 21,351 |
| 类已有实例 / 关系已用 | 15/16 · 32/39 | 15/16 · 32/39 |
| 定义域 / 值域违例 | 0 | **0** |
| 悬空端点 | 0 | **0** |
| 自环 | 0 | **3**（`subPatternOf`：虚证、实证、热证各指向自身） |
| 同主语、同宾语、同类型的重复关系 | — | **10 组**（多为同一断言在两处章节各被抽出一次，如 目色→病之存亡） |
| 无原文句的关系 | — | 20（仅有章节路径） |
| 逐字原文证据 | 20,907 (97.9%) | 20,907 (97.9%) |
| 仅一处文献支撑 | 21,092 (98.8%) | 21,092 (98.8%) |
| 最大连通分量 | 8,488 | 8,488（另有 501 个大小 ≥ 2 的卫星分量） |
| 无关系节点 | 6,355 | 6,355 |
| 病证与医案相连 | 416 | 416（有诊断的医案 625/657） |
| 病证 × 用药前 12 行 | 见上表 | 案数逐行一致，共现药物前列一致；末位同频药物的取舍因排序规则而异（如 咳嗽 第六位 前胡 / 紫菀） |

自环与重复关系如实保留，未作修改；站点浏览器绘制时忽略自环。

### 基数

`statedIn` / `belongsToChannel` / `subPatternOf` 在上游 1.0.0 本体中声明为 `0..1`，
本次交付中分别有 10 / 3 / 2 个主语带多条出边（例：一条学术观点同时载于多部著作）。
上游自报全部关系通过校验，故导入时按交付数据把三者记为 `0..*`；
仍为 `0..1` 的四条关系（`caseByPhysician` `derivesFrom` `diseaseSubtypeOf` `institutionAtPlace`）实测 0 例超限。

### 层与引擎

浏览器载荷不逐条给出抽取层与引擎，导入时按上游 meta 的层定义推定：
章节根为《何廉臣医案》者归医案层；章节根不属《绍派伤寒》专著者归越医文化层；
专著语料按关系类型归谱系 / 诊法 / 证候 / 本草四层。引擎按上游声明取层默认值
（谱系层 `builtin-sonnet`，其余五层 `builtin-haiku`）；上一版已收录的 2,645 条关系沿用其记录在案的引擎，
其中 331 条六经归属与子证候关系带上游 V2 的 `builtin-haiku+vocab`（词表辅助）标注。

| 层 | 关系数 |
|---|---|
| 医案层 case | 16,343 |
| 谱系层 lineage | 1,674 |
| 证候层 pattern | 1,445 |
| 诊法层 diagnostic | 1,100 |
| 越医文化层 culture | 663 |
| 本草方剂层 materia | 126 |

### 其他观察

1. 症状与诊法征象两类有 **430 个同名节点**并存（胸痛、腹痛、舌干……），是医案层与诊法层各自命名所致。
2. 《越中名医传》《越醫雜詠》为繁体底本：會稽 / 会稽、山陰 / 山阴、紹興 / 绍兴 各自成地域节点，
   機構類型 學校 / 学校、醫社 / 医社 亦然，尚未归并。
3. 证候性质 `nature` 有「湿|热」与「湿热」两种写法（48 / 42），主页统计时合并显示，数据未改。
4. 中药节点上的 `dose` / `unit` / `processing` 是原文所见的抽取值（如 滑石 4.0 钱 · 飞），非药典常规剂量。
5. 上游 V2 的 3,951 个节点与 2,645 条关系全部按原 ID 出现在本次交付中；
   上一版由本仓库确定性解析器产出的本地层（366 节点 / 567 关系）不在交付之内，见 README「版本沿革」。
