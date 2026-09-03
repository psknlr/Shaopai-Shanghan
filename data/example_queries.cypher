// ---- 绍派伤寒 · 越医知识图谱 — Example queries ----
// 载入方式见 load_neo4j.cypher。关系属性：n_support · layer · source_sentence · chapter_path ·
// evidence_verbatim · engine · agreement（本副本的 passage_id 为空，核验以原文与章节路径为准）。

// ---------- 谱系层 (lineage) ----------

// 1. Intellectual genealogy: who studied under or was influenced by whom
MATCH (a:Physician)-[r:studiedUnder|influencedBy]->(b:Physician)
RETURN a.name AS student, type(r) AS link, b.name AS teacher, r.source_sentence AS evidence
ORDER BY link, student;

// 2. The school's defining doctrines, with attribution and source
MATCH (p:Physician)-[r:proposes]->(d:Doctrine)
WHERE d.statement_zh CONTAINS '六经' OR d.statement_zh CONTAINS '三焦'
RETURN p.name AS physician, d.statement_zh AS doctrine, r.chapter_path AS chapter
ORDER BY physician;

// 3. Bibliography of a given physician
MATCH (p:Physician {name: '俞根初'})-[r:authored|editedRevised]->(w:Work)
RETURN type(r) AS role, w.name AS work, r.source_sentence AS evidence;

// 4. Editorial chain around 《通俗伤寒论》 — who wrote, revised, annotated it
MATCH (p:Physician)-[r]->(w:Work)
WHERE w.name CONTAINS '通俗伤寒论'
RETURN w.name AS work, type(r) AS role, p.name AS physician, r.chapter_path AS chapter
ORDER BY work, role;

// 5. Best-supported assertions in the graph (most independent mentions)
MATCH (s)-[r]->(o)
RETURN labels(s)[0] AS from_type, s.name AS subject, type(r) AS rel,
       o.name AS object, r.n_support AS support
ORDER BY support DESC LIMIT 25;

// 6. Provenance audit: any edge whose evidence is not verbatim
MATCH ()-[r]->() WHERE r.evidence_verbatim = false
RETURN type(r) AS rel, r.source_sentence AS claimed_evidence, r.chapter_path AS chapter LIMIT 50;

// ---------- 诊法层 (diagnostic) ----------

// 7. 腹诊 signs and the patterns they indicate — the school's signature method
MATCH (s:DiagnosticSign {modality:'腹诊'})-[r:signIndicates]->(p:Pattern)
RETURN s.name AS sign, p.name AS pattern, r.source_sentence AS evidence, r.chapter_path AS chapter
ORDER BY sign LIMIT 40;

// 8. 目诊 (ocular diagnosis) inventory
MATCH (s:DiagnosticSign {modality:'目诊'})
OPTIONAL MATCH (s)-[r:signIndicates]->(p:Pattern)
RETURN s.name AS sign, collect(p.name) AS indicates, s.n_mentions AS mentions
ORDER BY mentions DESC LIMIT 30;

// 9. Patterns grouped by six-channel attribution
MATCH (p:Pattern)-[:belongsToChannel]->(c:Pattern)
RETURN c.name AS channel, count(p) AS n_patterns, collect(p.name)[..8] AS examples
ORDER BY n_patterns DESC;

// 10. Which signs are most diagnostically loaded (indicate the most patterns)?
MATCH (s:DiagnosticSign)-[:signIndicates]->(p:Pattern)
RETURN s.name AS sign, s.modality AS modality, count(DISTINCT p) AS n_patterns
ORDER BY n_patterns DESC LIMIT 25;

// 11. Exclusion reasoning — 征象排除
MATCH (s:DiagnosticSign)-[r:signExcludes]->(p:Pattern)
RETURN s.name AS sign, p.name AS excluded_pattern, r.source_sentence AS evidence LIMIT 30;

// 12. Tongue findings and their pattern targets, by coat descriptor
MATCH (s:DiagnosticSign {modality:'舌诊'})-[:signIndicates]->(p:Pattern)
RETURN s.descriptor AS coat, collect(DISTINCT p.name)[..6] AS patterns, count(*) AS n
ORDER BY n DESC LIMIT 20;

// ---------- 证候层 (pattern) ----------

// 13. Pattern → treatment principle → the formulas that realise it
MATCH (p:Pattern)-[:treatedByPrinciple]->(t:TreatmentPrinciple)
OPTIONAL MATCH (t)-[:principleRealizedBy]->(f:Formula)
RETURN p.name AS pattern, t.name AS principle, collect(DISTINCT f.name) AS formulas
ORDER BY pattern LIMIT 40;

// 14. Diseases with the most named sub-patterns
MATCH (p:Pattern)-[:patternOfDisease]->(d:Disease)
RETURN d.name AS disease, d.category AS category, count(p) AS n_patterns, collect(p.name)[..6] AS examples
ORDER BY n_patterns DESC LIMIT 20;

// ---------- 医案层 (case) ----------

