# AION Frontend Integration Specification

> **Artificial Intelligence Organizational Nervous System**  
> Backend: FastAPI · PostgreSQL · Neo4j · Qdrant · Redis · Kafka  
> Base URL: `http://localhost:8000` | API Prefix: `/api/v1`  
> Auth: JWT Bearer tokens (access: 30 min TTL, refresh: 7 days)

---

## Table of Contents

1. [API Inventory](#1-api-inventory)
2. [TypeScript Interfaces](#2-typescript-interfaces)
3. [Frontend Route Map](#3-frontend-route-map)
4. [State Management Plan](#4-state-management-plan)
5. [UI Component Hierarchy](#5-ui-component-hierarchy)
6. [Data Flow Diagram](#6-data-flow-diagram)
7. [Authentication Flow](#7-authentication-flow)
8. [Error Handling Strategy](#8-error-handling-strategy)

---

## 1. API Inventory

### Authentication — `/api/v1/auth`

| Method | Path | Auth Required | Permission | Request Body | Description |
|--------|------|:---:|:---:|--------------|-------------|
| POST | `/auth/register` | No | — | `RegisterRequest` | Creates new org + admin user. Returns token pair. |
| POST | `/auth/login` | No | — | `OAuth2PasswordRequestForm` (`username`, `password`) | Returns token pair |
| POST | `/auth/refresh` | No | — | `{ refresh_token: string }` (query param) | Rotates tokens |
| GET | `/auth/me` | Yes | Any | — | Returns current user info, role, permissions |

**RegisterRequest fields:** `email`, `username`, `full_name`, `password` (min 8), `org_name`, `industry`

**TokenResponse:** `{ access_token, refresh_token, token_type: "bearer", expires_in: 1800 }`

---

### Memory Graph — `/api/v1/graph` · Permission: `read:graph` / `write:graph`

| Method | Path | Auth | Permission | Body / Params | Response |
|--------|------|:---:|:---:|---|---|
| GET | `/graph/nodes` | Yes | `read:graph` | `?node_type=Person\|Knowledge\|Project\|Department&limit=50` | `{ nodes[], total }` |
| POST | `/graph/nodes/person` | Yes | `write:graph` | `CreatePersonRequest` | `{ status, node }` |
| POST | `/graph/nodes/knowledge` | Yes | `write:graph` | `CreateKnowledgeRequest` | `{ status, node }` |
| POST | `/graph/relationships` | Yes | `write:graph` | `CreateRelationshipRequest` | `{ status, relationship_type }` |
| GET | `/graph/traverse` | Yes | `read:graph` | `?from_node_id&relationship_type&max_depth=3` | Subgraph from node |
| GET | `/graph/search` | Yes | `read:graph` | `?q=<text>&domain=<optional>` | `{ query, results[], count }` |

**CreatePersonRequest:** `user_id, name, email, department?, role?, expertise?[]`  
**CreateKnowledgeRequest:** `knowledge_id, title, domain, source_type, summary?, tags?[]`  
**CreateRelationshipRequest:** `from_id, to_id, relationship_type (KNOWS|CONTRIBUTES_TO|COLLABORATES_WITH), properties?`

---

### Knowledge Decay Engine — `/api/v1/decay` · Permission: `read:knowledge` / `read:intelligence`

| Method | Path | Auth | Permission | Params | Response Shape |
|--------|------|:---:|:---:|---|---|
| GET | `/decay/report` | Yes | `read:knowledge` | — | `{ org_id, report_type, summary{isolated_items,single_owner_critical}, isolated_knowledge[], single_owner_critical[], recommendations[] }` |
| GET | `/decay/entropy` | Yes | `read:intelligence` | — | `{ org_id, entropy_bits, domain_distribution[], ...entropy_report }` |
| GET | `/decay/half-life/{knowledge_id}` | Yes | `read:knowledge` | `?domain&access_freq_per_week&last_updated_days_ago&days_since_last_access&owner_count` | `{ knowledge_id, domain, half_life_days, current_relevance, relevance_percentage, days_until_critical, interpretation }` |
| GET | `/decay/forgotten` | Yes | `read:knowledge` | `?threshold_days=90` | `{ threshold_days, forgotten_items[], count }` |
| GET | `/decay/conflicts` | Yes | `read:knowledge` | — | `{ org_id, conflicts[], note }` |

---

### Disease Detection — `/api/v1/diseases` · Permission: `read:intelligence`

| Method | Path | Auth | Permission | Params | Response Shape |
|--------|------|:---:|:---:|---|---|
| GET | `/diseases/scan` | Yes | `read:intelligence` | — | Full disease scan report (see below) |
| GET | `/diseases/report` | Yes | `read:intelligence` | — | Same as scan |
| GET | `/diseases/{disease_type}` | Yes | `read:intelligence` | `disease_type` path param | Single disease info + status |
| GET | `/diseases/timeline` | Yes | `read:intelligence` | — | `{ org_id, predictions{ disease_type: { days_until_critical, status } } }` |

**Valid disease_type values:** `knowledge_cancer` · `memory_alzheimers` · `communication_stroke` · `knowledge_obesity` · `innovation_paralysis`

**Disease Scan Response:**
```
{
  scan_timestamp: string (ISO),
  org_id: string,
  overall_health_score: number (0-100),
  critical_diseases: number,
  warning_diseases: number,
  healthy_dimensions: number,
  diseases: {
    knowledge_cancer: DiseaseResult,
    memory_alzheimers: DiseaseResult,
    communication_stroke: DiseaseResult,
    knowledge_obesity: DiseaseResult,
    innovation_paralysis: DiseaseResult
  }
}
```

**DiseaseResult:**
```
{
  disease_type: string,
  title: string,
  severity: "critical" | "warning" | "healthy",
  severity_score: number (0-100),
  confidence: number (0-1),
  description: string,
  evidence: Record<string, any>,
  days_until_critical: number | null,
  recommended_action: string | null
}
```

---

### Simulation Engine — `/api/v1/simulation` · Permission: `run:simulation`

| Method | Path | Auth | Permission | Body | Response |
|--------|------|:---:|:---:|---|---|
| GET | `/simulation/scenarios` | Yes | `run:simulation` | — | `{ scenarios: PredefinedScenario[] }` |
| POST | `/simulation/run` | Yes | `run:simulation` | `SimulationRequest` | `SimulationResult` |

**SimulationRequest:** `{ scenario_type: string, parameters: Record<string,any>, description?: string }`

**scenario_type values:** `employee_departure` · `mass_resignation` · `department_closure` · `project_delay` · `system_failure`

**SimulationResult:**
```
{
  simulation_id: string,
  scenario_type: string,
  org_id: string,
  status: "completed",
  cascade_chain: any[],
  results: {
    knowledge_loss_percentage: number,
    affected_projects: any[],
    affected_customers: any[],
    orphaned_knowledge: any[],
    revenue_risk_usd: number,
    recovery_time_days: number,
    business_impact_summary: string
  }
}
```

---

### Self-Healing AI — `/api/v1/healing` · Permission: `read:healing` / `approve:healing`

| Method | Path | Auth | Permission | Params / Body | Response |
|--------|------|:---:|:---:|---|---|
| GET | `/healing/recommendations` | Yes | `read:healing` | `?status_filter&priority` | `{ recommendations: HealingAction[], total }` |
| POST | `/healing/recommendations/{id}/approve` | Yes | `approve:healing` | — | `{ status, recommendation_id, next_step }` |
| POST | `/healing/recommendations/{id}/reject` | Yes | `approve:healing` | `?reason` | `{ status, recommendation_id }` |
| POST | `/healing/generate` | Yes | `read:healing` | — | `{ generated: number, recommendations[] }` |

**HealingAction status values:** `pending` · `approved` · `in_progress` · `completed` · `rejected` · `cancelled`  
**action_type values:** `create_sop` · `assign_mentor` · `schedule_training` · `merge_docs` · `archive_files` · `notify_managers` · `generate_onboarding` · `create_quiz` · `update_wiki` · `knowledge_transfer`  
**priority values:** `critical` · `high` · `medium` · `low`

---

### Intelligence Index — `/api/v1/intelligence` · Permission: `read:intelligence`

| Method | Path | Auth | Params | Response |
|--------|------|:---:|---|---|
| GET | `/intelligence/index` | Yes | — | `OIISnapshot` |
| GET | `/intelligence/history` | Yes | `?limit=30` | `OIISnapshot[]` |
| GET | `/intelligence/trends` | Yes | — | `{ trend, current, delta_30d, history[] }` |

**OIISnapshot:**
```
{
  id: string,
  org_id: string,
  computed_at: string,
  overall_health: number (0-1),
  dimensions: {
    knowledge_velocity, knowledge_coverage, knowledge_quality,
    learning_agility, collaboration_density, innovation_index,
    decision_intelligence, cognitive_resilience, knowledge_accessibility,
    expertise_depth, knowledge_retention, adaptability_score
  },
  proprietary_metrics: {
    knowledge_half_life_days: number,
    knowledge_entropy_bits: number,
    memory_compression_ratio: number
  }
}
```

---

### AI Board Advisor — `/api/v1/advisor` · Permission: `view:board`

| Method | Path | Auth | Response |
|--------|------|:---:|---|
| GET | `/advisor/briefing/latest` | Yes | Full executive briefing (8 sections) |
| GET | `/advisor/briefing` | Yes | List of past briefings |
| GET | `/advisor/risks` | Yes | `{ org_id, predicted_risks[] }` |
| GET | `/advisor/opportunities` | Yes | `{ org_id, opportunities[] }` |

**Briefing response sections:** org health, predicted risks, knowledge lost, future critical areas, innovation opportunities, isolated departments, employees requiring transfer, business impact prediction.

---

### OCSIE — `/api/v1/ocsie` · Permission: `read:ocsie` / `write:ocsie`

| Method | Path | Auth | Permission | Response |
|--------|------|:---:|:---:|---|
| GET | `/ocsie/employee/{employee_id}/profile` | Yes | `read:ocsie` | Full Employee Knowledge DNA Profile |
| GET | `/ocsie/continuity-report/{employee_id}` | Yes | `read:ocsie` | 10-section Continuity Intelligence Report |
| POST | `/ocsie/transition/{employee_id}` | Yes | `write:ocsie` | `{ status, continuity_report_ready, continuity_report }` |
| GET | `/ocsie/unfinished-work/{employee_id}` | Yes | `read:ocsie` | `{ pending_approvals, open_prs, unanswered_emails, ...}` |
| GET | `/ocsie/successor-roadmap/{employee_id}` | Yes | `read:ocsie` | `{ week_1, week_2, week_3, estimated_full_competency_weeks }` |
| GET | `/ocsie/knowledge-gap/{from_id}/{to_id}` | Yes | `read:ocsie` | `{ gap_analysis: { identified_gaps[], training_recommendations[] } }` |
| GET | `/ocsie/business-impact/{employee_id}` | Yes | `read:ocsie` | `{ orphaned_knowledge_items, revenue_risk_estimate_usd, recovery_time_days, knowledge_loss_severity }` |

**POST /ocsie/transition query params:** `departure_date?` (ISO datetime), `reason` (string, default `"resignation"`)

---

### Organizational MRI — `/api/v1/mri` · Permission: `read:intelligence`

| Method | Path | Auth | Response |
|--------|------|:---:|---|
| GET | `/mri/brain-map` | Yes | `{ nodes[], edges[], summary{ total_nodes, green_nodes, yellow_nodes, red_nodes, overall_health_color }, legend }` |
| GET | `/mri/knowledge-flow` | Yes | `{ from_department, to_department, flow_strength, unique_contributors, health_status }[]` |
| GET | `/mri/bottlenecks` | Yes | `{ knowledge_id, title, domain, owner_ids[], risk_level, recommendation }[]` |
| GET | `/mri/dependencies` | Yes | Single-owner critical knowledge items |
| GET | `/mri/innovation-centers` | Yes | `{ center_id, title, domain, connection_strength, innovation_score, color }[]` |
| GET | `/mri/black-holes` | Yes | `{ knowledge_id, title, domain, created_at, risk, color: "red" }[]` |
| GET | `/mri/timeline-forecast` | Yes | `{ 3_month_forecast, 6_month_forecast, 12_month_forecast }` each with `{ date, projected_health_change, critical_risks[], required_actions[], confidence }` |

**Brain-map node shape:**
```
{
  id: string,
  label: string,
  type: "Person" | "Knowledge" | "Project" | "Department",
  connection_count: number,
  health_color: "green" | "yellow" | "red",
  health_score: number (0-100),
  tooltip: string
}
```

**Brain-map edge shape:**
```
{
  from: string,
  to: string,
  type: string,
  weight: number,
  display_weight: number (0.5-5.0)
}
```

---

### Root / Health

| Method | Path | Auth | Response |
|--------|------|:---:|---|
| GET | `/` | No | `{ name, version, tagline, status, layers: 13, docs }` |
| GET | `/health` | No | `{ status, app, version, environment }` |

---

## 2. TypeScript Interfaces

```typescript
// ─── Auth ─────────────────────────────────────────────────────────────────

export type UserRole = 'super_admin' | 'org_admin' | 'dept_admin' | 'analyst' | 'viewer';

export type Permission =
  | 'read:knowledge' | 'write:knowledge' | 'delete:knowledge'
  | 'read:graph' | 'write:graph'
  | 'read:intelligence'
  | 'run:simulation'
  | 'read:healing' | 'approve:healing'
  | 'read:ocsie' | 'write:ocsie'
  | 'manage:users' | 'manage:org'
  | 'view:board'
  | 'configure:integrations';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface CurrentUser {
  user_id: string;
  org_id: string;
  email: string;
  role: UserRole;
  permissions: Permission[];
}

export interface RegisterRequest {
  email: string;
  username: string;
  full_name: string;
  password: string;
  org_name: string;
  industry?: string;
}

// ─── Graph ────────────────────────────────────────────────────────────────

export type NodeType = 'Person' | 'Knowledge' | 'Project' | 'Department';
export type HealthColor = 'green' | 'yellow' | 'red';

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  connection_count: number;
  health_color: HealthColor;
  health_score: number;
  tooltip: string;
  [key: string]: unknown;
}

export interface GraphEdge {
  from: string;
  to: string;
  type: string;
  weight: number;
  display_weight: number;
}

export interface BrainMapSummary {
  total_nodes: number;
  total_connections: number;
  green_nodes: number;
  yellow_nodes: number;
  red_nodes: number;
  overall_health_color: HealthColor;
}

export interface BrainMapResponse {
  org_id: string;
  generated_at: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: BrainMapSummary;
  legend: Record<HealthColor, string>;
}

export interface CreatePersonRequest {
  user_id: string;
  name: string;
  email: string;
  department?: string;
  role?: string;
  expertise?: string[];
}

export interface CreateKnowledgeRequest {
  knowledge_id: string;
  title: string;
  domain: string;
  source_type?: string;
  summary?: string;
  tags?: string[];
}

export interface CreateRelationshipRequest {
  from_id: string;
  to_id: string;
  relationship_type: 'KNOWS' | 'CONTRIBUTES_TO' | 'COLLABORATES_WITH';
  properties?: Record<string, unknown>;
}

// ─── Decay Engine ─────────────────────────────────────────────────────────

export interface HalfLifeResult {
  knowledge_id: string;
  domain: string;
  half_life_days: number;
  current_relevance: number;
  relevance_percentage: number;
  days_until_critical: number | null;
  interpretation: 'Critical — immediate attention needed' | 'Warning — review within 30 days' | 'Healthy';
}

export interface DecayReport {
  org_id: string;
  report_type: 'knowledge_decay';
  summary: {
    isolated_items: number;
    single_owner_critical: number;
  };
  isolated_knowledge: GraphNode[];
  single_owner_critical: GraphNode[];
  recommendations: string[];
}

export interface EntropyReport {
  org_id: string;
  entropy_bits: number;
  domain_distribution: Array<{ domain: string; count: number }>;
}

// ─── Disease Detection ────────────────────────────────────────────────────

export type DiseaseType =
  | 'knowledge_cancer'
  | 'memory_alzheimers'
  | 'communication_stroke'
  | 'knowledge_obesity'
  | 'innovation_paralysis';

export type DiseaseSeverity = 'critical' | 'warning' | 'healthy';

export interface DiseaseResult {
  disease_type: DiseaseType;
  title: string;
  severity: DiseaseSeverity;
  severity_score: number;
  confidence: number;
  description: string;
  evidence: Record<string, unknown>;
  days_until_critical: number | null;
  recommended_action: string | null;
}

export interface DiseaseScanReport {
  scan_timestamp: string;
  org_id: string;
  overall_health_score: number;
  critical_diseases: number;
  warning_diseases: number;
  healthy_dimensions: number;
  diseases: Record<DiseaseType, DiseaseResult>;
}

export interface DiseaseTimeline {
  org_id: string;
  predictions: Record<DiseaseType, { days_until_critical: number | null; status: string }>;
}

// ─── Simulation ───────────────────────────────────────────────────────────

export type ScenarioType =
  | 'employee_departure'
  | 'mass_resignation'
  | 'department_closure'
  | 'project_delay'
  | 'system_failure';

export interface SimulationRequest {
  scenario_type: ScenarioType;
  parameters: Record<string, unknown>;
  description?: string;
}

export interface PredefinedScenario {
  id: string;
  name: string;
  scenario_type: ScenarioType;
  description: string;
  parameters: Record<string, unknown>;
}

export interface SimulationResult {
  simulation_id: string;
  scenario_type: ScenarioType;
  org_id: string;
  status: 'completed' | 'running' | 'failed';
  cascade_chain: unknown[];
  results: {
    knowledge_loss_percentage: number;
    affected_projects: unknown[];
    affected_customers: unknown[];
    orphaned_knowledge: unknown[];
    revenue_risk_usd: number;
    recovery_time_days: number;
    business_impact_summary: string;
  };
}

// ─── Self-Healing ─────────────────────────────────────────────────────────

export type HealingActionType =
  | 'create_sop' | 'assign_mentor' | 'schedule_training'
  | 'merge_docs' | 'archive_files' | 'notify_managers'
  | 'generate_onboarding' | 'create_quiz' | 'update_wiki' | 'knowledge_transfer';

export type HealingStatus = 'pending' | 'approved' | 'in_progress' | 'completed' | 'rejected' | 'cancelled';
export type HealingPriority = 'critical' | 'high' | 'medium' | 'low';

export interface HealingAction {
  id: string;
  action_type: HealingActionType;
  title: string;
  description: string;
  priority: HealingPriority;
  status: HealingStatus;
  estimated_impact: string | null;
  created_at: string;
}

// ─── Intelligence Index ───────────────────────────────────────────────────

export interface OIIDimensions {
  knowledge_velocity: number;
  knowledge_coverage: number;
  knowledge_quality: number;
  learning_agility: number;
  collaboration_density: number;
  innovation_index: number;
  decision_intelligence: number;
  cognitive_resilience: number;
  knowledge_accessibility: number;
  expertise_depth: number;
  knowledge_retention: number;
  adaptability_score: number;
}

export interface ProprietaryMetrics {
  knowledge_half_life_days: number;
  knowledge_entropy_bits: number;
  memory_compression_ratio: number;
}

export interface OIISnapshot {
  id: string;
  org_id: string;
  computed_at: string;
  overall_health: number;
  dimensions: OIIDimensions;
  proprietary_metrics: ProprietaryMetrics;
}

export interface OIITrends {
  trend: 'improving' | 'declining' | 'stable' | 'insufficient_data';
  current: number;
  delta_30d: number;
  history: Array<{ date: string; score: number }>;
}

// ─── Board Advisor ────────────────────────────────────────────────────────

export interface BoardBriefing {
  briefing_date: string;
  generated_for: string;
  org_id: string;
  executive_summary: {
    organization_health_score: string;
    health_trend: string;
    top_priority: string;
  };
  sections: {
    '1_organization_health': Record<string, unknown>;
    '2_predicted_risks': Array<{ risk: string; count: number; severity: string; action: string }>;
    '3_knowledge_lost_this_week': Record<string, unknown>;
    '4_future_critical_areas': string[];
    '5_innovation_opportunities': string[];
    '6_departments_becoming_isolated': unknown[];
    '7_employees_requiring_knowledge_transfer': Array<{
      employee_id: string | null;
      knowledge_at_risk: string;
      urgency: string;
    }>;
    '8_business_impact_prediction': Record<string, unknown>;
  };
}

// ─── OCSIE ────────────────────────────────────────────────────────────────

export interface KnowledgeDNA {
  knowledge_criticality_score: number;
  replacement_difficulty_score: number;
  knowledge_risk_score: number;
  primary_domains: string[];
  technical_expertise: Record<string, unknown>;
  business_expertise: Record<string, unknown>;
  decision_style: string | null;
  work_style: string | null;
  communication_style: string | null;
}

export interface EmployeeKnowledgeProfile {
  employee: {
    id: string;
    name: string;
    email: string;
    role: string | null;
    department_id: string | null;
  };
  knowledge_dna: KnowledgeDNA;
  work_profile: {
    critical_responsibilities: unknown[];
    active_projects: unknown[];
    collaboration_network: unknown[];
    customer_contacts: unknown[];
    vendor_contacts: unknown[];
    stakeholders: unknown[];
  };
  knowledge_inventory: {
    owned_knowledge: unknown[];
    orphaned_if_departs: unknown[];
    orphaned_count: number;
    hidden_knowledge: unknown[];
  };
  reasoning_profile: {
    reasoning_patterns: unknown[];
    decision_history_summary: string | null;
  };
  risk_assessment: {
    recommended_successors: unknown[];
    is_departure_initiated: boolean;
    departure_date: string | null;
  };
  last_computed_at: string | null;
}

export interface ContinuityReport {
  generated_at: string;
  employee_id: string;
  employee_name: string;
  report_type: 'continuity_intelligence_report';
  sections: {
    '1_employee_knowledge_dna': Record<string, unknown>;
    '2_active_projects': Record<string, unknown>;
    '3_unfinished_work': Record<string, unknown>;
    '4_how_this_person_thinks': Record<string, unknown>;
    '5_hidden_knowledge': Record<string, unknown>;
    '6_successor_roadmap': SuccessorRoadmap;
    '7_ai_mentor_mode': Record<string, unknown>;
    '8_knowledge_gap_analysis': Record<string, unknown>;
    '9_business_impact_prediction': Record<string, unknown>;
    '10_continuous_knowledge_backup': Record<string, unknown>;
  };
}

export interface SuccessorRoadmap {
  week_1: { focus: string; tasks: string[] };
  week_2: { focus: string; tasks: string[] };
  week_3: { focus: string; tasks: string[] };
  estimated_full_competency_weeks: number;
}

export interface BusinessImpact {
  employee_id: string;
  orphaned_knowledge_items: number;
  affected_projects: unknown[];
  revenue_risk_estimate_usd: number;
  recovery_time_days: number;
  knowledge_loss_severity: 'critical' | 'high' | 'medium' | 'low';
  immediate_actions: string[];
}

// ─── MRI ─────────────────────────────────────────────────────────────────

export interface KnowledgeFlow {
  from_department: string;
  to_department: string;
  flow_strength: number;
  unique_contributors: number;
  health_status: 'healthy' | 'warning' | 'critical';
}

export interface Bottleneck {
  knowledge_id: string;
  title: string;
  domain: string;
  owner_ids: string[];
  risk_level: 'critical';
  recommendation: string;
}

export interface InnovationCenter {
  center_id: string;
  title: string;
  domain: string;
  connection_strength: number;
  related_concepts: number;
  innovation_score: number;
  color: 'green';
}

export interface KnowledgeBlackHole {
  knowledge_id: string;
  title: string;
  domain: string;
  created_at: string;
  risk: string;
  color: 'red';
}

export interface ForecastPeriod {
  date: string;
  projected_health_change: string;
  critical_risks: string[];
  required_actions: string[];
  confidence: number;
}

export interface TimelineForecast {
  forecast_generated_at: string;
  org_id: string;
  note: string;
  '3_month_forecast': ForecastPeriod;
  '6_month_forecast': ForecastPeriod;
  '12_month_forecast': ForecastPeriod;
}

// ─── Generic API Wrapper ──────────────────────────────────────────────────

export interface APIError {
  error: string;
  message: string;
  details: unknown;
}

export interface PaginationParams {
  page: number;
  page_size: number;
}
```

---

## 3. Frontend Route Map

```
/                               → Landing / Login redirect
/auth/login                     → Login Page
/auth/register                  → Register New Organization
/auth/refresh                   → (silent) Token refresh handler

/dashboard                      → Main Dashboard (OII overview + disease alerts)
/dashboard/mri                  → Organizational MRI — Brain Map (signature page)
/dashboard/intelligence         → Intelligence Index — 12 dimensions radar
/dashboard/diseases             → Disease Control Panel — 5 diseases
/dashboard/decay                → Decay Engine — entropy, half-life explorer

/simulation                     → Simulation Hub
/simulation/scenarios           → Predefined Scenario Gallery
/simulation/run                 → Custom Simulation Builder
/simulation/:id                 → Simulation Result View

/healing                        → Self-Healing Dashboard
/healing/recommendations        → Recommendation List (filterable)
/healing/:id                    → Recommendation Detail + Approve/Reject

/ocsie                          → OCSIE Home — Employee Search
/ocsie/:employeeId              → Employee Knowledge DNA Profile
/ocsie/:employeeId/continuity   → 10-Section Continuity Report
/ocsie/:employeeId/roadmap      → Successor Roadmap
/ocsie/:employeeId/gap/:toId    → Knowledge Gap Analysis (compare two employees)
/ocsie/:employeeId/impact       → Business Impact Prediction
/ocsie/transition/:employeeId   → Initiate Departure Protocol

/board                          → AI Board Advisor
/board/briefing                 → Latest Executive Briefing
/board/risks                    → Predicted Risks Panel
/board/opportunities            → Innovation Opportunities

/graph                          → Memory Graph Explorer
/graph/search                   → Semantic Search
/graph/nodes                    → Node List + Filters
/graph/nodes/:id                → Node Profile (traverse from node)

/settings                       → Organization Settings
/settings/users                 → User Management (manage:users)
/settings/integrations          → Integrations (configure:integrations)
/settings/profile               → User Profile
```

---

## 4. State Management Plan

**Recommended:** React Query (TanStack Query) for server state + Zustand for client state

### Zustand Stores

#### `authStore`
```typescript
interface AuthStore {
  user: CurrentUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: CurrentUser) => void;
  logout: () => void;
  hasPermission: (permission: Permission) => boolean;
}
```

#### `orgStore`
```typescript
interface OrgStore {
  orgId: string | null;
  orgName: string | null;
  lastHealthScore: number | null;
  activeDiseaseCount: number;
  setOrg: (id: string, name: string) => void;
}
```

#### `mriStore`
```typescript
interface MRIStore {
  selectedNode: GraphNode | null;
  filterType: NodeType | null;
  showRedOnly: boolean;
  setSelectedNode: (node: GraphNode | null) => void;
  setFilter: (type: NodeType | null) => void;
}
```

#### `simulationStore`
```typescript
interface SimulationStore {
  lastResult: SimulationResult | null;
  isRunning: boolean;
  setResult: (r: SimulationResult) => void;
  setRunning: (v: boolean) => void;
}
```

### React Query Keys

```typescript
export const queryKeys = {
  auth: {
    me: ['auth', 'me'],
  },
  intelligence: {
    index: (orgId: string) => ['intelligence', 'index', orgId],
    history: (orgId: string, limit: number) => ['intelligence', 'history', orgId, limit],
    trends: (orgId: string) => ['intelligence', 'trends', orgId],
  },
  diseases: {
    scan: (orgId: string) => ['diseases', 'scan', orgId],
    timeline: (orgId: string) => ['diseases', 'timeline', orgId],
    single: (orgId: string, type: DiseaseType) => ['diseases', orgId, type],
  },
  mri: {
    brainMap: (orgId: string) => ['mri', 'brain-map', orgId],
    flow: (orgId: string) => ['mri', 'flow', orgId],
    bottlenecks: (orgId: string) => ['mri', 'bottlenecks', orgId],
    blackHoles: (orgId: string) => ['mri', 'black-holes', orgId],
    forecast: (orgId: string) => ['mri', 'forecast', orgId],
    innovationCenters: (orgId: string) => ['mri', 'innovation', orgId],
  },
  decay: {
    report: (orgId: string) => ['decay', 'report', orgId],
    entropy: (orgId: string) => ['decay', 'entropy', orgId],
    halfLife: (knowledgeId: string) => ['decay', 'half-life', knowledgeId],
    forgotten: (orgId: string, days: number) => ['decay', 'forgotten', orgId, days],
  },
  healing: {
    recommendations: (orgId: string, status?: string, priority?: string) =>
      ['healing', 'recommendations', orgId, status, priority],
  },
  simulation: {
    scenarios: ['simulation', 'scenarios'],
  },
  ocsie: {
    profile: (employeeId: string) => ['ocsie', 'profile', employeeId],
    report: (employeeId: string) => ['ocsie', 'report', employeeId],
    roadmap: (employeeId: string) => ['ocsie', 'roadmap', employeeId],
    impact: (employeeId: string) => ['ocsie', 'impact', employeeId],
    unfinished: (employeeId: string) => ['ocsie', 'unfinished', employeeId],
    gap: (fromId: string, toId: string) => ['ocsie', 'gap', fromId, toId],
  },
  board: {
    latestBriefing: (orgId: string) => ['board', 'briefing', 'latest', orgId],
    risks: (orgId: string) => ['board', 'risks', orgId],
    opportunities: (orgId: string) => ['board', 'opportunities', orgId],
  },
  graph: {
    nodes: (orgId: string, type?: NodeType) => ['graph', 'nodes', orgId, type],
    search: (orgId: string, q: string) => ['graph', 'search', orgId, q],
  },
} as const;
```

### Cache TTLs (staleTime / gcTime)

| Query | staleTime | gcTime | Notes |
|-------|-----------|--------|-------|
| OII Index | 5 min | 30 min | Background refreshed daily |
| Disease Scan | 10 min | 1 hr | Expensive scan |
| MRI Brain Map | 5 min | 30 min | Color-coded graph |
| OCSIE Profile | 2 min | 15 min | Changes daily via worker |
| Board Briefing | 1 hr | 6 hr | Generated weekly |
| Simulation Result | ∞ (immutable) | 24 hr | Results never change |
| Healing Recs | 1 min | 10 min | User may approve/reject |
| Auth/me | 5 min | 30 min | Token refresh handles expiry |

---

## 5. UI Component Hierarchy

```
<App>
├── <AuthProvider>             — Zustand auth store + token refresh loop
├── <QueryClientProvider>      — TanStack Query
│
├── <PublicRoutes>
│   ├── <LoginPage>
│   │   ├── <LoginForm>
│   │   └── <OAuthButtons> (future)
│   └── <RegisterPage>
│       └── <RegisterForm>
│
└── <ProtectedRoutes>          — requires isAuthenticated
    ├── <AppShell>
    │   ├── <TopNav>
    │   │   ├── <OrgHealthBadge>     — live overall_health pulse
    │   │   ├── <AlertsBell>         — disease count badge
    │   │   └── <UserMenu>
    │   ├── <Sidebar>
    │   │   ├── <NavSection label="Intelligence">
    │   │   │   ├── <NavItem> Dashboard
    │   │   │   ├── <NavItem> MRI Brain Map
    │   │   │   ├── <NavItem> Intelligence Index
    │   │   │   └── <NavItem> Disease Panel
    │   │   ├── <NavSection label="People">
    │   │   │   └── <NavItem> OCSIE
    │   │   ├── <NavSection label="Actions">
    │   │   │   ├── <NavItem> Simulations
    │   │   │   └── <NavItem> Self-Healing
    │   │   ├── <NavSection label="Board">
    │   │   │   └── <NavItem> Board Advisor
    │   │   └── <NavSection label="Data">
    │   │       ├── <NavItem> Memory Graph
    │   │       └── <NavItem> Decay Engine
    │   │
    │   └── <PageOutlet>       — routed pages render here
    │
    ├── <DashboardPage>
    │   ├── <OIIHealthGauge>          — circular gauge 0-100%
    │   ├── <DiseaseAlertStrip>       — 5 disease pills (green/yellow/red)
    │   ├── <OIIRadarChart>           — 12-dimension radar
    │   ├── <ProprietaryMetricsRow>   — 3 cards: half-life, entropy, compression
    │   ├── <MRIPreviewCard>          — mini brain map + "View Full MRI" CTA
    │   ├── <HealingActionsPreview>   — top 3 pending recommendations
    │   └── <BoardBriefingTeaser>     — latest briefing snippet
    │
    ├── <MRIPage>
    │   ├── <BrainMapHeader>          — summary pill counts (green/yellow/red)
    │   ├── <BrainMapCanvas>          — force-directed graph (react-force-graph or sigma.js)
    │   │   ├── <NodeTooltip>
    │   │   └── <EdgeLabel>
    │   ├── <BrainMapControls>        — filter by node type, color, zoom
    │   ├── <KnowledgeFlowPanel>      — department-to-department flow table
    │   ├── <BottlenecksTable>
    │   ├── <BlackHolesTable>
    │   ├── <InnovationCentersGrid>
    │   └── <TimelineForecastCard>    — 3/6/12 month accordion
    │
    ├── <IntelligencePage>
    │   ├── <OIIScoreHeader>
    │   ├── <DimensionRadarChart>     — all 12 dimensions
    │   ├── <DimensionTable>          — sortable dimension breakdown
    │   ├── <TrendLineChart>          — overall_health over time
    │   └── <ProprietaryMetricsPanel>
    │
    ├── <DiseasePage>
    │   ├── <DiseaseScanHeader>       — overall_health_score + scan button
    │   ├── <DiseaseGrid>             — 5 disease cards in 2-3 col grid
    │   │   └── <DiseaseCard>         — severity badge, score bar, evidence, CTA
    │   ├── <DiseaseTimelineChart>    — days_until_critical per disease
    │   └── <DiseaseDetailDrawer>     — slide-out: evidence detail + recommended action
    │
    ├── <DecayPage>
    │   ├── <EntropyGauge>
    │   ├── <HalfLifeExplorer>        — knowledge item selector + half-life calculator
    │   ├── <ForgottenKnowledgeTable>
    │   ├── <IsolatedKnowledgeTable>
    │   └── <ConflictsTable>
    │
    ├── <SimulationPage>
    │   ├── <ScenarioGallery>         — 4 predefined scenario cards
    │   ├── <CustomScenarioBuilder>   — scenario type select + params form
    │   ├── <RunSimulationButton>     — triggers POST /simulation/run
    │   └── <SimulationResultView>
    │       ├── <CascadeChainTimeline>
    │       ├── <BusinessImpactSummaryCard>
    │       ├── <AffectedProjectsList>
    │       └── <RecoveryMetrics>
    │
    ├── <HealingPage>
    │   ├── <HealingStatsBar>         — count by status
    │   ├── <GenerateButton>          — POST /healing/generate
    │   ├── <RecommendationFilters>   — status + priority filters
    │   └── <RecommendationList>
    │       └── <RecommendationCard>
    │           ├── <PriorityBadge>
    │           ├── <StatusBadge>
    │           ├── <ApproveButton>   — approve:healing permission guard
    │           └── <RejectButton>
    │
    ├── <OCSIEPage>
    │   ├── <EmployeeSearch>          — search by name/email
    │   └── <EmployeeProfileView>     — loads on employee select
    │       ├── <KnowledgeDNACard>    — criticality, risk scores, domains
    │       ├── <WorkProfileCard>     — projects, collaborators
    │       ├── <RiskScoreCard>       — orphaned count, revenue risk
    │       ├── <SuccessorRoadmapCard>
    │       ├── <ContinuityReportButton>
    │       └── <InitiateDepartureButton> — write:ocsie guard
    │
    ├── <ContinuityReportPage>
    │   └── <ReportSectionAccordion>  — renders all 10 sections expandable
    │
    ├── <BoardAdvisorPage>
    │   ├── <BriefingHeader>          — date + org health score
    │   ├── <ExecutiveSummaryBanner>
    │   └── <BriefingSections>        — 8 sections as collapsible panels
    │
    └── <GraphPage>
        ├── <GraphSearchBar>
        ├── <NodeTypeFilter>
        ├── <NodeList>
        └── <TraverseViewer>          — expand from selected node
```

---

## 6. Data Flow Diagram

```
Browser
│
│  1. On load → authStore checks localStorage for tokens
│  2. If tokens exist → GET /auth/me → populate authStore + orgStore
│  3. If 401 → POST /auth/refresh → new tokens stored → retry
│  4. If refresh fails → redirect to /auth/login
│
├─ Login Flow
│   POST /auth/login ──► TokenResponse
│   └─► authStore.setTokens() + authStore.setUser()
│       └─► GET /auth/me ──► CurrentUser
│
├─ Dashboard Page
│   ├─ GET /intelligence/index ──► OIISnapshot ──► OIIHealthGauge + RadarChart
│   ├─ GET /diseases/scan ──► DiseaseScanReport ──► DiseaseAlertStrip
│   ├─ GET /mri/brain-map ──► BrainMapResponse ──► MRIPreviewCard
│   └─ GET /healing/recommendations?status=pending ──► HealingActionsPreview
│
├─ MRI Page (data-intensive)
│   ├─ GET /mri/brain-map ──► BrainMapCanvas (nodes + edges → graph renderer)
│   ├─ GET /mri/knowledge-flow ──► KnowledgeFlowPanel
│   ├─ GET /mri/bottlenecks ──► BottlenecksTable
│   ├─ GET /mri/black-holes ──► BlackHolesTable
│   ├─ GET /mri/innovation-centers ──► InnovationCentersGrid
│   └─ GET /mri/timeline-forecast ──► TimelineForecastCard
│
├─ OCSIE Page
│   ├─ User selects employee
│   ├─ GET /ocsie/employee/{id}/profile ──► EmployeeKnowledgeProfile
│   ├─ GET /ocsie/business-impact/{id} ──► BusinessImpact
│   └─ On "View Continuity Report":
│       └─ GET /ocsie/continuity-report/{id} ──► ContinuityReport (10 sections)
│
├─ Simulation Page
│   ├─ GET /simulation/scenarios ──► ScenarioGallery (static, cached long)
│   └─ User runs scenario:
│       POST /simulation/run ──► SimulationResult
│       └─► simulationStore.setResult()
│           └─► SimulationResultView renders cascade chain
│
├─ Healing Page
│   ├─ GET /healing/recommendations ──► RecommendationList
│   ├─ POST /healing/generate ──► generates new recs → invalidate cache
│   ├─ POST /healing/recommendations/{id}/approve ──► invalidate cache
│   └─ POST /healing/recommendations/{id}/reject ──► invalidate cache
│
└─ Token Refresh Loop (background)
    Every 25 min (before 30 min expiry):
    POST /auth/refresh ──► new access token ──► authStore.setTokens()
```

---

## 7. Authentication Flow

### Token Storage
- `access_token` → `sessionStorage` (cleared on tab close, XSS-safer than localStorage for short-lived tokens)
- `refresh_token` → `localStorage` (persists across sessions, 7-day TTL)
- `user` object → `sessionStorage` (cached from `/auth/me`)

### Interceptor Setup (Axios / Fetch wrapper)

```typescript
// Every request:
// 1. Attach Authorization: Bearer {access_token}
// 2. On 401 response:
//    a. Call POST /auth/refresh with refresh_token
//    b. If success → store new tokens → retry original request (once)
//    c. If refresh also 401 → clear all tokens → redirect /auth/login
```

### Route Guards

```typescript
// ProtectedRoute wrapper:
// - if !isAuthenticated → redirect /auth/login
// - if authenticated but lacks required permission → show 403 page

// Usage:
<ProtectedRoute permission="view:board">
  <BoardAdvisorPage />
</ProtectedRoute>

<ProtectedRoute permission="run:simulation">
  <SimulationPage />
</ProtectedRoute>
```

### Role → Page Access Matrix

| Page | viewer | analyst | dept_admin | org_admin | super_admin |
|------|:------:|:-------:|:----------:|:---------:|:-----------:|
| Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ |
| MRI Brain Map | ✓ | ✓ | ✓ | ✓ | ✓ |
| Intelligence Index | ✓ | ✓ | ✓ | ✓ | ✓ |
| Disease Panel | ✓ | ✓ | ✓ | ✓ | ✓ |
| Simulation | — | ✓ | ✓ | ✓ | ✓ |
| Healing (view) | — | ✓ | ✓ | ✓ | ✓ |
| Healing (approve) | — | — | ✓ | ✓ | ✓ |
| OCSIE (view) | — | ✓ | ✓ | ✓ | ✓ |
| OCSIE (initiate departure) | — | — | — | ✓ | ✓ |
| Board Advisor | — | — | ✓ | ✓ | ✓ |
| Graph (read) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Graph (write) | — | — | ✓ | ✓ | ✓ |
| Settings / Users | — | — | — | ✓ | ✓ |

---

## 8. Error Handling Strategy

### API Error Shape

```typescript
interface APIError {
  error: string;      // error code: "AUTHENTICATION_ERROR" | "FORBIDDEN" | "NOT_FOUND" | "CONFLICT" | "VALIDATION_ERROR"
  message: string;    // human-readable
  details: unknown;   // field-level errors for validation
}
```

### HTTP Status → UI Behavior

| Status | Error Code | UI Action |
|--------|-----------|-----------|
| 400 | `VALIDATION_ERROR` | Inline form field errors |
| 401 | `AUTHENTICATION_ERROR` | Clear tokens → redirect `/auth/login` |
| 403 | `FORBIDDEN` | Show 403 page with role explanation |
| 404 | `NOT_FOUND` | Show inline "Not found" empty state |
| 409 | `CONFLICT` | Toast: "This item already exists" |
| 422 | `VALIDATION_ERROR` | Map `details[]` to form field errors |
| 429 | (rate limit) | Toast: "Too many requests, try again in X seconds" |
| 500 | — | Toast: "Something went wrong. Try again." + Sentry capture |
| Network error | — | Toast: "Unable to connect. Check your connection." |

### React Query Error Handling

```typescript
// Global error handler in QueryClient:
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: APIError) => {
        // Never retry auth errors or not-found — retry network errors up to 2x
        if (error.error === 'AUTHENTICATION_ERROR') return false;
        if (error.error === 'NOT_FOUND') return false;
        return failureCount < 2;
      },
      onError: (error: APIError) => {
        if (error.error === 'AUTHENTICATION_ERROR') {
          authStore.getState().logout();
          router.push('/auth/login');
        }
      },
    },
    mutations: {
      onError: (error: APIError) => toast.error(error.message),
    },
  },
});
```

### Loading States

Every data-dependent page must show:
- **Skeleton loaders** while queries are in `isLoading` state
- **Error banners** with a Retry button when queries are in `isError` state  
- **Empty states** with descriptive text when data is `[]` / null (e.g. "No OII data yet. Run the intelligence computation first.")

### Optimistic Updates

Apply optimistic updates on:
- Healing approve/reject — immediately flip status in cache, rollback on error
- Graph node creation — add node to graph instantly, rollback on 4xx

### Permission-Gated Actions

Wrap all write-action buttons with a `<PermissionGuard>` component:
```typescript
// Renders children only if current user has the required permission
// Otherwise renders disabled button with tooltip explaining the missing role
<PermissionGuard permission="approve:healing" fallback={<DisabledButton reason="Requires dept_admin or above" />}>
  <ApproveButton />
</PermissionGuard>
```

---

## Implementation Notes

### Recommended Tech Stack

| Layer | Library | Reason |
|-------|---------|--------|
| Framework | React 18 + Vite | Fast dev, optimal for SPA |
| Routing | React Router v6 | Nested routes, lazy loading |
| State | Zustand + TanStack Query v5 | Server vs client state separation |
| UI | shadcn/ui + Tailwind CSS | Accessible, headless, dark mode |
| Graph Viz | `react-force-graph-2d` or `@react-sigma/core` | MRI brain map rendering |
| Charts | Recharts or Nivo | OII radar, trend lines, disease bars |
| HTTP | Axios with interceptors | Token refresh, error normalization |
| Auth | Custom hooks over Zustand | No external auth library needed |
| Forms | React Hook Form + Zod | Matches Pydantic v2 validation |
| Notifications | Sonner (toast) | Lightweight, stackable |

### Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_PREFIX=/api/v1
VITE_TOKEN_REFRESH_INTERVAL_MS=1500000  # 25 min
```

### CORS

Backend already allows: `http://localhost:3000`, `http://localhost:8080`  
Set Vite dev server port to `3000` or add `http://localhost:5173` to backend `ALLOWED_ORIGINS`.

### No WebSocket / No File Upload

The current backend has **no WebSocket endpoints** and **no file upload API endpoints** exposed through the routers (document processing runs via the `DocumentProcessor` integration internally). These are not required in the initial frontend.

### Background Jobs (Celery)

Workers run server-side only; no frontend integration needed. However, the UI should communicate:
- "Intelligence scores are updated daily at midnight UTC"
- "Disease scans run every 6 hours automatically"
- "Board briefing is generated every Monday 8am UTC"

---

*Specification generated: 2026-07-06 | Backend: AION v1.0.0 | 46 endpoints across 10 modules*
