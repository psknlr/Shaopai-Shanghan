**Table 1 | Source works of the corpus and the relations extracted from each.**

| Source work | English title | Genre | Responsibility* | Script | Passages | Characters† | Relations |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 何廉臣医案 | Case records of He Lianchen | Case records | He Lianchen | Simplified | 1,324 | 215,750 | 16,342 |
| 浙派中医丛书·绍派伤寒 ‡ | Shaopai Shanghan (Zhejiang School of Chinese Medicine series) | School monograph | Shen Qinrong (ed.), 2021 | Simplified | 1,586 | 205,452 | 4,330 |
| 俞根初临证经验集要 | Essentials of Yu Genchu's clinical experience | Monograph on the founder | Shen Qinrong (comp.) | Simplified | 1,094 | 163,641 | 1,156 |
| 越医文化 | Medical culture of Yue (10 chapters, contents and postscript) | Regional medical history | – | Simplified | 554 | 77,495 | 87 |
| 赵晴初医论 | Medical essays of Zhao Qingchu | Medical essays | Zhao Qingchu | Simplified | 396 | 74,914 | 162 |
| 越中名医传 | Biographies of eminent physicians of Yuezhong (part 2 and supplement) | Biographies | – | Traditional | 356 | 74,775 | 310 |
| 绍派伤寒史料图片研究 | Pictorial historical sources of the Shaopai school | Illustrated catalogue | Tao Jianhua (chief reviewer); Shen Qinrong, Lin Yibing (eds.) | Simplified | 533 | 36,526 | 227 |
| 越醫雜詠 | Miscellaneous verses on Yue medicine | Verse | – | Traditional | 138 | 7,462 | 84 |
| **Total §** | 8 works |  |  |  | 5,981 | 856,015 | 22,698 |

* As recorded in the delivered sources; –, not recorded.  
† Unicode code points of passage text, including punctuation.  
‡ 浙派中医丛书·绍派伤寒 (Shaopai Shanghan): passages follow this release's re-segmentation of the original book (b-numbered); its relations cite the upstream p-numbered segmentation, which could not be aligned (Technical Validation).  
§ A ninth source, 131 outpatient case records (2022–2026), was delivered but is withheld from release pending consent review; its 5,682 relations and 1,234 dependent entities are excluded from all counts.  

**Table 2 | Entity classes of ontology v1.2.0 and their instances.**

| Class | Chinese label | Declared attributes* | Entities | With relations | Without relations |
| --- | --- | --- | ---: | ---: | ---: |
| Diagnostic sign | 诊法征象 | name_zh, modality, descriptor | 2,597 | 1,501 | 1,096 |
| Doctrine | 学术观点 | statement_zh, topic, novelty | 2,522 | 1,477 | 1,045 |
| Symptom | 症状 | name_zh, body_region, severity, timing | 2,216 | 1,468 | 748 |
| Pattern | 证候 | name_zh, channel, triple_burner, nature, aliases | 2,042 | 1,693 | 349 |
| Treatment principle | 治法 | name_zh, action_type | 1,940 | 1,137 | 803 |
| Disease | 病证 | name_zh, category, aliases | 1,524 | 562 | 962 |
| Herb | 中药 | name_zh, aliases, part_used, is_fresh | 1,379 | 807 | 572 |
| Formula | 方剂 | name_zh, source_work, attributed_to, preparation, aliases | 1,280 | 517 | 763 |
| Work | 著作 | title_zh, author, year, edition, is_extant | 758 | 509 | 249 |
| Physician | 医家 | name_zh, courtesy_name, birth_year, death_year, native_place, dynasty, role_in_school | 671 | 486 | 185 |
| Case record | 医案 | patient_desc, presentation, outcome, physician | 657 | 657 | 0 |
| Place | 地域 | name_zh, modern_name, region | 309 | 87 | 222 |
| Institution | 机构团体 | name_zh, kind, founded_year, place, founder | 137 | 57 | 80 |
| Herb property | 药性 | flavor, temperature, channel_tropism | 80 | 73 | 7 |
| Medical family | 医学世家 | name_zh, specialty, place, generations | 37 | 31 | 6 |
| Examination † | 辅助检查 | name_zh, modality, finding | 0 | 0 | 0 |
| Procedure † | 外治操作 | name_zh, kind, site | 0 | 0 | 0 |
| Western diagnosis † | 西医诊断 | name_zh, icd_hint, system | 0 | 0 | 0 |
| Western drug † | 西药 | name_zh, dose, route, frequency | 0 | 0 | 0 |
| Dosage ‡ | 剂量炮制 | amount, unit, processing, admin_note | 0 | 0 | 0 |
| **Total** |  | 15 of 20 classes populated | 18,149 | 11,062 | 7,087 |

