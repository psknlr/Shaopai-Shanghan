// ---- Example queries ----

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
RETURN type(r) AS rel, r.source_sentence AS claimed_evidence, r.passage_id AS passage LIMIT 50;

// ---------- 诊法层 (diagnostics) ----------

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

// ---------- SPARQL equivalents (for the Turtle files) ----------
// NOTE: all Chinese literals in the RDF carry an @zh language tag. A plain
// "腹诊" will NOT match — you must write "腹诊"@zh. Example:
//
//   PREFIX sp:<https://w3id.org/shaopai/ontology#>
//   PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
//   SELECT ?sign ?pattern WHERE {
//     ?s sp:modality "腹诊"@zh ; rdfs:label ?sign ; sp:signIndicates ?p .
//     ?p rdfs:label ?pattern }
//
// Verified output includes 虚里跃动应衣 → 宗气外泄 and 三脘痞硬 → 胃家实.