// 15. Signature herbs of a disease, by co-occurrence across its cases (cf. disease_profiles.csv)
MATCH (c:CaseRecord)-[:caseDiagnosedAs]->(d:Disease {name:'疟'}), (c)-[:caseUsesHerb]->(h:Herb)
RETURN h.name AS herb, count(DISTINCT c) AS cases
ORDER BY cases DESC LIMIT 10;

// 16. Cases presenting 胃钝 (the most frequent symptom) and what they were diagnosed as
MATCH (c:CaseRecord)-[:caseShowsSymptom]->(:Symptom {name:'胃钝'})
OPTIONAL MATCH (c)-[:caseDiagnosedAs]->(d:Disease)
RETURN d.name AS disease, count(DISTINCT c) AS cases
ORDER BY cases DESC LIMIT 15;

// 17. Herb pairs most often prescribed together
MATCH (c:CaseRecord)-[:caseUsesHerb]->(a:Herb), (c)-[:caseUsesHerb]->(b:Herb)
WHERE a.name < b.name
RETURN a.name AS herb_a, b.name AS herb_b, count(*) AS cases
ORDER BY cases DESC LIMIT 20;

// 18. Ready-made formulas (成方) used in cases, with the patterns those cases were assigned
MATCH (c:CaseRecord)-[:caseUsesFormula]->(f:Formula)
OPTIONAL MATCH (c)-[:caseShowsPattern]->(p:Pattern)
RETURN f.name AS formula, count(DISTINCT c) AS cases, collect(DISTINCT p.name)[..5] AS patterns
ORDER BY cases DESC LIMIT 15;

// 19. One case in full: everything 何廉臣 recorded for it
MATCH (c:CaseRecord {name:'案278 肝热夹痰上冲心肺'})-[r]->(x)
RETURN type(r) AS rel, labels(x)[0] AS kind, x.name AS name, r.source_sentence AS evidence
ORDER BY rel, name;

// ---------- 越医文化层 (culture) ----------

// 20. Physicians by native place (traditional / simplified variants are separate nodes)
MATCH (p:Physician)-[:physicianOfPlace]->(pl:Place)
RETURN pl.name AS place, pl.modern_name AS modern, count(p) AS physicians, collect(p.name)[..8] AS examples
ORDER BY physicians DESC LIMIT 15;

// 21. Medical families and their members
MATCH (p:Physician)-[:physicianInFamily]->(f:MedicalFamily)
RETURN f.name AS family, f.specialty AS specialty, f.place AS place, f.generations AS generations,
       collect(p.name) AS members
ORDER BY size(members) DESC;

// 22. Institutions founded by physicians, where, and on what evidence
MATCH (p:Physician)-[r:physicianFounded]->(i:Institution)
OPTIONAL MATCH (i)-[:institutionAtPlace]->(pl:Place)
RETURN p.name AS founder, i.name AS institution, i.kind AS kind, i.founded_year AS year,
       pl.name AS place, r.source_sentence AS evidence
ORDER BY year;

// ---------- 跨层与审计 ----------

// 23. From a diagnostic sign to the cases that applied the principle its pattern calls for
MATCH (s:DiagnosticSign)-[:signIndicates]->(p:Pattern)-[:treatedByPrinciple]->(t:TreatmentPrinciple)
      <-[:caseAppliesPrinciple]-(c:CaseRecord)
RETURN s.name AS sign, p.name AS pattern, t.name AS principle, count(DISTINCT c) AS cases
ORDER BY cases DESC LIMIT 20;

// 24. Relation counts per extraction layer and engine
MATCH ()-[r]->()
RETURN r.layer AS layer, r.engine AS engine, count(*) AS n
ORDER BY n DESC;

// 25. Isolated entities (no relation at all) — the long tail kept in the data but hidden from the figure
MATCH (n) WHERE NOT (n)--()
RETURN labels(n)[0] AS kind, count(*) AS n
ORDER BY n DESC;

// ---------- SPARQL equivalents (for the Turtle files) ----------
// NOTE: all Chinese literals in the RDF carry an @zh language tag. A plain
// "腹诊" will NOT match — you must write "腹诊"@zh. Examples:
//
//   PREFIX sp:<https://w3id.org/shaopai/ontology#>
//   PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
//   SELECT ?sign ?pattern WHERE {
//     ?s sp:modality "腹诊"@zh ; rdfs:label ?sign ; sp:signIndicates ?p .
//     ?p rdfs:label ?pattern }
//
//   # herbs used in cases diagnosed as 疟, with the provenance statement behind each use
//   PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
//   SELECT ?case ?herb ?sentence WHERE {
//     ?c sp:caseDiagnosedAs ?d . ?d rdfs:label "疟"@zh .
//     ?c sp:caseUsesHerb ?h ; rdfs:label ?case . ?h rdfs:label ?herb .
//     ?st a rdf:Statement ; rdf:subject ?c ; rdf:predicate sp:caseUsesHerb ; rdf:object ?h ;
//         sp:sourceSentence ?sentence }
//
// Verified output for the first query includes 虚里跃动应衣 → 宗气外泄 and 三脘痞硬 → 胃家实.
