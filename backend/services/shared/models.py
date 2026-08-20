"""SQLAlchemy Declarative Models mapped exactly to the 27-table PostgreSQL / Supabase Schema."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (

    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Numeric
)
from sqlalchemy.orm import relationship, synonym
from backend.services.shared.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================================
# 1. IDENTITY & ORGANIZATION (4 Tables)
# ============================================================================

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class OrgUnit(Base):
    __tablename__ = "org_units"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    parent_id = Column(String(64), nullable=True)
    unit_type = Column(String(64), nullable=True)  # BRANCH, REGION, TEAM, DIVISION
    name = Column(String(128), nullable=False)
    code = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    employee_code = Column(String(64), nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(32), nullable=True)
    manager_id = Column(String(64), nullable=True)
    org_unit_id = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(String(64), primary_key=True)
    role_id = Column(String(64), primary_key=True)


# ============================================================================
# 2. CRM CORE (6 Tables)
# ============================================================================

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_code = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(32), nullable=True)
    segment = Column(String(64), nullable=False, default="RETAIL")
    city = Column(String(128), nullable=True)
    potential_value = Column(Float, default=0.0)
    rm_id = Column(String(64), nullable=True, index=True)
    lifecycle_status = Column(String(64), default="ACTIVE")
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    # Column synonyms for SQL queries
    primary_rm_id = synonym("rm_id")
    relationship_value = synonym("potential_value")
    status = synonym("lifecycle_status")

    @property
    def first_name(self) -> str:
        return self.full_name.split()[0] if self.full_name else ""

    @first_name.setter
    def first_name(self, val: str):
        ln = getattr(self, "_last_name", "") or (self.full_name.split()[1] if self.full_name and len(self.full_name.split()) > 1 else "")
        self._first_name = val
        self.full_name = f"{val} {ln}".strip()

    @property
    def last_name(self) -> str:
        parts = self.full_name.split() if self.full_name else []
        return getattr(self, "_last_name", "") or (" ".join(parts[1:]) if len(parts) > 1 else "")

    @last_name.setter
    def last_name(self, val: str):
        fn = getattr(self, "_first_name", "") or (self.full_name.split()[0] if self.full_name else "")
        self._last_name = val
        self.full_name = f"{fn} {val}".strip()

    @property
    def region(self) -> str:
        return getattr(self, "_region", "WEST")

    @region.setter
    def region(self, val: str):
        self._region = val


class Product(Base):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    @property
    def base_commission_rate(self) -> float:
        rates = {"INSURANCE": 0.05, "MUTUAL_FUND": 0.015, "EQUITY": 0.010, "LOAN": 0.012}
        return getattr(self, "_base_commission_rate", None) or rates.get(self.category, 0.02)

    @base_commission_rate.setter
    def base_commission_rate(self, val: float):
        self._base_commission_rate = float(val)


class CustomerProduct(Base):
    __tablename__ = "customer_products"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), nullable=False, index=True)
    product_id = Column(String(64), nullable=False, index=True)
    status = Column(String(64), default="ACTIVE")
    relationship_value = Column(Float, default=0.0)
    acquired_on = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    closed_on = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    holding_value = synonym("relationship_value")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    lead_code = Column(String(64), unique=True, nullable=True)
    customer_id = Column(String(64), nullable=True, index=True)
    rm_id = Column(String(64), nullable=True, index=True)
    source = Column(String(64), nullable=True)
    stage = Column(String(64), default="NEW")
    status = Column(String(64), default="OPEN")
    potential_value = Column(Float, default=0.0)
    priority = Column(String(32), default="MEDIUM")
    created_at = Column(DateTime(timezone=True), default=now_utc)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    next_followup_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    assigned_rm_id = synonym("rm_id")
    title = synonym("lead_code")
    estimated_value = synonym("potential_value")




class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), nullable=False, index=True)
    lead_id = Column(String(64), nullable=True)
    rm_id = Column(String(64), nullable=True, index=True)
    interaction_type = Column(String(64), nullable=False)
    outcome = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=now_utc)
    next_followup_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), nullable=False, index=True)
    lead_id = Column(String(64), nullable=True)
    rm_id = Column(String(64), nullable=True, index=True)
    product_id = Column(String(64), nullable=True)
    transaction_type = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(16), default="INR")
    status = Column(String(64), default="COMPLETED")
    transaction_at = Column(DateTime(timezone=True), default=now_utc)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Synonym for occurred_at
    occurred_at = synonym("transaction_at")


# ============================================================================
# 3. EVENT PROCESSING (3 Tables)
# ============================================================================

class EventType(Base):
    __tablename__ = "event_types"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class BusinessEvent(Base):
    __tablename__ = "business_events"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    event_type_id = Column(String(64), nullable=True)
    event_key = Column(String(128), unique=True, nullable=True, index=True)
    customer_id = Column(String(64), nullable=True, index=True)
    lead_id = Column(String(64), nullable=True)
    rm_id = Column(String(64), nullable=True)
    transaction_id = Column(String(64), nullable=True)
    payload = Column(JSON, default=dict)
    source = Column(String(64), default="api")
    occurred_at = Column(DateTime(timezone=True), default=now_utc)
    received_at = Column(DateTime(timezone=True), default=now_utc)
    processing_status = Column(String(64), default="PENDING")
    retry_count = Column(Integer, default=0)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    idempotency_key = synonym("event_key")
    status = synonym("processing_status")

    @property
    def event_type(self) -> str:
        if isinstance(self.payload, dict):
            return self.payload.get("event_type", getattr(self, "_event_type", "UNKNOWN"))
        return getattr(self, "_event_type", "UNKNOWN")

    @event_type.setter
    def event_type(self, val: str):
        self._event_type = val
        if not isinstance(self.payload, dict):
            self.payload = {}
        self.payload["event_type"] = val

    @property
    def correlation_id(self) -> str:
        if isinstance(self.payload, dict):
            return self.payload.get("correlation_id", getattr(self, "_correlation_id", "root"))
        return getattr(self, "_correlation_id", "root")

    @correlation_id.setter
    def correlation_id(self, val: str):
        self._correlation_id = val
        if not isinstance(self.payload, dict):
            self.payload = {}
        self.payload["correlation_id"] = val

    @property
    def entity_type(self) -> str:
        if isinstance(self.payload, dict):
            return self.payload.get("entity_type", getattr(self, "_entity_type", "CUSTOMER"))
        return getattr(self, "_entity_type", "CUSTOMER")

    @entity_type.setter
    def entity_type(self, val: str):
        self._entity_type = val
        if not isinstance(self.payload, dict):
            self.payload = {}
        self.payload["entity_type"] = val

    @property
    def actor_id(self) -> str:
        return getattr(self, "_actor_id", None) or (self.payload.get("actor_id") if isinstance(self.payload, dict) else None) or self.rm_id or ""

    @actor_id.setter
    def actor_id(self, val: str):
        self._actor_id = val
        if not isinstance(self.payload, dict):
            self.payload = {}
        self.payload["actor_id"] = val

    @property
    def schema_version(self) -> str:
        return getattr(self, "_schema_version", "1.0")

    @schema_version.setter
    def schema_version(self, val: str):
        self._schema_version = val

    @property
    def entity_id(self) -> str:
        return self.customer_id or self.lead_id or getattr(self, "_entity_id", "")

    @entity_id.setter
    def entity_id(self, val: str):
        self._entity_id = val
        if getattr(self, "_entity_type", "CUSTOMER").upper() == "LEAD":
            self.lead_id = val
        else:
            self.customer_id = val
    @property
    def causation_id(self) -> Optional[str]:
        return getattr(self, "_causation_id", None) or (self.payload.get("causation_id") if isinstance(self.payload, dict) else None)

    @causation_id.setter
    def causation_id(self, val: Optional[str]):
        self._causation_id = val
        if not isinstance(self.payload, dict):
            self.payload = {}
        self.payload["causation_id"] = val






class EventProcessingAttempt(Base):
    __tablename__ = "event_processing_attempts"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    event_id = Column(String(64), nullable=False, index=True)
    status = Column(String(64), nullable=False)
    attempt_number = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=now_utc)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    processed_at = synonym("completed_at")

    @property
    def processor_name(self) -> str:
        return getattr(self, "_processor_name", "event_intelligence_server")


    @processor_name.setter
    def processor_name(self, val: str):
        self._processor_name = val



# ============================================================================
# 4. INTELLIGENCE & RULES (6 Tables)
# ============================================================================

class Rule(Base):
    __tablename__ = "rules"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rule_id = Column(String(64), nullable=False, index=True)
    version_number = Column(Integer, default=1)
    conditions = Column(JSON, default=dict)
    action_config = Column(JSON, default=dict)
    scoring_config = Column(JSON, default=dict)
    event_window_minutes = Column(Integer, default=1440)
    effective_from = Column(DateTime(timezone=True), default=now_utc)
    effective_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class RuleEventType(Base):
    __tablename__ = "rule_event_types"

    rule_id = Column(String(64), primary_key=True)
    event_type_id = Column(String(64), primary_key=True)


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rule_version_id = Column(String(64), nullable=True)
    event_id = Column(String(64), nullable=True)
    customer_id = Column(String(64), nullable=True)
    lead_id = Column(String(64), nullable=True)
    rm_id = Column(String(64), nullable=True)
    matched = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    evaluated_state = Column(JSON, default=dict)
    matched_conditions = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), default=now_utc)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), nullable=False, index=True)
    lead_id = Column(String(64), nullable=True)
    rm_id = Column(String(64), nullable=True, index=True)
    product_id = Column(String(64), nullable=True)
    source_event_id = Column(String(64), nullable=True)
    source_rule_id = Column(String(64), nullable=True)
    opportunity_type = Column(String(64), nullable=False)
    status = Column(String(64), default="DETECTED")
    potential_value = Column(Float, default=0.0)
    score = Column(Float, default=0.5)
    reason = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), default=now_utc)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    estimated_value = synonym("potential_value")
    rule_version_id = synonym("source_rule_id")



    @property
    def title(self) -> str:
        return getattr(self, "_title", None) or f"{self.opportunity_type.replace('_', ' ').title()}"

    @title.setter
    def title(self, val: str):
        self._title = val

    @property
    def priority(self) -> str:
        if hasattr(self, "_priority") and self._priority:
            return self._priority
        if self.score >= 0.8:
            return "CRITICAL" if self.score >= 0.9 else "HIGH"
        return "MEDIUM" if self.score >= 0.5 else "LOW"

    @priority.setter
    def priority(self, val: str):
        self._priority = val

    @property
    def recommended_action(self) -> str:
        return getattr(self, "_recommended_action", None) or (self.reason or f"Recommend {self.opportunity_type} to customer")

    @recommended_action.setter
    def recommended_action(self, val: str):
        self._recommended_action = val

    @property
    def reason_codes(self) -> list:
        return getattr(self, "_reason_codes", None) or [self.opportunity_type]

    @reason_codes.setter
    def reason_codes(self, val: list):
        self._reason_codes = val

    @property
    def evidence(self) -> dict:
        return getattr(self, "_evidence", None) or {"opportunity_type": self.opportunity_type, "score": self.score, "reason": self.reason, "agent_version": "1.0.0-deterministic"}

    @evidence.setter
    def evidence(self, val: dict):
        self._evidence = val


    @property
    def correlation_id(self) -> str:
        return self.source_event_id or "root"

    @correlation_id.setter
    def correlation_id(self, val: str):
        self.source_event_id = val


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rm_id = Column(String(64), nullable=False, index=True)
    achievement_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    period = Column(String(32), nullable=True)
    milestone_value = Column(Float, default=0.0)
    metadata_json = Column("metadata", JSON, default=dict)
    awarded_at = Column(DateTime(timezone=True), default=now_utc)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    metric_value = synonym("milestone_value")
    evidence = synonym("metadata_json")




# ============================================================================
# 5. ACTION & WORKFLOW (3 Tables)
# ============================================================================

class Action(Base):
    __tablename__ = "actions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), nullable=False, index=True)
    lead_id = Column(String(64), nullable=True)
    rm_id = Column(String(64), nullable=False, index=True)
    opportunity_id = Column(String(64), nullable=True)
    action_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(32), default="MEDIUM")
    status = Column(String(64), default="PROPOSED")
    due_date = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    assigned_rm_id = synonym("rm_id")

    @property
    def correlation_id(self) -> str:
        if isinstance(self.metadata_json, dict):
            return self.metadata_json.get("correlation_id", "root")
        return "root"

    @correlation_id.setter
    def correlation_id(self, val: str):
        if not isinstance(self.metadata_json, dict):
            self.metadata_json = {}
        self.metadata_json["correlation_id"] = val

    @property
    def source_decision_id(self) -> str:
        if isinstance(self.metadata_json, dict):
            return self.metadata_json.get("source_decision_id", "")
        return getattr(self, "_source_decision_id", "")

    @source_decision_id.setter
    def source_decision_id(self, val: str):
        self._source_decision_id = val
        if not isinstance(self.metadata_json, dict):
            self.metadata_json = {}
        self.metadata_json["source_decision_id"] = val


class ActionHistory(Base):
    __tablename__ = "action_history"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    action_id = Column(String(64), nullable=False, index=True)
    from_status = Column(String(64), nullable=True)
    to_status = Column(String(64), nullable=False)
    changed_by_id = Column(String(64), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class ActionOutcome(Base):
    __tablename__ = "action_outcomes"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    action_id = Column(String(64), unique=True, nullable=False, index=True)
    outcome_type = Column(String(64), nullable=False)
    converted_product_id = Column(String(64), nullable=True)
    converted_value = Column(Float, default=0.0)
    commission_eligible = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=now_utc)


# ============================================================================
# 6. PERFORMANCE & TARGETS (3 Tables)
# ============================================================================

class Target(Base):
    __tablename__ = "targets"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rm_id = Column(String(64), nullable=False, index=True)
    org_unit_id = Column(String(64), nullable=True)
    product_id = Column(String(64), nullable=True)
    metric_code = Column(String(64), default="REVENUE")
    period_type = Column(String(32), default="QUARTER")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    target_value = Column(Float, nullable=False)
    unit = Column(String(32), default="INR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    target_amount = synonym("target_value")
    start_date = synonym("period_start")
    end_date = synonym("period_end")

    @property
    def achieved_amount(self) -> float:
        return getattr(self, "_achieved_amount", 0.0)

    @achieved_amount.setter
    def achieved_amount(self, val: float):
        self._achieved_amount = float(val)

    @property
    def period(self) -> str:
        return getattr(self, "_period", None) or (f"{self.period_start.year}-Q{(self.period_start.month-1)//3 + 1}" if self.period_start else "2026-Q1")

    @period.setter
    def period(self, val: str):
        self._period = val


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    org_unit_id = Column(String(64), nullable=True)
    metric_code = Column(String(64), nullable=False)
    period_type = Column(String(32), default="MONTH")
    benchmark_value = Column(Float, nullable=False)
    unit = Column(String(32), default="INR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    metric_name = synonym("metric_code")
    period = synonym("period_type")
    expected_amount = synonym("benchmark_value")

    @property
    def team_average(self) -> float:
        return float(self.benchmark_value or 0.0)



class RMPerformanceSnapshot(Base):
    __tablename__ = "rm_performance_snapshots"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rm_id = Column(String(64), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    target_value = Column(Float, default=0.0)
    achieved_value = Column(Float, default=0.0)
    achievement_percent = Column(Float, default=0.0)
    expected_run_rate_percent = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    activity_count = Column(Integer, default=0)
    overdue_action_count = Column(Integer, default=0)
    pipeline_value = Column(Float, default=0.0)
    sla_breach_count = Column(Float, default=0.0)
    contributing_factors = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    target = synonym("target_value")
    achievement = synonym("achieved_value")
    run_rate_pacing = synonym("expected_run_rate_percent")
    expected_run_rate = synonym("expected_run_rate_percent")
    projected_value = synonym("pipeline_value")
    overdue_actions = synonym("overdue_action_count")
    sla_breaches = synonym("sla_breach_count")



    @property
    def period(self) -> str:
        if isinstance(self.contributing_factors, dict):
            return self.contributing_factors.get("period", "2026-Q1")
        return getattr(self, "_period", "2026-Q1")

    @period.setter
    def period(self, val: str):
        self._period = val
        if not isinstance(self.contributing_factors, dict):
            self.contributing_factors = {}
        self.contributing_factors["period"] = val

    @property
    def status(self) -> str:
        if isinstance(self.contributing_factors, dict):
            return self.contributing_factors.get("status", "HEALTHY")
        return getattr(self, "_status", "HEALTHY")

    @status.setter
    def status(self, val: str):
        self._status = val
        if not isinstance(self.contributing_factors, dict):
            self.contributing_factors = {}
        self.contributing_factors["status"] = val

    @property
    def primary_drivers(self) -> list:
        if isinstance(self.contributing_factors, dict):
            return self.contributing_factors.get("primary_drivers", [])
        return getattr(self, "_primary_drivers", [])

    @primary_drivers.setter
    def primary_drivers(self, val: list):
        self._primary_drivers = val
        if not isinstance(self.contributing_factors, dict):
            self.contributing_factors = {}
        self.contributing_factors["primary_drivers"] = val

    @property
    def productivity(self) -> float:
        return getattr(self, "_productivity", 0.0)

    @productivity.setter
    def productivity(self, val: float):
        self._productivity = val

    @property
    def sla_score(self) -> float:
        return getattr(self, "_sla_score", 0.0)

    @sla_score.setter
    def sla_score(self, val: float):
        self._sla_score = val

    @property
    def benchmark_delta(self) -> float:
        return getattr(self, "_benchmark_delta", 0.0)

    @benchmark_delta.setter
    def benchmark_delta(self, val: float):
        self._benchmark_delta = val

    @property
    def secondary_drivers(self) -> list:
        return getattr(self, "_secondary_drivers", [])

    @secondary_drivers.setter
    def secondary_drivers(self, val: list):
        self._secondary_drivers = val

    @property
    def recommended_intervention(self) -> str:
        return getattr(self, "_recommended_intervention", "")

    @recommended_intervention.setter
    def recommended_intervention(self, val: str):
        self._recommended_intervention = val

    @property
    def snapshot_at(self) -> datetime:
        return getattr(self, "_snapshot_at", None) or self.created_at

    @snapshot_at.setter
    def snapshot_at(self, val: datetime):
        self._snapshot_at = val
        self.snapshot_date = val.date() if isinstance(val, datetime) else val




# ============================================================================
# 7. AUDIT & BLOCKCHAIN (2 Tables)
# ============================================================================

class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    action = Column(String(128), nullable=False)
    actor_id = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)
    payload_hash = Column(String(64), nullable=False)
    canonical_payload = Column(JSON, nullable=False)
    correlation_id = Column(String(128), nullable=False, index=True)
    causation_id = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    blockchain_record = relationship("BlockchainRecord", back_populates="audit_record", uselist=False)


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    audit_record_id = Column(String(64), ForeignKey("audit_records.id"), nullable=False, unique=True, index=True)
    blockchain_network = Column(String(64), default="local_integrity_ledger")
    contract_address = Column(String(128), nullable=True)
    transaction_hash = Column(String(128), nullable=True)
    block_number = Column(String(64), nullable=True)
    record_hash = Column(String(64), nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)
    status = Column(String(32), default="PENDING")
    submitted_at = Column(DateTime(timezone=True), default=now_utc)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    audit_record = relationship("AuditRecord", back_populates="blockchain_record")
    tx_hash = synonym("transaction_hash")
    batch_root_hash = synonym("record_hash")
    created_at = synonym("submitted_at")
    anchored_at = synonym("confirmed_at")

    @property
    def retry_count(self) -> int:
        if isinstance(self.metadata_json, dict):
            return self.metadata_json.get("retry_count", getattr(self, "_retry_count", 0))
        return getattr(self, "_retry_count", 0)

    @retry_count.setter
    def retry_count(self, val: int):
        self._retry_count = val
        meta = dict(self.metadata_json) if isinstance(self.metadata_json, dict) else {}
        meta["retry_count"] = val
        self.metadata_json = meta

    @property
    def last_error(self) -> str:
        if isinstance(self.metadata_json, dict):
            return self.metadata_json.get("last_error", getattr(self, "_last_error", ""))
        return getattr(self, "_last_error", "")

    @last_error.setter
    def last_error(self, val: str):
        self._last_error = val
        meta = dict(self.metadata_json) if isinstance(self.metadata_json, dict) else {}
        meta["last_error"] = val
        self.metadata_json = meta


