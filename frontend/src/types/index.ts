// ─── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole = "super_admin" | "org_admin" | "dept_admin" | "analyst" | "viewer";

export type Permission =
  | "read:knowledge" | "write:knowledge" | "delete:knowledge"
  | "read:graph" | "write:graph"
  | "read:intelligence"
  | "run:simulation"
  | "read:healing" | "approve:healing"
  | "read:ocsie" | "write:ocsie"
  | "manage:users" | "manage:org"
  | "view:board"
  | "configure:integrations";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
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

export interface LoginRequest {
  username: string;
  password: string;
}

// ─── Graph / MRI ──────────────────────────────────────────────────────────────

export type NodeType = "Person" | "Knowledge" | "Project" | "Department";
export type HealthColor = "green" | "yellow" | "red";

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
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

export interface CreatePersonRequest {
  employee_id: string;
  name: string;
  department?: string;
  role?: string;
}

export interface CreateKnowledgeRequest {
  title: string;
  domain: string;
  owner_id: string;
  description?: string;
  tags?: string[];
}

export interface CreateRelationshipRequest {
  from_node_id: string;
  to_node_id: string;
  relationship_type: string;
  weight?: number;
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

export interface KnowledgeFlow {
  from_department: string;
  to_department: string;
  flow_strength: number;
  unique_contributors: number;
  health_status: "healthy" | "warning" | "critical";
}

export interface Bottleneck {
  knowledge_id: string;
  title: string;
  domain: string;
  owner_ids: string[];
  risk_level: "critical";
  recommendation: string;
}

export interface InnovationCenter {
  center_id: string;
  title: string;
  domain: string;
  connection_strength: number;
  related_concepts: number;
  innovation_score: number;
  color: "green";
}

export interface KnowledgeBlackHole {
  knowledge_id: string;
  title: string;
  domain: string;
  created_at: string;
  risk: string;
  color: "red";
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
  "3_month_forecast": ForecastPeriod;
  "6_month_forecast": ForecastPeriod;
  "12_month_forecast": ForecastPeriod;
}

// ─── Knowledge Decay ──────────────────────────────────────────────────────────

export interface HalfLifeResult {
  knowledge_id: string;
  domain: string;
  half_life_days: number;
  current_relevance: number;
  relevance_percentage: number;
  days_until_critical: number | null;
  interpretation: string;
}

export interface DecayReport {
  org_id: string;
  report_type: string;
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
  domain_entropy_bits: number;
  department_entropy_bits: number;
  normalized_domain_entropy: number;
  normalized_department_entropy: number;
  duplication_entropy: number;
  isolation_ratio: number;
  ownership_entropy_bits: number;
  composite_entropy_score: number;
  health_interpretation: string;
  domain_distribution: Record<string, number>;
  total_knowledge_items: number;
  isolated_items: number;
}

export interface ForgottenKnowledgeResponse {
  threshold_days: number;
  forgotten_items: GraphNode[];
  count: number;
}

// ─── Disease Detection ────────────────────────────────────────────────────────

export type DiseaseType =
  | "knowledge_cancer"
  | "memory_alzheimers"
  | "communication_stroke"
  | "knowledge_obesity"
  | "innovation_paralysis";

export type DiseaseSeverity = "critical" | "warning" | "healthy";

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

// ─── Simulation ───────────────────────────────────────────────────────────────

export type ScenarioType =
  | "employee_departure"
  | "mass_resignation"
  | "department_closure"
  | "project_delay"
  | "system_failure";

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
  status: "completed" | "running" | "failed";
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

// ─── Self-Healing ─────────────────────────────────────────────────────────────

export type HealingActionType =
  | "create_sop" | "assign_mentor" | "schedule_training"
  | "merge_docs" | "archive_files" | "notify_managers"
  | "generate_onboarding" | "create_quiz" | "update_wiki" | "knowledge_transfer";

export type HealingStatus = "pending" | "approved" | "in_progress" | "completed" | "rejected" | "cancelled";
export type HealingPriority = "critical" | "high" | "medium" | "low";

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

// ─── Intelligence Index ───────────────────────────────────────────────────────

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
  trend: "improving" | "declining" | "stable" | "insufficient_data";
  current: number;
  delta_30d: number;
  history: Array<{ date: string; score: number }>;
}

// ─── Board Advisor ────────────────────────────────────────────────────────────

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
    "1_organization_health": Record<string, unknown>;
    "2_predicted_risks": Array<{ risk: string; count: number; severity: string; action: string }>;
    "3_knowledge_lost_this_week": Record<string, unknown>;
    "4_future_critical_areas": string[];
    "5_innovation_opportunities": string[];
    "6_departments_becoming_isolated": unknown[];
    "7_employees_requiring_knowledge_transfer": Array<{
      employee_id: string | null;
      knowledge_at_risk: string;
      urgency: string;
    }>;
    "8_business_impact_prediction": Record<string, unknown>;
  };
}

// ─── OCSIE ────────────────────────────────────────────────────────────────────

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
  knowledge_loss_severity: "critical" | "high" | "medium" | "low";
  immediate_actions: string[];
}

export interface ContinuityReport {
  generated_at: string;
  employee_id: string;
  employee_name: string;
  report_type: string;
  sections: Record<string, unknown>;
}

// ─── API Error ────────────────────────────────────────────────────────────────

export interface APIError {
  error: string;
  message: string;
  details: unknown;
}

export interface PaginationParams {
  page: number;
  page_size: number;
}

// ─── UI State ─────────────────────────────────────────────────────────────────

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  permission?: Permission;
  badge?: string | number;
}
