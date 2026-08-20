"""
CRM Service Models
-------------------
Tables: customers, products, customer_products, leads,
        interactions, transactions
"""

import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Date, DateTime, ForeignKey,
    Index, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# CUSTOMERS
# ──────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_code = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    segment = Column(String, nullable=True)
    city = Column(String, nullable=True)
    potential_value = Column(Numeric, nullable=True)
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    lifecycle_status = Column(String, nullable=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    rm = relationship("Profile", back_populates="customers")
    leads = relationship("Lead", back_populates="customer")
    customer_products = relationship(
        "CustomerProduct", back_populates="customer"
    )
    interactions = relationship("Interaction", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")
    business_events = relationship("BusinessEvent", back_populates="customer")
    rule_evaluations = relationship(
        "RuleEvaluation", back_populates="customer"
    )
    opportunities = relationship("Opportunity", back_populates="customer")
    actions = relationship("Action", back_populates="customer")

    __table_args__ = (
        Index("ix_customers_segment", "segment"),
        Index("ix_customers_lifecycle_status", "lifecycle_status"),
    )


# ──────────────────────────────────────────────
# PRODUCTS
# ──────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    customer_products = relationship(
        "CustomerProduct", back_populates="product"
    )
    transactions = relationship("Transaction", back_populates="product")
    opportunities = relationship("Opportunity", back_populates="product")
    targets = relationship("Target", back_populates="product")
    benchmarks = relationship("Benchmark", back_populates="product")

    __table_args__ = (
        Index("ix_products_category", "category"),
    )


# ──────────────────────────────────────────────
# CUSTOMER_PRODUCTS
# ──────────────────────────────────────────────

class CustomerProduct(Base):
    __tablename__ = "customer_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String, nullable=True)
    relationship_value = Column(Numeric, nullable=True)
    acquired_on = Column(Date, nullable=True)
    closed_on = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    customer = relationship("Customer", back_populates="customer_products")
    product = relationship("Product", back_populates="customer_products")


# ──────────────────────────────────────────────
# LEADS
# ──────────────────────────────────────────────

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_code = Column(String, unique=True, nullable=False)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source = Column(String, nullable=True)
    stage = Column(String, nullable=True)
    status = Column(String, nullable=True, index=True)
    potential_value = Column(Numeric, nullable=True)
    priority = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    next_followup_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    customer = relationship("Customer", back_populates="leads")
    rm = relationship("Profile", back_populates="leads")
    interactions = relationship("Interaction", back_populates="lead")
    transactions = relationship("Transaction", back_populates="lead")
    business_events = relationship("BusinessEvent", back_populates="lead")
    rule_evaluations = relationship("RuleEvaluation", back_populates="lead")
    opportunities = relationship("Opportunity", back_populates="lead")
    actions = relationship("Action", back_populates="lead")


# ──────────────────────────────────────────────
# INTERACTIONS
# ──────────────────────────────────────────────

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    interaction_type = Column(String, nullable=False)
    outcome = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    next_followup_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    customer = relationship("Customer", back_populates="interactions")
    lead = relationship("Lead", back_populates="interactions")
    rm = relationship("Profile", back_populates="interactions")


# ──────────────────────────────────────────────
# TRANSACTIONS
# ──────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=True, index=True)
    transaction_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    lead = relationship("Lead", back_populates="transactions")
    rm = relationship("Profile", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")
    business_events = relationship(
        "BusinessEvent", back_populates="transaction"
    )
