// AION Neo4j Seed Data — Demo Organization
// Creates a sample organizational knowledge graph for demonstration

// Demo Organization
MERGE (o:Organization {org_id: 'demo-org-001'})
SET o.name = 'Acme Corp', o.industry = 'technology', o.size = 'medium';

// Departments
MERGE (eng:Department {dept_id: 'dept-eng', org_id: 'demo-org-001'})
SET eng.name = 'Engineering', eng.code = 'ENG';

MERGE (prod:Department {dept_id: 'dept-prod', org_id: 'demo-org-001'})
SET prod.name = 'Product', prod.code = 'PROD';

MERGE (sales:Department {dept_id: 'dept-sales', org_id: 'demo-org-001'})
SET sales.name = 'Sales', sales.code = 'SALES';

// People
MERGE (alice:Person {user_id: 'user-001', org_id: 'demo-org-001'})
SET alice.name = 'Alice Chen', alice.role = 'Lead Engineer', alice.email = 'alice@acme.com';

MERGE (bob:Person {user_id: 'user-002', org_id: 'demo-org-001'})
SET bob.name = 'Bob Smith', bob.role = 'Product Manager', bob.email = 'bob@acme.com';

MERGE (carol:Person {user_id: 'user-003', org_id: 'demo-org-001'})
SET carol.name = 'Carol White', carol.role = 'Senior Engineer', carol.email = 'carol@acme.com';

// Knowledge nodes
MERGE (k1:Knowledge {knowledge_id: 'know-001', org_id: 'demo-org-001'})
SET k1.name = 'Microservices Architecture', k1.domain = 'engineering', k1.relevance_score = 0.95;

MERGE (k2:Knowledge {knowledge_id: 'know-002', org_id: 'demo-org-001'})
SET k2.name = 'Customer Onboarding Process', k2.domain = 'sales', k2.relevance_score = 0.88;

MERGE (k3:Knowledge {knowledge_id: 'know-003', org_id: 'demo-org-001'})
SET k3.name = 'Deployment Pipeline', k3.domain = 'engineering', k3.relevance_score = 0.92;

// Projects
MERGE (p1:Project {project_id: 'proj-001', org_id: 'demo-org-001'})
SET p1.name = 'Platform v2.0', p1.status = 'active', p1.priority = 'high';

// Relationships
MERGE (alice)-[:KNOWS {strength: 0.95}]->(k1);
MERGE (alice)-[:KNOWS {strength: 0.90}]->(k3);
MERGE (carol)-[:KNOWS {strength: 0.85}]->(k1);
MERGE (carol)-[:KNOWS {strength: 0.90}]->(k3);
MERGE (bob)-[:KNOWS {strength: 0.80}]->(k2);

MERGE (alice)-[:COLLABORATES_WITH {frequency: 0.8}]->(bob);
MERGE (alice)-[:COLLABORATES_WITH {frequency: 0.9}]->(carol);
MERGE (bob)-[:COLLABORATES_WITH {frequency: 0.7}]->(carol);

MERGE (alice)-[:CONTRIBUTES_TO]->(p1);
MERGE (carol)-[:CONTRIBUTES_TO]->(p1);
MERGE (bob)-[:CONTRIBUTES_TO]->(p1);

MERGE (p1)-[:DEPENDS_ON]->(k1);
MERGE (p1)-[:DEPENDS_ON]->(k3);

MERGE (alice)-[:BELONGS_TO]->(eng);
MERGE (carol)-[:BELONGS_TO]->(eng);
MERGE (bob)-[:BELONGS_TO]->(prod);
