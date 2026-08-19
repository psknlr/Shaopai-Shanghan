# 绍派伤寒 Knowledge Graph — QC Audit

**Built by** 医哲未来人工智能研究院 (IMPFAI) · https://impfai.github.io/

**Source** 《浙派中医丛书》专题系列·绍派伤寒, ed. 沈钦荣 (2021)。
语料自原书 Word 文档复原：1,586 段落、203,045 字（上游审计口径 205,712，差 1.3%），见 `corpus_shaopai.json`。

## 状态：四层已完成三层

| 层 | 状态 | 抽取方式 |
|---|---|---|
| 谱系层（医家·著作·学术观点） | **完成** | 单模型 LLM 抽取 |
| 诊法层（舌·脉·腹·目诊） | **完成** | 单模型 LLM 抽取 |
| 本草方剂层（方剂·中药·治法·医案） | **完成** | **确定性解析器**（可复现） |
| 证候层（病证·证候·症状） | 未运行 | — |

## 图谱现状

- **4,205 节点** — 1524 Doctrine · 1311 DiagnosticSign · 542 Pattern · 356 Work · 218 Physician · 188 Herb · 41 Formula · 15 CaseRecord · 10 TreatmentPrinciple
- **3,034 关系** — proposes 1142 · signIndicates 605 · subPatternOf 272 · hasIngredient 262 · authored 223 · statedIn 135 · influencedBy 81 · editedRevised 75 · belongsToChannel 59 · ingredientRole 41 · signExcludes 35 · derivesFrom 27 · addHerbIf 22 · studiedUnder 18 · caseByPhysician 15 · principleRealizedBy 10 · removeHerbIf 7 · formulaTreats 5
- **连通性** 70.2% 的节点至少有一条边
- **最大连通分量 2,355 节点**

## 已解决：两层不连通问题

上一版记录的结构性缺口——谱系层（1,444 节点）与诊法层（663 节点）互不相连——**已经消解**。

本草方剂层同时连向两侧：`derivesFrom`（方剂→著作，27 条）落在谱系层，
`formulaTreats`（方剂→证候，5 条）落在诊法层，`caseByPhysician`（医案→医家，15 条）
再补一道。最大连通分量由 **1,444 增至 2,355** 节点，医家、著作、学说、征象、证候、
治法、方剂、药物首次汇入同一张网。

## 完整性

| 检查项 | 结果 |
|---|---|
| 本体定义域/值域违例 | **0** / 3,034 |
| 悬空端点 | 0 |
| 带出处的关系 | 3,034 / 3,034 |
| 逐字原文证据 | 2941/3034 (96.9%) |
| 仅一处文献支撑 | 2938/3034 (96.8%) |

## 本草方剂层详情

**引擎** `rule-parser-v1 (deterministic, not an LLM)`。与前两层不同，本层不由语言模型抽取，而是对原书「方剂选录」
「医案选按」等结构规整的章节做确定性解析：**同一输入必得同一图谱**，可逐行复核、可复现。

- 方剂 41 · 中药 188 · 治法 10 · 医案 15
- 药物组成 262 条（带原剂量与炮制）· 君臣佐使 41 条 · 随症加减 29 条
- **抽样校验**：蒿芩清胆汤 8/8 ingredient recall vs pilot_validation.json gold set——与上游 `pilot_validation.json` 的金标准完全一致。

### 本层已知限制

1. Herb surface forms are NOT unified: 生枳壳 / 枳壳, 炙甘草 / 甘草 are separate nodes. Prefix stripping was rejected because it collapses 陈皮 / 青皮 / 新会皮 into 皮.
2. Only formulas whose composition is printed in the book are minted as Formula nodes; formulas merely cited by name (麻黄汤, 白虎汤 …) are not, to avoid isolated nodes.
3. Dosage class stays at 0 instances by design: dose, processing and 君臣佐使 are carried on the hasIngredient / ingredientRole relations instead of as separate nodes.
4. formulaTreats links rest on string containment between a formula indication and an existing Pattern name; only 5 matched.
5. Disease and Symptom classes remain empty; the pattern layer has not run.
6. Passage ids for this layer use a b##### scheme from a fresh segmentation of the source .doc and do NOT align with the p##### ids of the lineage / diagnostic layers.

## 沿袭自前两层的限制

1. **谱系层与诊法层全部关系为单模型抽取**，`agreement` 为 `single_engine`，交叉验证未运行。
   本草层为确定性解析，`agreement` 为 `deterministic_parse`。
2. 约 3% 的关系无逐字原文证据，标注 `evidence_verbatim=false`，请回溯原书核验。
3. 796 项诊法征象未抽出「提示何种证候」的断言，在图谱中呈孤点。
4. 证候的六经与性质由**名称**经词表匹配推得——某证候未标六经，只说明其名称未含六经字样。
5. 356 部著作中有 11 条实为参考文献中的期刊论文题名。
6. 籍贯粒度不一（山阴 / 绍兴），张畹香记为「江南」。

## 查询提示

Turtle 中所有中文字面量带 `@zh` 语言标记，SPARQL 需写 `"腹诊"@zh`，
写成 `"腹诊"` 会静默返回空结果。
