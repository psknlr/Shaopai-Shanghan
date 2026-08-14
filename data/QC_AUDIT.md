# 绍派伤寒 Knowledge Graph — QC Audit

**Built by** 医哲未来人工智能研究院 (IMPFAI) · https://impfai.github.io/

**Source** 《浙派中医丛书》专题系列·绍派伤寒, ed. 沈钦荣 (2021) — 205,712 chars across 1,243 retained passages, 11 physicians.

205712 chars = retained extractable passages (audited figure). 213357 = all non-empty paragraphs incl. TOC/front matter; 209201 = body after hard-wrap repair, before heading/fragment removal.

## Status: two of four layers complete

| Layer | Status | Passages |
|---|---|---|
| Lineage (医家·著作·学术观点) | **complete** | 407 |
| Diagnostics (舌·脉·腹·目诊) | **complete** | 281 / 284 |
| Pattern (病证·证候·症状·治法) | not run | 786 |
| Materia medica (方剂·中药·加减·医案) | not run | 555 |

frame LLM token ceiling (2.0M) reached again after the diagnostic layer; MiniMax cross-validation still unavailable because the control-plane kernel cannot start (/usr/bin/python3 is a broken Xcode CLT stub), so no credential access.

**Cross-model validation still has not run.** Every edge carries `agreement="single_engine"`
(or `vocabulary_bridge` for the 18 controlled-vocabulary axis links). The MiniMax key was pasted
into the chat twice and was never used; it should be rotated and stored under
Customize → Credentials instead.

## Graph as built

- **3,951 nodes** — 218 Physician · 356 Work · 1,524 Doctrine · 1,311 DiagnosticSign · 542 Pattern
- **2,645 edges** — proposes 1,142 · signIndicates 605 · subPatternOf 272 · authored 223 · statedIn 135 · influencedBy 81 · editedRevised 75 · belongsToChannel 59 · signExcludes 35 · studiedUnder 18
- **Connectivity** 68.3% of nodes carry at least one edge
- **RDF** 314 T-Box + 49,966 A-Box = 50,277 triples

The graph is a **binary system**: the lineage layer (1,444-node component) and the diagnostics
layer (663-node component) are **not connected to each other**. Nothing in the extracted text
links a 诊法征象 or 证候 back to the physician who described it, because `signIndicates` runs
sign→pattern and no property in the ontology bridges a clinical finding to its author. This is a
genuine gap, not a layout artifact — closing it needs either a `describedBy` relation added to
the ontology or the pattern layer, which will carry physician-attributed 治法 statements.

## Integrity

| Check | Result |
|---|---|
| Ontology domain/range violations | **0** / 2,645 |
| Self-loops | 3 |
| Dangling endpoints | 0 |
| Edges carrying provenance | 2645/2645 |
| Evidence verbatim in source | 2552/2645 (96.5%) |
| Edges on a single mention | 2549/2645 (96.4%) |

## Diagnostics layer detail

Signs by modality — the school's signature methods are well represented:

| Modality | Signs |
|---|---|
| 问诊 | 412 |
| 舌诊 | 265 |
| 望诊 | 260 |
| 脉诊 | 168 |
| 腹诊 | 110 |
| 目诊 | 75 |
| 闻诊 | 21 |

- **296/542** patterns attach to a canonical 六经/三焦/性质 axis via
  `belongsToChannel` or `subPatternOf`. The remainder are free-text pattern names with no
  vocabulary anchor.
- **796 of 1,311 signs carry no relation** — they were named in a passage but
  the model extracted no sign→pattern assertion for them.
- **1,149 signs are single-mention.** Classical texts phrase findings variably
  (虚里跃动应衣, 三脘痞硬, 高低凹凸如畎亩状), so most surface once. These are real findings, not
  extraction noise, but they cannot be corroborated within this corpus.

## Known issues

1. **11 Work nodes are journal-article titles** from 参考文献 sections. Fix: exclude those chapter paths.
2. **96.5% of edges have verbatim evidence** — the rest are flagged `evidence_verbatim=false` in every export.
3. **Native-place granularity variants** (山阴 vs 绍兴). One genuine outlier: 张畹香 as 江南.
4. **The two layers do not interconnect** (see above).
5. **Pattern nodes were minted from diagnostic relations**, not from a dedicated pattern extraction.
   Their attributes are inferred from the pattern *name* by vocabulary matching, so a pattern whose
   name omits its channel carries no channel — absence of an attribute is not evidence of absence
   in the source.
6. **All edges are single-engine.** No cross-validation exists.

## Pilot validation

{
 "passage": "p02121",
 "gold_ingredients": [
  "青蒿脑",
  "淡竹茹",
  "仙半夏",
  "赤茯苓",
  "青子芩",
  "生枳壳",
  "陈广皮",
  "碧玉散"
 ],
 "verified": {
  "model": "claude-haiku-4-5-20251001",
  "ingredient_recall": "8/8",
  "attribution": "俞根初 / 《通俗伤寒论》",
  "non_verbatim_evidence": 0,
  "output_tokens": 2047,
  "stop_reason": "end_turn"
 },
 "not_measured": {
  "model": "claude-sonnet-5",
  "outcome": "response truncated at the 3000-token cap and did not parse; no valid recall score",
  "note": "the 0/8 printed for this arm is a truncation artifact, not a measured recall. A re-run at a larger cap was attempted but the frame token ceiling was exhausted, so no reasoning-model score exists for this session."
 },
 "decision": "haiku-class model selected for all three clinical layers on the strength of its own verified pilot score, not on a comparison against the reasoning model."
}

## To complete the build

Fix the interpreter path (`[conda].operon_python_bin` → `/Users/dao/.claude-science/conda/envs/python/bin/python3`,
or `xcode-select --install`). That restores sub-agent delegation, so the two remaining layers can run
with independent token budgets, and restores credential access for the MiniMax cross-validation pass.

## Querying note

All Chinese literals in the Turtle files carry an `@zh` language tag. SPARQL filters must write
`"腹诊"@zh`, not `"腹诊"` — a plain literal silently returns zero rows. See the footer of
`example_queries.cypher`.
