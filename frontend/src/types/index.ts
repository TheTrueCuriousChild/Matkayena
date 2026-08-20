// ─── Enums ───────────────────────────────────────────────────────────────────

export enum RoleEnum {
  RM = 'RM',
  TEAM_LEAD = 'TEAM_LEAD',
  MANAGER = 'MANAGER',
  REGIONAL_MANAGER = 'REGIONAL_MANAGER',
  ADMIN = 'ADMIN',
  SYSTEM_SERVICE = 'SYSTEM_SERVICE',
}

export enum OpportunityType {
  CROSS_SELL = 'CROSS_SELL',
  UPSELL = 'UPSELL',
  DORMANT_REACTIVATION = 'DORMANT_REACTIVATION',
  HIGH_INTENT_LEAD = 'HIGH_INTENT_LEAD',
  PRODUCT_GAP = 'PRODUCT_GAP',
  OPPORTUNITY_AT_RISK = 'OPPORTUNITY_AT_RISK',
}

export enum OpportunityStatus {
  DETECTED = 'DETECTED',
  ASSIGNED = 'ASSIGNED',
  CONTACT_PENDING = 'CONTACT_PENDING',
  CONTACTED = 'CONTACTED',
  INTERESTED = 'INTERESTED',
  CONVERTED = 'CONVERTED',
  LOST = 'LOST',
}

export enum ActionStatus {
  PROPOSED = 'PROPOSED',
  VALIDATED = 'VALIDATED',
  ASSIGNED = 'ASSIGNED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  SNOOZED = 'SNOOZED',
  REASSIGNED = 'REASSIGNED',
  FAILED = 'FAILED',
  EXPIRED = 'EXPIRED',
  REJECTED = 'REJECTED',
}

export enum ActionOutcomeType {
  CONVERTED = 'CONVERTED',
  INTERESTED_FOLLOWUP = 'INTERESTED_FOLLOWUP',
  REJECTED = 'REJECTED',
  NOT_REACHABLE = 'NOT_REACHABLE',
}

export enum AlertType {
  MANAGER_ALERT = 'MANAGER_ALERT',
  ESCALATION = 'ESCALATION',
  ACHIEVEMENT = 'ACHIEVEMENT',
  COACHING_RECOMMENDATION = 'COACHING_RECOMMENDATION',
  OPPORTUNITY_RISK = 'OPPORTUNITY_RISK',
}

export enum Severity {
  INFO = 'INFO',
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password?: string;
  roles?: string[];
}

export interface LoginResponse {
  user_id: string;
  full_name: string;
  email: string;
  roles: string[];
  manager_id: string | null;
  org_unit_id: string | null;
  access_token: string;
  token_type: string;
  message: string;
}

export interface User {
  user_id: string;
  email: string;
  roles: string[];
  org_unit_id: string | null;
  full_name: string;
  manager_id: string | null;
  is_active: boolean;
}

// ─── CRM Core ────────────────────────────────────────────────────────────────

export interface Customer {
  id: string;
  customer_code: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  segment: string;
  city: string | null;
  potential_value: number;
  rm_id: string | null;
  lifecycle_status: string;
  last_contact_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  code: string;
  name: string;
  category: string;
  description: string | null;
  is_active: boolean;
}

export interface CustomerProduct {
  id: string;
  customer_id: string;
  product_id: string;
  status: string;
  relationship_value: number;
  acquired_on: string | null;
  closed_on: string | null;
}

export interface Lead {
  id: string;
  lead_code: string | null;
  customer_id: string | null;
  rm_id: string | null;
  source: string | null;
  stage: string;
  status: string;
  potential_value: number;
  priority: string;
  created_at: string;
  last_contact_at: string | null;
  next_followup_at: string | null;
  converted_at: string | null;
}

export interface Transaction {
  id: string;
  customer_id: string;
  lead_id: string | null;
  rm_id: string | null;
  product_id: string | null;
  transaction_type: string;
  amount: number;
  currency: string;
  status: string;
  transaction_at: string;
}

export interface Interaction {
  id: string;
  customer_id: string;
  lead_id: string | null;
  rm_id: string | null;
  interaction_type: string;
  outcome: string | null;
  notes: string | null;
  occurred_at: string;
  next_followup_at: string | null;
}

export interface Customer360Response {
  customer: Customer;
  holdings: CustomerProduct[];
  recent_transactions: Transaction[];
  recent_interactions: Interaction[];
  active_leads: Lead[];
}

