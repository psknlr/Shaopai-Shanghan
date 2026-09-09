// 绍派伤寒 · 越医知识图谱 — Neo4j loader（由 tools/export_csv.py 生成）
// 用法：把 nodes.csv 与 edges.csv 放入 DBMS 的 import/ 目录，然后运行本文件。
// 节点 18,151 · 关系 22,700 · 本体 1.1.0

// ---------- 约束与索引 ----------
CREATE CONSTRAINT physician_id IF NOT EXISTS FOR (n:Physician) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT work_id IF NOT EXISTS FOR (n:Work) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT doctrine_id IF NOT EXISTS FOR (n:Doctrine) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (n:Pattern) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (n:Symptom) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT diagnosticsign_id IF NOT EXISTS FOR (n:DiagnosticSign) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT treatmentprinciple_id IF NOT EXISTS FOR (n:TreatmentPrinciple) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT formula_id IF NOT EXISTS FOR (n:Formula) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT herb_id IF NOT EXISTS FOR (n:Herb) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT herbproperty_id IF NOT EXISTS FOR (n:HerbProperty) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT dosage_id IF NOT EXISTS FOR (n:Dosage) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT caserecord_id IF NOT EXISTS FOR (n:CaseRecord) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (n:Institution) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT place_id IF NOT EXISTS FOR (n:Place) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT medicalfamily_id IF NOT EXISTS FOR (n:MedicalFamily) REQUIRE n.id IS UNIQUE;
CREATE INDEX physician_name IF NOT EXISTS FOR (n:Physician) ON (n.name);
CREATE INDEX work_name IF NOT EXISTS FOR (n:Work) ON (n.name);
CREATE INDEX doctrine_name IF NOT EXISTS FOR (n:Doctrine) ON (n.name);
CREATE INDEX diagnosticsign_name IF NOT EXISTS FOR (n:DiagnosticSign) ON (n.name);
CREATE INDEX pattern_name IF NOT EXISTS FOR (n:Pattern) ON (n.name);
CREATE INDEX disease_name IF NOT EXISTS FOR (n:Disease) ON (n.name);
CREATE INDEX symptom_name IF NOT EXISTS FOR (n:Symptom) ON (n.name);
CREATE INDEX treatmentprinciple_name IF NOT EXISTS FOR (n:TreatmentPrinciple) ON (n.name);
CREATE INDEX herb_name IF NOT EXISTS FOR (n:Herb) ON (n.name);
CREATE INDEX formula_name IF NOT EXISTS FOR (n:Formula) ON (n.name);
CREATE INDEX medicalfamily_name IF NOT EXISTS FOR (n:MedicalFamily) ON (n.name);
CREATE INDEX institution_name IF NOT EXISTS FOR (n:Institution) ON (n.name);
CREATE INDEX place_name IF NOT EXISTS FOR (n:Place) ON (n.name);
CREATE INDEX caserecord_name IF NOT EXISTS FOR (n:CaseRecord) ON (n.name);
CREATE INDEX herbproperty_name IF NOT EXISTS FOR (n:HerbProperty) ON (n.name);
CREATE INDEX diagnosticsign_modality IF NOT EXISTS FOR (n:DiagnosticSign) ON (n.modality);
CREATE INDEX doctrine_topic IF NOT EXISTS FOR (n:Doctrine) ON (n.topic);
CREATE INDEX caserecord_physician IF NOT EXISTS FOR (n:CaseRecord) ON (n.physician);

