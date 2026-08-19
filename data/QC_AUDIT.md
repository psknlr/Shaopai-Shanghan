# 绍派伤寒 Knowledge Graph — QC Audit

**Built by** 医哲未来人工智能研究院 (IMPFAI) · https://impfai.github.io/

**Source** 《浙派中医丛书》专题系列·绍派伤寒, ed. 沈钦荣 (2021)。
语料自原书 Word 文档复原：1,586 段落、203,045 字（上游审计口径 205,712，差 1.3%），
见 `corpus_shaopai.json`。

## 状态：四层全备

| 层 | 状态 | 抽取方式 |
|---|---|---|
| 谱系层（医家·著作·学术观点） | **完成** | 单模型 LLM |
| 诊法层（舌·脉·腹·目诊） | **完成** | 单模型 LLM |
| 本草方剂层（方剂·中药·医案） | **完成** | **确定性解析器** |
| 证候层（病证·证候·治法） | **完成** | **确定性解析器** |

本体 1.1.0：13 类 / 27 关系，其中 **10 类已有实例**。

### 本体扩展

1.0.0 → 1.1.0: added subDiseaseOf (Disease→Disease, 0..1). The book enumerates 伤寒本证/兼证/夹证/坏证/复证 and their members, but 1.0.0 had no Disease-to-Disease relation, so 51 diseases could only be isolated nodes. Nothing else was changed.

### 三个仍为空的类

| 类 | 原因 |
|---|---|
| Symptom 症状 | deliberate — 17/18 common symptom candidates are already DiagnosticSign nodes (672 carry modality 问诊/望诊). A parallel class would duplicate nodes and split the graph. |
| Dosage 剂量炮制 | deliberate — dose, processing and 君臣佐使 ride on hasIngredient / ingredientRole instead of separate nodes. |
| HerbProperty 药性 | not extracted — the book states herb properties in prose, not in a tabular form the parser can read without inference. |

## 图谱现状

- **4,317 节点** — 1524 Doctrine · 1311 DiagnosticSign · 567 Pattern · 356 Work · 218 Physician · 188 Herb · 68 Disease · 41 Formula · 29 TreatmentPrinciple · 15 CaseRecord
- **3,144 关系** — proposes 1142 · signIndicates 605 · subPatternOf 272 · hasIngredient 262 · authored 223 · statedIn 135 · influencedBy 81 · editedRevised 75 · subDiseaseOf 61 · belongsToChannel 59 · ingredientRole 41 · signExcludes 35 · derivesFrom 27 · treatedByPrinciple 27 · addHerbIf 22 · patternOfDisease 20 · studiedUnder 18 · caseByPhysician 15 · principleRealizedBy 10 · removeHerbIf 7 · formulaTreats 7
- **连通性** 71.0% 的节点至少有一条边
- **最大连通分量 2,391 节点**（十类俱全），另有一株 57 节点的伤寒病证树独立成群

## 完整性

| 检查项 | 结果 |
|---|---|
| 本体定义域/值域违例 | **0** / 3,144 |
| 悬空端点 | 0 |
| 带出处的关系 | 3,144 / 3,144 |
| 逐字原文证据 | 3051/3144 (97.0%) |
| 仅一处文献支撑 | 3048/3144 (96.9%) |

## 本草方剂层

**引擎** `rule-parser-v1 (deterministic, not an LLM)`。方剂 41 · 中药 188 · 医案 15；
药物组成 262 条（带原剂量与炮制）· 君臣佐使 41 条 ·
随症加减 29 条。

**抽样校验**：蒿芩清胆汤 8/8 ingredient recall vs pilot_validation.json gold set——与上游 `pilot_validation.json` 的金标准完全一致。

### 限制

1. Herb surface forms are NOT unified: 生枳壳 / 枳壳, 炙甘草 / 甘草 are separate nodes. Prefix stripping was rejected because it collapses 陈皮 / 青皮 / 新会皮 into 皮.
2. Only formulas whose composition is printed in the book are minted as Formula nodes; formulas merely cited by name (麻黄汤, 白虎汤 …) are not, to avoid isolated nodes.
3. Dosage class stays at 0 instances by design: dose, processing and 君臣佐使 are carried on the hasIngredient / ingredientRole relations instead of as separate nodes.
4. formulaTreats links rest on string containment between a formula indication and an existing Pattern name; only 5 matched.
5. Disease and Symptom classes remain empty; the pattern layer has not run.
6. Passage ids for this layer use a b##### scheme from a fresh segmentation of the source .doc and do NOT align with the p##### ids of the lineage / diagnostic layers.

## 证候层

**引擎** `rule-parser-v1 (deterministic, not an LLM)`。病证 68 · 新增证候 25 · 治法 29；
关系 subDiseaseOf 61 · treatedByPrinciple 27 · patternOfDisease 20 · formulaTreats 7。

**分类完整性校验**：Every taxonomy member was matched verbatim in its source passage and the count checked against the number the book itself states: 本证 5/5, 兼证 21/21, 夹证 16/16, 坏证 4/4, 复证 5/5.

### 限制

1. The 57-node 伤寒 disease subtree is a separate component. No ontology property links a disease to the physician who described it or to a formula that treats it, so it cannot join the giant component.
2. Treatment principles were harvested from a handful of passages that state them in an「X宜Y」form; principles discussed only in prose are not captured.
3. patternOfDisease edges for the 六淫 sub-patterns rest on the book grouping them under a 「X病药」 section heading, not on an explicit sentence asserting membership.
4. The formula names cited in 何廉臣 down-method classification (紫草承气汤, 局方凉膈散 …) print no composition, so no principleRealizedBy edges were created for them.

## 沿袭自前两层的限制

1. **谱系层与诊法层全部关系为单模型抽取**，`agreement` 为 `single_engine`，交叉验证未运行。
   后两层为确定性解析，`agreement` 为 `deterministic_parse`。
2. 约 3% 的关系无逐字原文证据，标注 `evidence_verbatim=false`，请回溯原书核验。
3. 796 项诊法征象未抽出「提示何种证候」的断言，在图谱中呈孤点。
4. 证候的六经与性质由**名称**经词表匹配推得——某证候未标六经，只说明其名称未含六经字样。
5. 356 部著作中有 11 条实为参考文献中的期刊论文题名。
6. 籍贯粒度不一（山阴 / 绍兴），张畹香记为「江南」。

## 段落编号的两套体系

谱系层与诊法层沿用上游的 `p#####`；本草方剂层与证候层用 `b#####`，来自本次对原书 .doc
的重新切分。**两套不同源，不可直接对齐**；核验一律以逐字原文与章节路径为准。

## 查询提示

Turtle 中所有中文字面量带 `@zh` 语言标记，SPARQL 需写 `"腹诊"@zh`，
写成 `"腹诊"` 会静默返回空结果。
