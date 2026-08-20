"""
Model Registry
---------------
Imports every model module so all 27 tables are registered
in Base.metadata before create_all() is called.
"""

# Identity & Organization Service  (4 tables)
from app.models.identity import Role, OrgUnit, Profile, UserRole  # noqa: F401

# CRM Service  (6 tables)
from app.models.crm import (  # noqa: F401
    Customer, Product, CustomerProduct,
    Lead, Interaction, Transaction,
)

# Event Processing Service  (3 tables)
from app.models.events import (  # noqa: F401
    EventType, BusinessEvent, EventProcessingAttempt,
)

# Intelligence / Rule Engine Service  (6 tables)
from app.models.intelligence import (  # noqa: F401
    Rule, RuleVersion, RuleEventType,
    RuleEvaluation, Opportunity, Achievement,
)

# Action & Workflow Service  (3 tables)
from app.models.actions import Action, ActionHistory, ActionOutcome  # noqa: F401

# Performance Intelligence Service  (3 tables)
from app.models.performance import (  # noqa: F401
    Target, Benchmark, RmPerformanceSnapshot,
)

# Audit / Blockchain Service  (2 tables)
from app.models.audit import AuditRecord, BlockchainRecord  # noqa: F401