// ---------- 节点（按标签分批）----------
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Physician'
  MERGE (n:Physician {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.courtesy_name = CASE WHEN row['courtesy_name:string'] = '' THEN null ELSE row['courtesy_name:string'] END,
      n.birth_year = CASE WHEN row['birth_year:string'] = '' THEN null ELSE row['birth_year:string'] END,
      n.death_year = CASE WHEN row['death_year:string'] = '' THEN null ELSE row['death_year:string'] END,
      n.native_place = CASE WHEN row['native_place:string'] = '' THEN null ELSE row['native_place:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Work'
  MERGE (n:Work {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.author = CASE WHEN row['author:string'] = '' THEN null ELSE row['author:string'] END,
      n.year = CASE WHEN row['year:string'] = '' THEN null ELSE row['year:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Doctrine'
  MERGE (n:Doctrine {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.statement_zh = CASE WHEN row['statement_zh:string'] = '' THEN null ELSE row['statement_zh:string'] END,
      n.topic = CASE WHEN row['topic:string'] = '' THEN null ELSE row['topic:string'] END,
      n.proposed_by = CASE WHEN row['proposed_by:string'] = '' THEN null ELSE row['proposed_by:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'DiagnosticSign'
  MERGE (n:DiagnosticSign {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.modality = CASE WHEN row['modality:string'] = '' THEN null ELSE row['modality:string'] END,
      n.descriptor = CASE WHEN row['descriptor:string'] = '' THEN null ELSE row['descriptor:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Pattern'
  MERGE (n:Pattern {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.channel = CASE WHEN row['channel:string'] = '' THEN null ELSE row['channel:string'] END,
      n.triple_burner = CASE WHEN row['triple_burner:string'] = '' THEN null ELSE row['triple_burner:string'] END,
      n.nature = CASE WHEN row['nature:string'] = '' THEN null ELSE row['nature:string'] END,
      n.note = CASE WHEN row['note:string'] = '' THEN null ELSE row['note:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Disease'
  MERGE (n:Disease {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.category = CASE WHEN row['category:string'] = '' THEN null ELSE row['category:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Symptom'
  MERGE (n:Symptom {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float'])
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'TreatmentPrinciple'
  MERGE (n:TreatmentPrinciple {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float'])
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Herb'
  MERGE (n:Herb {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.dose = CASE WHEN row['dose:string'] = '' THEN null ELSE row['dose:string'] END,
      n.unit = CASE WHEN row['unit:string'] = '' THEN null ELSE row['unit:string'] END,
      n.processing = CASE WHEN row['processing:string'] = '' THEN null ELSE row['processing:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Formula'
  MERGE (n:Formula {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float'])
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'MedicalFamily'
  MERGE (n:MedicalFamily {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.specialty = CASE WHEN row['specialty:string'] = '' THEN null ELSE row['specialty:string'] END,
      n.place = CASE WHEN row['place:string'] = '' THEN null ELSE row['place:string'] END,
      n.generations = CASE WHEN row['generations:string'] = '' THEN null ELSE row['generations:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Institution'
  MERGE (n:Institution {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.kind = CASE WHEN row['kind:string'] = '' THEN null ELSE row['kind:string'] END,
      n.place = CASE WHEN row['place:string'] = '' THEN null ELSE row['place:string'] END,
      n.founder = CASE WHEN row['founder:string'] = '' THEN null ELSE row['founder:string'] END,
      n.founded_year = CASE WHEN row['founded_year:string'] = '' THEN null ELSE row['founded_year:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Place'
  MERGE (n:Place {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.modern_name = CASE WHEN row['modern_name:string'] = '' THEN null ELSE row['modern_name:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'CaseRecord'
  MERGE (n:CaseRecord {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float']),
      n.patient_desc = CASE WHEN row['patient_desc:string'] = '' THEN null ELSE row['patient_desc:string'] END,
      n.presentation = CASE WHEN row['presentation:string'] = '' THEN null ELSE row['presentation:string'] END,
      n.physician = CASE WHEN row['physician:string'] = '' THEN null ELSE row['physician:string'] END
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'HerbProperty'
  MERGE (n:HerbProperty {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.component = toInteger(row['component:int']),
      n.x = toFloat(row['x:float']),
      n.y = toFloat(row['y:float'])
} IN TRANSACTIONS OF 1000 ROWS;

// ---------- 关系（APOC）----------
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
CALL {
  WITH row
  MATCH (s {id: row[':START_ID']}), (o {id: row[':END_ID']})
  CALL apoc.merge.relationship(s, row[':TYPE'], {}, {
    n_support: toInteger(row['n_support:int']),
    layer: row['layer:string'],
    corpus: row['corpus:string'],
    source_sentence: row['source_sentence:string'],
    chapter_path: row['chapter_path:string'],
    passage_id: row['passage_id:string'],
    evidence_verbatim: row['evidence_verbatim:boolean'] = 'true',
    engine: row['engine:string'],
    agreement: row['agreement:string']
  }, o) YIELD rel
  RETURN rel
} IN TRANSACTIONS OF 1000 ROWS;

// ---------- 关系（无 APOC 时的逐类型替代：去掉每行开头的 "// " 后运行）----------
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseUsesHerb'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:Herb {id: row[':END_ID']}) MERGE (s)-[rel:caseUsesHerb]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseShowsSymptom'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:Symptom {id: row[':END_ID']}) MERGE (s)-[rel:caseShowsSymptom]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseShowsSign'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:DiagnosticSign {id: row[':END_ID']}) MERGE (s)-[rel:caseShowsSign]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'proposes'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Doctrine {id: row[':END_ID']}) MERGE (s)-[rel:proposes]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseAppliesPrinciple'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:TreatmentPrinciple {id: row[':END_ID']}) MERGE (s)-[rel:caseAppliesPrinciple]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'signIndicates'
// MATCH (s:DiagnosticSign {id: row[':START_ID']}), (o:Pattern {id: row[':END_ID']}) MERGE (s)-[rel:signIndicates]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'formulaTreats'
// MATCH (s:Formula {id: row[':START_ID']}), (o:Pattern {id: row[':END_ID']}) MERGE (s)-[rel:formulaTreats]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseDiagnosedAs'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:Disease {id: row[':END_ID']}) MERGE (s)-[rel:caseDiagnosedAs]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseShowsPattern'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:Pattern {id: row[':END_ID']}) MERGE (s)-[rel:caseShowsPattern]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'authored'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Work {id: row[':END_ID']}) MERGE (s)-[rel:authored]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'caseUsesFormula'
// MATCH (s:CaseRecord {id: row[':START_ID']}), (o:Formula {id: row[':END_ID']}) MERGE (s)-[rel:caseUsesFormula]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'treatedByPrinciple'
// MATCH (s:Pattern {id: row[':START_ID']}), (o:TreatmentPrinciple {id: row[':END_ID']}) MERGE (s)-[rel:treatedByPrinciple]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'manifestsAs'
// MATCH (s:Pattern {id: row[':START_ID']}), (o:Symptom {id: row[':END_ID']}) MERGE (s)-[rel:manifestsAs]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'patternOfDisease'
// MATCH (s:Pattern {id: row[':START_ID']}), (o:Disease {id: row[':END_ID']}) MERGE (s)-[rel:patternOfDisease]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'subPatternOf'
// MATCH (s:Pattern {id: row[':START_ID']}), (o:Pattern {id: row[':END_ID']}) MERGE (s)-[rel:subPatternOf]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'statedIn'
// MATCH (s:Doctrine {id: row[':START_ID']}), (o:Work {id: row[':END_ID']}) MERGE (s)-[rel:statedIn]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'principleRealizedBy'
// MATCH (s:TreatmentPrinciple {id: row[':START_ID']}), (o:Formula {id: row[':END_ID']}) MERGE (s)-[rel:principleRealizedBy]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'physicianOfPlace'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Place {id: row[':END_ID']}) MERGE (s)-[rel:physicianOfPlace]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'belongsToChannel'
// MATCH (s:Pattern {id: row[':START_ID']}), (o:Pattern {id: row[':END_ID']}) MERGE (s)-[rel:belongsToChannel]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'herbHasProperty'
// MATCH (s:Herb {id: row[':START_ID']}), (o:HerbProperty {id: row[':END_ID']}) MERGE (s)-[rel:herbHasProperty]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'editedRevised'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Work {id: row[':END_ID']}) MERGE (s)-[rel:editedRevised]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'influencedBy'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Physician {id: row[':END_ID']}) MERGE (s)-[rel:influencedBy]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'studiedUnder'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Physician {id: row[':END_ID']}) MERGE (s)-[rel:studiedUnder]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'physicianInFamily'
// MATCH (s:Physician {id: row[':START_ID']}), (o:MedicalFamily {id: row[':END_ID']}) MERGE (s)-[rel:physicianInFamily]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'derivesFrom'
// MATCH (s:Formula {id: row[':START_ID']}), (o:Work {id: row[':END_ID']}) MERGE (s)-[rel:derivesFrom]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'signExcludes'
// MATCH (s:DiagnosticSign {id: row[':START_ID']}), (o:Pattern {id: row[':END_ID']}) MERGE (s)-[rel:signExcludes]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'diseaseTreatedByFormula'
// MATCH (s:Formula {id: row[':START_ID']}), (o:Disease {id: row[':END_ID']}) MERGE (s)-[rel:diseaseTreatedByFormula]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'hasIngredient'
// MATCH (s:Formula {id: row[':START_ID']}), (o:Herb {id: row[':END_ID']}) MERGE (s)-[rel:hasIngredient]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'institutionAtPlace'
// MATCH (s:Institution {id: row[':START_ID']}), (o:Place {id: row[':END_ID']}) MERGE (s)-[rel:institutionAtPlace]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'physicianFounded'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Institution {id: row[':END_ID']}) MERGE (s)-[rel:physicianFounded]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'diseaseManifestsAs'
// MATCH (s:Disease {id: row[':START_ID']}), (o:Symptom {id: row[':END_ID']}) MERGE (s)-[rel:diseaseManifestsAs]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row WITH row WHERE row[':TYPE'] = 'familySpecializesIn'
// MATCH (s:MedicalFamily {id: row[':START_ID']}), (o:Disease {id: row[':END_ID']}) MERGE (s)-[rel:familySpecializesIn]->(o)
// SET rel.n_support = toInteger(row['n_support:int']), rel.layer = row['layer:string'], rel.corpus = row['corpus:string'], rel.source_sentence = row['source_sentence:string'], rel.chapter_path = row['chapter_path:string'], rel.passage_id = row['passage_id:string'], rel.evidence_verbatim = row['evidence_verbatim:boolean'] = 'true', rel.engine = row['engine:string'], rel.agreement = row['agreement:string'];
