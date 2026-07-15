// AION Neo4j Constraints & Indexes
// Run once on a fresh Neo4j instance

// ── Uniqueness Constraints ───────────────────────────────────────────────────
CREATE CONSTRAINT org_id_unique IF NOT EXISTS
  FOR (o:Organization) REQUIRE o.org_id IS UNIQUE;

CREATE CONSTRAINT person_unique IF NOT EXISTS
  FOR (p:Person) REQUIRE (p.user_id, p.org_id) IS UNIQUE;

CREATE CONSTRAINT knowledge_unique IF NOT EXISTS
  FOR (k:Knowledge) REQUIRE (k.knowledge_id, k.org_id) IS UNIQUE;

CREATE CONSTRAINT project_unique IF NOT EXISTS
  FOR (p:Project) REQUIRE (p.project_id, p.org_id) IS UNIQUE;

CREATE CONSTRAINT department_unique IF NOT EXISTS
  FOR (d:Department) REQUIRE (d.dept_id, d.org_id) IS UNIQUE;

CREATE CONSTRAINT process_unique IF NOT EXISTS
  FOR (p:Process) REQUIRE (p.process_id, p.org_id) IS UNIQUE;

CREATE CONSTRAINT decision_unique IF NOT EXISTS
  FOR (d:Decision) REQUIRE (d.decision_id, d.org_id) IS UNIQUE;

CREATE CONSTRAINT customer_unique IF NOT EXISTS
  FOR (c:Customer) REQUIRE (c.customer_id, c.org_id) IS UNIQUE;

CREATE CONSTRAINT risk_unique IF NOT EXISTS
  FOR (r:Risk) REQUIRE (r.risk_id, r.org_id) IS UNIQUE;

// ── Text Search Indexes ──────────────────────────────────────────────────────
CREATE FULLTEXT INDEX knowledge_fulltext IF NOT EXISTS
  FOR (k:Knowledge) ON EACH [k.name, k.domain, k.description];

CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
  FOR (p:Person) ON EACH [p.name, p.role, p.email];

// ── Range Indexes ────────────────────────────────────────────────────────────
CREATE INDEX person_org_idx IF NOT EXISTS FOR (p:Person) ON (p.org_id);
CREATE INDEX knowledge_org_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.org_id);
CREATE INDEX knowledge_domain_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.domain);
CREATE INDEX knowledge_relevance_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.relevance_score);
CREATE INDEX project_org_idx IF NOT EXISTS FOR (p:Project) ON (p.org_id);
CREATE INDEX dept_org_idx IF NOT EXISTS FOR (d:Department) ON (d.org_id);