* Attribute names as declared in the ontology specification; values are extracted text, not normalized codes.  
† Populated only by the withheld modern outpatient records.  
‡ Defined in the ontology but not populated by any released source.  

**Table 3 | Relation types: declared domain, range and cardinality, and observed counts.**

| Relation | Chinese label | Domain → range | Declared cardinality | Exceptions* | Relations |
| --- | --- | --- | --- | ---: | ---: |
| *Lineage layer* | | | | | |
| proposes | 主张 | Physician → Doctrine | 0..* | – | 1,278 |
| authored | 撰写 | Physician → Work | 0..* | – | 430 |
| statedIn | 载于 | Doctrine → Work | 0..1 | 11 | 275 |
| editedRevised | 校勘增订 | Physician → Work | 0..* | – | 126 |
| influencedBy | 私淑 | Physician → Physician | 0..* | – | 120 |
| studiedUnder | 师承 | Physician → Physician | 0..* | – | 78 |
| *Diagnosis layer* | | | | | |
| signIndicates | 征象提示 | Diagnostic sign → Pattern | 0..* | – | 859 |
| subPatternOf | 子证候 | Pattern → Pattern | 0..1 | 2 | 296 |
| belongsToChannel | 属于六经 | Pattern → Pattern | 0..1 | 3 | 159 |
| signExcludes | 征象排除 | Diagnostic sign → Pattern | 0..* | – | 48 |
| *Pattern layer* | | | | | |
| formulaTreats | 方剂主治 | Formula → Pattern | 0..* | – | 767 |
| treatedByPrinciple | 治法对应 | Pattern → Treatment principle | 0..* | – | 428 |
| manifestsAs | 表现为 | Pattern → Symptom | 0..* | – | 370 |
| patternOfDisease | 病之证候 | Pattern → Disease | 0..* | – | 360 |
| principleRealizedBy | 治法用方 | Treatment principle → Formula | 0..* | – | 227 |
| diseaseTreatedByFormula | 病之主方 | Formula → Disease | 0..* | – | 42 |
| diseaseManifestsAs | 病之症状 | Disease → Symptom | 0..* | – | 9 |
| diseaseSubtypeOf † | 病之子类 | Disease → Disease | 0..* | – | 0 |
| *Materia medica layer* | | | | | |
| herbHasProperty | 药性归经 | Herb → Herb property | 0..* | – | 128 |
| derivesFrom | 源自 | Formula → Work | 0..1 | 14 | 50 |
| hasIngredient | 药物组成 | Formula → Herb | 1..* | – | 41 |
| addHerbIf † | 随症加药 | Formula → Herb | 0..* | – | 0 |
| hasDosage † | 用量 | Formula → Dosage | 0..* | – | 0 |
| ingredientRole † | 君臣佐使 | Formula → Herb | 0..* | – | 0 |
| modifiedBy † | 加减变化 | Formula → Formula | 0..* | – | 0 |
| removeHerbIf † | 随症减药 | Formula → Herb | 0..* | – | 0 |
| *Case records layer* | | | | | |
| caseUsesHerb | 医案用药 | Case record → Herb | 0..* | – | 8,486 |
| caseShowsSymptom | 医案见症 | Case record → Symptom | 0..* | – | 3,233 |
| caseShowsSign | 医案见象 | Case record → Diagnostic sign | 0..* | – | 1,875 |
| caseAppliesPrinciple | 医案治法 | Case record → Treatment principle | 0..* | – | 1,109 |
| caseDiagnosedAs | 医案诊断 | Case record → Disease | 0..* | – | 702 |
| caseShowsPattern | 医案辨证 | Case record → Pattern | 0..* | – | 434 |
| caseUsesFormula | 医案用方 | Case record → Formula | 0..* | – | 429 |
| caseByPhysician † | 医案医家 | Case record → Physician | 0..1 | 0 | 0 |
| *Culture layer* | | | | | |
| physicianOfPlace | 籍贯 | Physician → Place | 0..1 | 20 | 203 |
| physicianInFamily | 属于世家 | Physician → Medical family | 0..1 | 3 | 66 |
| institutionAtPlace | 机构所在 | Institution → Place | 0..1 | 2 | 41 |
| physicianFounded | 创办机构 | Physician → Institution | 0..* | – | 23 |
| familySpecializesIn | 世家专科 | Medical family → Disease | 0..* | – | 6 |
| *Modern outpatient records (withheld) ‡* | | | | | |
| caseComorbidity | 医案既往史 | Case record → Disease | 0..* | – | 0 |
| caseHasExamination | 医案辅助检查 | Case record → Examination | 0..* | – | 0 |
| caseUsesProcedure | 医案外治操作 | Case record → Procedure | 0..* | – | 0 |
| caseUsesWesternDrug | 医案西药 | Case record → Western drug | 0..* | – | 0 |
| caseWesternDiagnosis | 医案西医诊断 | Case record → Western diagnosis | 0..* | – | 0 |
| examSupportsDiagnosis | 检查支持诊断 | Examination → Western diagnosis | 0..* | – | 0 |
| wdCorrespondsToTcm | 西医病名对应中医病名 | Western diagnosis → Disease | 0..* | – | 0 |
| **Total** |  | 32 of 46 relation types populated |  | 55 | 22,698 |