// ─── Intelligence ────────────────────────────────────────────────────────────

export interface Opportunity {
  id: string;
  customer_id: string;
  lead_id: string | null;
  rm_id: string | null;
  product_id: string | null;
  source_event_id: string | null;
  source_rule_id: string | null;
  opportunity_type: string;
  status: string;
  potential_value: number;
  score: number;
  reason: string | null;
  detected_at: string;
  expires_at: string | null;
  converted_at: string | null;
  created_at: string;
  updated_at: string;
  // Computed properties from backend
  title?: string;
  priority?: string;
  recommended_action?: string;
  reason_codes?: string[];
  evidence?: Record<string, unknown>;
  correlation_id?: string;
}

// ─── Actions ─────────────────────────────────────────────────────────────────

export interface Action {
  id: string;
  customer_id: string;
  lead_id: string | null;
  rm_id: string;
  opportunity_id: string | null;
  action_type: string;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  due_date: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ActionOutcome {
  id: string;
  action_id: string;
  outcome_type: string;
  converted_product_id: string | null;
  converted_value: number;
  commission_eligible: boolean;
  notes: string | null;
  recorded_at: string;
}

export interface ActionHistory {
  id: string;
  action_id: string;
  from_status: string | null;
  to_status: string;
  changed_by_id: string | null;
  reason: string | null;
  created_at: string;
}

export interface ActionDetailResponse {
  action: Action;
  outcome: ActionOutcome | null;
  history: ActionHistory[];
}

export interface CompleteActionRequest {
  outcome_type: string;
  notes?: string;
  converted_product_id?: string;
  converted_value?: number;
  commission_eligible?: boolean;
}

export interface SnoozeActionRequest {
  snooze_until?: string;
  reason: string;
}

export interface ReassignActionRequest {
  new_rm_id: string;
  reason?: string;
}

export interface CompleteActionResponse {
  success: boolean;
  action_id: string;
  status: string;
  outcome: ActionOutcome;
  commission: CommissionResult | null;
}

export interface CommissionResult {
  rm_id: string;
  converted_value: number;
  base_rate: number;
  segment_multiplier: number;
  final_rate: number;
  commission_amount: number;
  is_eligible: boolean;
  rule_version: string;
  calculated_at: string;
}

// ─── Performance ─────────────────────────────────────────────────────────────

export interface PerformanceSnapshot {
  success: boolean;
  rm_id: string;
  period: string;
  snapshot: {
    rm_id: string;
    period: string;
    target: number;
    achievement: number;
    achievement_percent: number;
    expected_run_rate: number;
    conversion_rate: number;
    activity_count: number;
    overdue_actions: number;
    pipeline_value: number;
    sla_breaches: number;
    sla_score: number;
    productivity: number;
    benchmark_delta: number;
    status: string;
    primary_drivers: string[];
    secondary_drivers: string[];
    recommended_intervention: string;
    snapshot_at: string;
  };
}

export interface Achievement {
  id: string;
  rm_id: string;
  achievement_type: string;
  title: string;
  description: string | null;
  period: string | null;
  milestone_value: number;
  metadata_json: Record<string, unknown> | null;
  awarded_at: string;
  created_at: string;
}

// ─── Manager ─────────────────────────────────────────────────────────────────

export interface ManagerAlert {
  alert_id: string;
  manager_id: string | null;
  rm_id: string;
  alert_type: string;
  severity: string;
  title: string;
  summary: string;
  evidence: Record<string, unknown>;
  impact: string;
  recommended_action: string;
  status: string;
  created_at: string;
  correlation_id: string;
}

// ─── Audit ───────────────────────────────────────────────────────────────────

export interface AuditRecord {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string | null;
  previous_hash: string;
  current_hash: string;
  payload_hash: string;
  correlation_id: string;
  causation_id: string | null;
  created_at: string;
  blockchain_status: string | null;
  tx_hash: string | null;
}

export interface AuditVerifyResult {
  record_id: string;
  is_valid: boolean;
  payload_hash_match: boolean;
  node_hash_match: boolean;
  message: string;
}

export interface ChainVerifyResult {
  is_valid: boolean;
  total_records: number;
  verified_records: number;
  broken_at: string | null;
  message: string;
}

// ─── API Error ───────────────────────────────────────────────────────────────

export interface ApiError {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
  correlation_id?: string;
}
