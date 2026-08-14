// 绍派伤寒 Knowledge Graph — Neo4j loader
// Usage: place nodes.csv and edges.csv in the DBMS import/ folder, then run this file.

// ---------- constraints & indexes ----------
CREATE CONSTRAINT physician_id IF NOT EXISTS FOR (n:Physician) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT work_id      IF NOT EXISTS FOR (n:Work)      REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT doctrine_id  IF NOT EXISTS FOR (n:Doctrine)  REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sign_id      IF NOT EXISTS FOR (n:DiagnosticSign) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT pattern_id    IF NOT EXISTS FOR (n:Pattern)        REQUIRE n.id IS UNIQUE;
CREATE INDEX sign_name    IF NOT EXISTS FOR (n:DiagnosticSign) ON (n.name);
CREATE INDEX pattern_name IF NOT EXISTS FOR (n:Pattern)        ON (n.name);
CREATE INDEX sign_modality IF NOT EXISTS FOR (n:DiagnosticSign) ON (n.modality);
CREATE INDEX physician_name IF NOT EXISTS FOR (n:Physician) ON (n.name);
CREATE INDEX work_name      IF NOT EXISTS FOR (n:Work)      ON (n.name);
CREATE INDEX doctrine_topic IF NOT EXISTS FOR (n:Doctrine)  ON (n.topic);

// ---------- nodes ----------
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Physician'
  MERGE (n:Physician {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.courtesy_name = row['courtesy_name:string'],
      n.birth_year = row['birth_year:string'],
      n.death_year = row['death_year:string'],
      n.native_place = row['native_place:string']
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Work'
  MERGE (n:Work {id: row[':ID']})
  SET n.name = row['name:string'],
      n.aliases = CASE WHEN row['aliases:string[]'] = '' THEN [] ELSE split(row['aliases:string[]'], ';') END,
      n.n_mentions = toInteger(row['n_mentions:int']),
      n.author = row['author:string'],
      n.year = row['year:string']
} IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  WITH row WHERE row[':LABEL'] = 'Doctrine'
  MERGE (n:Doctrine {id: row[':ID']})
  SET n.name = row['name:string'],
      n.statement_zh = row['statement_zh:string'],
      n.topic = row['topic:string'],
      n.proposed_by = row['proposed_by:string'],
      n.n_mentions = toInteger(row['n_mentions:int'])
} IN TRANSACTIONS OF 1000 ROWS;

// ---------- edges ----------
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
CALL {
  WITH row
  MATCH (s {id: row[':START_ID']}), (o {id: row[':END_ID']})
  CALL apoc.merge.relationship(s, row[':TYPE'], {}, {
    n_support: toInteger(row['n_support:int']),
    source_sentence: row['source_sentence:string'],
    chapter_path: row['chapter_path:string'],
    passage_id: row['passage_id:string'],
    evidence_verbatim: row['evidence_verbatim:boolean'] = 'true',
    engine: row['engine:string'],
    agreement: row['agreement:string']
  }, o) YIELD rel
  RETURN rel
} IN TRANSACTIONS OF 1000 ROWS;

// If APOC is unavailable, load each relationship type explicitly instead, e.g.:
// LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
// WITH row WHERE row[':TYPE'] = 'authored'
// MATCH (s:Physician {id: row[':START_ID']}), (o:Work {id: row[':END_ID']})
// MERGE (s)-[r:authored]->(o)
// SET r.source_sentence = row['source_sentence:string'], r.n_support = toInteger(row['n_support:int']);