* Subjects with more than one distinct object for a relation declared 0..1; reported, not corrected. –, relation declared 0..* or 1..*.  
† Defined in the ontology but not populated by any released source.  
‡ Populated only by the withheld modern outpatient records.  

**Table 4 | Data records.**

| File* | Format | Size (MB)† | Records | Content |
| --- | --- | ---: | --- | --- |
| shaopai_kg.json | JSON | 23.04 | 18,149 entities; 22,698 relations | Complete graph: ontology, controlled vocabularies, entities with attributes and provenance, relations with evidence fields |
| nodes.csv | CSV | 2.28 | 18,149 rows | Entities in Neo4j import format, with attributes, layout coordinates and component index |
| edges.csv | CSV | 4.62 | 22,698 rows | Relations with passage identifier, evidence sentence, chapter path, layer, source work, verification flags |
| load_neo4j.cypher | Cypher | 0.04 | – | Constraints, indexes and batched import script |
| example_queries.cypher | Cypher | 0.01 | 29 queries | Worked graph queries with SPARQL equivalents |
| shaopai_instances.ttl | RDF/Turtle | 15.36 | 410,261 triples | Instance data; each relation reified as rdf:Statement carrying its provenance |
| shaopai_ontology.ttl | OWL/Turtle | 0.03 | 20 classes; 46 relation types; 810 triples | Ontology with bilingual labels, domains, ranges and cardinality annotations |
| corpus_yueyi.json | JSON | 2.75 | 4,395 passages | Segmented text of seven source works with passage identifiers and chapter paths |
| corpus_shaopai.json | JSON | 0.86 | 1,586 passages | Segmented text of Shaopai Shanghan (b-numbered re-segmentation) |
| layout_positions.json | JSON | 0.76 | 18,149 coordinates | Fixed two-dimensional layout used by the web explorer |
| disease_profiles.csv | CSV | 0.06 | 416 rows | Per-disease case counts with co-occurring herbs and symptoms (He Lianchen case records) |
| modern_case_profiles.csv | CSV | <0.01 | 9 rows | Aggregate profile of the withheld outpatient records; cells with fewer than 3 cases suppressed |
| qc_audit.json | JSON | 0.01 | – | Machine-readable quality-control figures |
| QC_AUDIT.md | Markdown | 0.01 | – | Quality-control report |

* In the data/ directory of the repository; the web explorer (explorer.html) and the two-book edition (v1.html) embed the same graph.  
† 1 MB = 1,000,000 bytes.  

**Table 5 | Summary of technical validation.**

| Check | Scope | Result |
| --- | --- | --- |
| Schema conformance (domain and range) | All relations (22,698) | 0 violations |
| Referential integrity | All relations (22,698) | 0 dangling endpoints |
| Self-loops | All relations (22,698) | 0 |
| Duplicate (subject, relation, object) triples | All relations (22,698) | 0 |
| Passage identifier present | All relations (22,698) | 22,698 (100.0%) |
| Evidence sentence present | All relations (22,698) | 22,678 (99.9%) |
| Evidence sentence located in cited passage* | Relations with resolvable passage (18,368) | 17,788 (96.8%) |
| Upstream verbatim flag not confirmed* | Flagged verbatim, passage resolvable (18,091) | 312 (1.7%) |
| Cited passage not resolvable† | All relations (22,698) | 4,330 (19.1%) |
| Declared 0..1 cardinality | 7 relation types | 55 subjects with >1 object |
| Identity resolution | Entities | 93 merged (89 script-variant groups; 5 name-variant pairs) |
| Extraction coverage‡ | Routed passages per layer | 74.9–100.0% (lowest: Culture) |
| Evidence redundancy | All relations (22,698) | 22,368 (98.5%) supported by one mention |
| Privacy screening§ | All released files | 0 matches; modern outpatient layer withheld |
| Cross-model agreement | All relations (22,698) | Not assessed (single extraction model) |

* After Unicode NFKC normalization and removal of white space; multi-part evidence joined by “ / ” counts as located when every part is found.  
† Relations from Shaopai Shanghan cite an upstream passage segmentation that could not be aligned with the released text.  
‡ Share of passages routed to a layer from which relations were extracted; shortfalls arise from per-frame output limits, so counts from those layers are lower bounds.  
§ Patient-header patterns (name, sex, age and record number), national identity and telephone numbers, and patient names derived at run time from the withheld records.  
