"""SQLAlchemy Declarative Models for the 27-table PS-02 Database Schema."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
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
    name = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    user_roles = relationship("UserRole", back_populates="role")


class OrgUnit(Base):
    __tablename__ = "org_units"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    type = Column(String(64), nullable=False)  # BRANCH, REGION, TEAM, DIVISION
    parent_id = Column(String(64), ForeignKey("org_units.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    parent = relationship("OrgUnit", remote_side=[id], backref="children")
    profiles = relationship("Profile", back_populates="org_unit")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=True)
    org_unit_id = Column(String(64), ForeignKey("org_units.id"), nullable=True)
    manager_id = Column(String(64), ForeignKey("profiles.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    org_unit = relationship("OrgUnit", back_populates="profiles")
    manager = relationship("Profile", remote_side=[id], backref="reportees")
    user_roles = relationship("UserRole", back_populates="profile")
    assigned_customers = relationship("Customer", back_populates="primary_rm")
    assigned_leads = relationship("Lead", back_populates="assigned_rm")
    assigned_opportunities = relationship("Opportunity", back_populates="rm")
    assigned_actions = relationship("Action", back_populates="assigned_rm")
    targets = relationship("Target", back_populates="rm")
    achievements = relationship("Achievement", back_populates="rm")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    user_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    role_id = Column(String(64), ForeignKey("roles.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    profile = relationship("Profile", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


# ============================================================================
# 2. CRM CORE (6 Tables)
# ============================================================================

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_code = Column(String(64), unique=True, nullable=False, index=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(32), nullable=True)
    segment = Column(String(64), nullable=False, default="RETAIL")  # RETAIL, HNI, ULTRA_HNI, CORPORATE
    city = Column(String(128), nullable=True)
    region = Column(String(128), nullable=True)
    relationship_value = Column(Float, default=0.0)
    aum = Column(Float, default=0.0)
    primary_rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=True, index=True)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, DORMANT, PROSPECT, INACTIVE
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    primary_rm = relationship("Profile", back_populates="assigned_customers")
    products = relationship("CustomerProduct", back_populates="customer")
    leads = relationship("Lead", back_populates="customer")
    interactions = relationship("Interaction", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")
    opportunities = relationship("Opportunity", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)  # EQUITY, MUTUAL_FUND, INSURANCE, FIXED_INCOME, LOAN
    is_active = Column(Boolean, default=True)
    base_commission_rate = Column(Float, default=0.02)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    customer_holdings = relationship("CustomerProduct", back_populates="product")


class CustomerProduct(Base):
    __tablename__ = "customer_products"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    holding_value = Column(Float, default=0.0)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, REDEEMED, CLOSED
    opened_at = Column(DateTime(timezone=True), default=now_utc)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    customer = relationship("Customer", back_populates="products")
    product = relationship("Product", back_populates="customer_holdings")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=True, index=True)
    assigned_rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=True, index=True)
    product_id = Column(String(64), ForeignKey("products.id"), nullable=True)
    title = Column(String(255), nullable=False)
    stage = Column(String(64), default="NEW")  # NEW, CONTACTED, QUALIFIED, PROPOSAL, CONVERTED, LOST
    intent_score = Column(Float, default=0.5)
    estimated_value = Column(Float, nullable=True)
    source = Column(String(128), default="DIRECT")
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    customer = relationship("Customer", back_populates="leads")
    assigned_rm = relationship("Profile", back_populates="assigned_leads")
    product = relationship("Product")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    lead_id = Column(String(64), ForeignKey("leads.id"), nullable=True)
    type = Column(String(64), default="CALL")  # CALL, MEETING, EMAIL, NOTE, DIGITAL
    summary = Column(Text, nullable=True)
    sentiment = Column(String(32), default="NEUTRAL")  # POSITIVE, NEUTRAL, NEGATIVE
    occurred_at = Column(DateTime(timezone=True), default=now_utc)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    customer = relationship("Customer", back_populates="interactions")
    rm = relationship("Profile")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id"), nullable=True)
    type = Column(String(64), nullable=False)  # PAYIN, PAYOUT, INVESTMENT, SIP, REDEMPTION
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    reference_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), default="COMPLETED")  # PENDING, COMPLETED, FAILED
    occurred_at = Column(DateTime(timezone=True), default=now_utc)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    customer = relationship("Customer", back_populates="transactions")
    product = relationship("Product")


# ============================================================================
# 3. EVENT PROCESSING (3 Tables)
# ============================================================================

class EventType(Base):
    __tablename__ = "event_types"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class BusinessEvent(Base):
    __tablename__ = "business_events"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    event_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(64), nullable=True)
    source = Column(String(128), default="system")
    payload = Column(JSON, nullable=False, default=dict)
    schema_version = Column(String(16), default="1.0")
    correlation_id = Column(String(64), nullable=False, index=True)
    causation_id = Column(String(64), nullable=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), default=now_utc)
    received_at = Column(DateTime(timezone=True), default=now_utc)

    attempts = relationship("EventProcessingAttempt", back_populates="event")


class EventProcessingAttempt(Base):
    __tablename__ = "event_processing_attempts"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    event_id = Column(String(64), ForeignKey("business_events.id"), nullable=False, index=True)
    processor_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)  # SUCCESS, FAILED, SKIPPED, RETRYING
    error_message = Column(Text, nullable=True)
    attempt_number = Column(Integer, default=1)
    processed_at = Column(DateTime(timezone=True), default=now_utc)

    event = relationship("BusinessEvent", back_populates="attempts")


# ============================================================================
# 4. INTELLIGENCE (6 Tables)
# ============================================================================

class Rule(Base):
    __tablename__ = "rules"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)  # OPPORTUNITY, PERFORMANCE, ALERT, COMMISSION
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    versions = relationship("RuleVersion", back_populates="rule")


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rule_id = Column(String(64), ForeignKey("rules.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    conditions = Column(JSON, nullable=False, default=dict)
    weights = Column(JSON, nullable=False, default=dict)
    thresholds = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    rule = relationship("Rule", back_populates="versions")
    evaluations = relationship("RuleEvaluation", back_populates="rule_version")


class RuleEventType(Base):
    __tablename__ = "rule_event_types"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rule_id = Column(String(64), ForeignKey("rules.id"), nullable=False, index=True)
    event_type_code = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rule_version_id = Column(String(64), ForeignKey("rule_versions.id"), nullable=True, index=True)
    event_id = Column(String(64), ForeignKey("business_events.id"), nullable=True)
    entity_id = Column(String(64), nullable=False, index=True)
    score = Column(Float, default=0.0)
    result = Column(Boolean, default=False)
    evidence = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    rule_version = relationship("RuleVersion", back_populates="evaluations")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id"), nullable=True)
    opportunity_type = Column(String(64), nullable=False)  # CROSS_SELL, UPSELL, DORMANT_REACTIVATION, HIGH_INTENT_LEAD, PRODUCT_GAP, OPPORTUNITY_AT_RISK
    title = Column(String(255), nullable=False)
    status = Column(String(32), default="DETECTED")  # DETECTED, ASSIGNED, CONTACT_PENDING, CONTACTED, INTERESTED, CONVERTED, SNOOZED, REJECTED, LOST, EXPIRED
    score = Column(Float, nullable=False, default=0.5)
    priority = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    estimated_value = Column(Float, nullable=True)
    recommended_action = Column(String(255), nullable=False)
    reason_codes = Column(JSON, nullable=False, default=list)
    evidence = Column(JSON, nullable=False, default=dict)
    source_event_id = Column(String(64), nullable=True)
    rule_version_id = Column(String(64), nullable=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    customer = relationship("Customer", back_populates="opportunities")
    rm = relationship("Profile", back_populates="assigned_opportunities")
    product = relationship("Product")
    actions = relationship("Action", back_populates="opportunity")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    achievement_type = Column(String(64), nullable=False)  # EARLY_TARGET_ACHIEVEMENT, EXCEPTIONAL_CONVERSION, MAJOR_WIN, DORMANT_RECOVERY
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metric_value = Column(Float, default=0.0)
    period = Column(String(32), nullable=False)
    evidence = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    rm = relationship("Profile", back_populates="achievements")


# ============================================================================
# 5. ACTION & WORKFLOW (3 Tables)
# ============================================================================

class Action(Base):
    __tablename__ = "actions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    opportunity_id = Column(String(64), ForeignKey("opportunities.id"), nullable=True, index=True)
    lead_id = Column(String(64), ForeignKey("leads.id"), nullable=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    assigned_rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    action_type = Column(String(64), nullable=False)  # CALL_CUSTOMER, OFFER_PRODUCT, FOLLOW_UP_LEAD, PORTFOLIO_REVIEW
    status = Column(String(32), default="PROPOSED")  # PROPOSED, VALIDATED, ASSIGNED, IN_PROGRESS, COMPLETED, SNOOZED, REASSIGNED, FAILED, EXPIRED, REJECTED
    priority = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    due_date = Column(DateTime(timezone=True), nullable=True)
    source_decision_id = Column(String(64), nullable=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    opportunity = relationship("Opportunity", back_populates="actions")
    customer = relationship("Customer")
    assigned_rm = relationship("Profile", back_populates="assigned_actions")
    history = relationship("ActionHistory", back_populates="action")
    outcome = relationship("ActionOutcome", uselist=False, back_populates="action")


class ActionHistory(Base):
    __tablename__ = "action_history"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    action_id = Column(String(64), ForeignKey("actions.id"), nullable=False, index=True)
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    changed_by_id = Column(String(64), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    action = relationship("Action", back_populates="history")


class ActionOutcome(Base):
    __tablename__ = "action_outcomes"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    action_id = Column(String(64), ForeignKey("actions.id"), unique=True, nullable=False, index=True)
    outcome_type = Column(String(64), nullable=False)  # CONVERTED, INTERESTED_FOLLOWUP, REJECTED, NOT_REACHABLE
    notes = Column(Text, nullable=True)
    converted_product_id = Column(String(64), ForeignKey("products.id"), nullable=True)
    converted_value = Column(Float, nullable=True)
    commission_eligible = Column(Boolean, default=False)
    recorded_at = Column(DateTime(timezone=True), default=now_utc)

    action = relationship("Action", back_populates="outcome")
    converted_product = relationship("Product")


# ============================================================================
# 6. PERFORMANCE (3 Tables)
# ============================================================================

class Target(Base):
    __tablename__ = "targets"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    period = Column(String(32), nullable=False, index=True)  # e.g., "2026-Q1"
    target_amount = Column(Float, default=0.0)
    achieved_amount = Column(Float, default=0.0)
    target_leads = Column(Integer, default=0)
    achieved_leads = Column(Integer, default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    rm = relationship("Profile", back_populates="targets")


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    org_unit_id = Column(String(64), ForeignKey("org_units.id"), nullable=True)
    metric_name = Column(String(128), nullable=False, index=True)
    period = Column(String(32), nullable=False, index=True)
    team_average = Column(Float, default=0.0)
    team_median = Column(Float, default=0.0)
    top_quartile = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class RMPerformanceSnapshot(Base):
    __tablename__ = "rm_performance_snapshots"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    rm_id = Column(String(64), ForeignKey("profiles.id"), nullable=False, index=True)
    period = Column(String(32), nullable=False, index=True)
    target = Column(Float, default=0.0)
    achievement = Column(Float, default=0.0)
    expected_run_rate = Column(Float, default=0.0)
    projected_value = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    productivity = Column(Float, default=0.0)
    pipeline_value = Column(Float, default=0.0)
    sla_score = Column(Float, default=1.0)
    benchmark_delta = Column(Float, default=0.0)
    status = Column(String(32), nullable=False, default="ON_TRACK")  # HEALTHY, ON_TRACK, AT_RISK, CRITICAL, EXCEPTIONAL
    primary_drivers = Column(JSON, nullable=False, default=list)
    secondary_drivers = Column(JSON, nullable=False, default=list)
    recommended_intervention = Column(Text, nullable=True)
    snapshot_at = Column(DateTime(timezone=True), default=now_utc)

    rm = relationship("Profile")


# ============================================================================
# 7. AUDIT & BLOCKCHAIN (2 Tables)
# ============================================================================

class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    actor_id = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)
    payload_hash = Column(String(64), nullable=False)
    canonical_payload = Column(JSON, nullable=False, default=dict)
    correlation_id = Column(String(64), nullable=False, index=True)
    causation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    blockchain_record = relationship("BlockchainRecord", uselist=False, back_populates="audit_record")


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    audit_record_id = Column(String(64), ForeignKey("audit_records.id"), nullable=True, index=True)
    batch_root_hash = Column(String(64), nullable=False, index=True)
    tx_hash = Column(String(128), nullable=True, index=True)
    blockchain_network = Column(String(64), default="integrity_ledger")  # integrity_ledger, polygon_pos, ethereum_mainnet
    block_number = Column(Integer, nullable=True)
    status = Column(String(32), default="PENDING")  # PENDING, ANCHORED, FAILED
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    anchored_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    audit_record = relationship("AuditRecord", back_populates="blockchain_record")
