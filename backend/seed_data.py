"""
PS-02 Comprehensive Database Seeder
====================================
Populates the SQLite database with realistic CRM data so the full
EVENT → INTELLIGENCE → OPPORTUNITY → ACTION pipeline has data.

Run from project root:
    python -m backend.seed_data

Or with venv:
    .venv/Scripts/python -m backend.seed_data
"""

import uuid
import random
import hashlib
import json
from datetime import datetime, timezone, timedelta, date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.shared.database import Base, engine, SessionLocal
from backend.services.shared.models import (
    Profile, Customer, Product, CustomerProduct, Lead,
    Transaction, Interaction, Opportunity, Action, ActionOutcome,
    ActionHistory, Target, RMPerformanceSnapshot, Achievement,
    AuditRecord, OrgUnit, Role
)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ─── Deterministic UUIDs ────────────────────────────────────────
def stable_id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))

now = datetime.now(timezone.utc)
now_naive = datetime.utcnow()  # for SQLite comparisons
today = now.date()

# ─── Clear existing data (idempotent re-seed) ───────────────────
for model in [
    ActionOutcome, ActionHistory, Action, Opportunity, Lead,
    Interaction, Transaction, CustomerProduct,
    RMPerformanceSnapshot, Target, Achievement,
    AuditRecord,
    Customer, Product, Profile, OrgUnit, Role,
]:
    try:
        db.query(model).delete()
        db.commit()
    except Exception:
        db.rollback()
print("✓ Cleared existing data")

# ═══════════════════════════════════════════════════════════════════
# 1. ORG STRUCTURE
# ═══════════════════════════════════════════════════════════════════

org_mumbai = OrgUnit(id=stable_id("branch_mumbai_01"), unit_type="BRANCH", name="Mumbai Central Branch", code="MUM_01")
org_delhi = OrgUnit(id=stable_id("branch_delhi_01"), unit_type="BRANCH", name="Delhi Connaught Place Branch", code="DEL_01")
db.add_all([org_mumbai, org_delhi])
db.commit()
print("✓ 2 org units")

# ═══════════════════════════════════════════════════════════════════
# 2. PROFILES (RMs + Manager)
# ═══════════════════════════════════════════════════════════════════

mgr_vikram = Profile(
    id=stable_id("mgr_vikram_01"), employee_code="EMP-MGR-01",
    full_name="Vikram Seth", email="vikram@crm.com", phone="+919800000001",
    manager_id=None, org_unit_id=org_mumbai.id, is_active=True
)
rm_priya = Profile(
    id=stable_id("rm_priya_01"), employee_code="EMP-RM-01",
    full_name="Priya Sharma", email="priya@crm.com", phone="+919800000002",
    manager_id=mgr_vikram.id, org_unit_id=org_mumbai.id, is_active=True
)
rm_arjun = Profile(
    id=stable_id("rm_arjun_01"), employee_code="EMP-RM-02",
    full_name="Arjun Mehta", email="arjun@crm.com", phone="+919800000003",
    manager_id=mgr_vikram.id, org_unit_id=org_mumbai.id, is_active=True
)
rm_neha = Profile(
    id=stable_id("rm_neha_01"), employee_code="EMP-RM-03",
    full_name="Neha Kapoor", email="neha@crm.com", phone="+919800000004",
    manager_id=mgr_vikram.id, org_unit_id=org_delhi.id, is_active=True
)
all_rms = [rm_priya, rm_arjun, rm_neha]
db.add_all([mgr_vikram, rm_priya, rm_arjun, rm_neha])
db.commit()
print("✓ 4 profiles (1 manager + 3 RMs)")

# ═══════════════════════════════════════════════════════════════════
# 3. PRODUCTS (10)
# ═══════════════════════════════════════════════════════════════════

products_data = [
    ("TERM_LIFE",    "Term Life Insurance",       "INSURANCE",    "Comprehensive term protection policy"),
    ("HEALTH_INS",   "Health Shield Premium",     "INSURANCE",    "Family floater health insurance plan"),
    ("BLUECHIP_MF",  "Bluechip Equity MF",        "MUTUAL_FUND",  "Diversified large cap mutual fund"),
    ("MIDCAP_MF",    "Midcap Growth Fund",        "MUTUAL_FUND",  "Growth-oriented mid-cap strategy"),
    ("DEBT_MF",      "Corporate Bond Fund",       "MUTUAL_FUND",  "High-grade corporate bond fund"),
    ("EQUITY_PMS",   "Equity PMS Alpha",          "EQUITY",       "High-alpha portfolio management service"),
    ("FIXED_DEP",    "Premium Fixed Deposit",     "FIXED_INCOME", "Special rate FD for HNI customers"),
    ("GOLD_ETF",     "Sovereign Gold Fund",       "COMMODITY",    "Gold-linked investment product"),
    ("NPS",          "National Pension Scheme",    "RETIREMENT",   "Tax-efficient retirement planning"),
    ("SIP_FLEXI",    "Flexible SIP Plan",         "MUTUAL_FUND",  "Step-up SIP with pause facility"),
]
products = []
for code, name, cat, desc in products_data:
    p = Product(id=stable_id(f"prod_{code}"), code=code, name=name, category=cat, description=desc, is_active=True)
    products.append(p)
db.add_all(products)
db.commit()
prod_map = {p.code: p for p in products}
print(f"✓ {len(products)} products")

# ═══════════════════════════════════════════════════════════════════
# 4. CUSTOMERS (15 across 3 RMs)
# ═══════════════════════════════════════════════════════════════════

customers_data = [
    ("CUST_101", "Vikram Malhotra",   "vikram.malhotra@mail.com",  "+919876543210", "ULTRA_HNI", "Mumbai",    25000000, rm_priya),
    ("CUST_102", "Ananya Reddy",      "ananya.reddy@mail.com",     "+919876543211", "HNI",       "Mumbai",    8500000,  rm_priya),
    ("CUST_103", "Rajesh Krishnan",   "rajesh.k@mail.com",         "+919876543212", "HNI",       "Pune",      6200000,  rm_priya),
    ("CUST_104", "Meera Deshmukh",    "meera.d@mail.com",          "+919876543213", "AFFLUENT",  "Mumbai",    3200000,  rm_priya),
    ("CUST_105", "Suresh Patel",      "suresh.p@mail.com",         "+919876543214", "RETAIL",    "Ahmedabad", 850000,   rm_priya),
    ("CUST_201", "Kavita Iyer",       "kavita.iyer@mail.com",      "+919876543220", "HNI",       "Delhi",     9800000,  rm_arjun),
    ("CUST_202", "Ramesh Gupta",      "ramesh.g@mail.com",         "+919876543221", "AFFLUENT",  "Delhi",     4500000,  rm_arjun),
    ("CUST_203", "Sunita Joshi",      "sunita.j@mail.com",         "+919876543222", "AFFLUENT",  "Gurgaon",   2800000,  rm_arjun),
    ("CUST_204", "Deepak Verma",      "deepak.v@mail.com",         "+919876543223", "RETAIL",    "Delhi",     600000,   rm_arjun),
    ("CUST_205", "Pooja Saxena",      "pooja.s@mail.com",          "+919876543224", "DORMANT",   "Noida",     1200000,  rm_arjun),
    ("CUST_301", "Arun Nair",         "arun.nair@mail.com",        "+919876543230", "ULTRA_HNI", "Bangalore", 32000000, rm_neha),
    ("CUST_302", "Lakshmi Venkat",    "lakshmi.v@mail.com",        "+919876543231", "HNI",       "Chennai",   7200000,  rm_neha),
    ("CUST_303", "Sanjay Kulkarni",   "sanjay.k@mail.com",         "+919876543232", "AFFLUENT",  "Hyderabad", 3800000,  rm_neha),
    ("CUST_304", "Divya Menon",       "divya.m@mail.com",          "+919876543233", "RETAIL",    "Kochi",     750000,   rm_neha),
    ("CUST_305", "Ravi Shankar",      "ravi.s@mail.com",           "+919876543234", "DORMANT",   "Bangalore", 1800000,  rm_neha),
]

customers = []
for code, name, email, phone, seg, city, val, rm in customers_data:
    status = "DORMANT" if seg == "DORMANT" else "ACTIVE"
    last_contact = now - timedelta(days=random.randint(1, 90) if seg != "DORMANT" else random.randint(180, 365))
    c = Customer(
        id=stable_id(code), customer_code=code, full_name=name, email=email, phone=phone,
        segment=seg, city=city, potential_value=float(val), rm_id=rm.id,
        lifecycle_status=status, last_contact_at=last_contact
    )
    customers.append(c)
db.add_all(customers)
db.commit()
cust_map = {c.customer_code: c for c in customers}
print(f"✓ {len(customers)} customers")

# ═══════════════════════════════════════════════════════════════════
# 5. CUSTOMER HOLDINGS
# ═══════════════════════════════════════════════════════════════════

holdings_data = [
    ("CUST_101", "BLUECHIP_MF", 2500000), ("CUST_101", "EQUITY_PMS", 8000000), ("CUST_101", "FIXED_DEP", 5000000),
    ("CUST_102", "BLUECHIP_MF", 3000000), ("CUST_102", "TERM_LIFE", 500000), ("CUST_102", "DEBT_MF", 2000000),
    ("CUST_103", "MIDCAP_MF", 1500000), ("CUST_103", "NPS", 800000),
    ("CUST_104", "SIP_FLEXI", 400000), ("CUST_104", "HEALTH_INS", 250000),
    ("CUST_105", "SIP_FLEXI", 100000),
    ("CUST_201", "EQUITY_PMS", 5000000), ("CUST_201", "BLUECHIP_MF", 2500000), ("CUST_201", "GOLD_ETF", 1000000),
    ("CUST_202", "MIDCAP_MF", 1200000), ("CUST_202", "TERM_LIFE", 300000),
    ("CUST_203", "SIP_FLEXI", 600000),
    ("CUST_204", "SIP_FLEXI", 80000),
    ("CUST_301", "EQUITY_PMS", 15000000), ("CUST_301", "BLUECHIP_MF", 5000000), ("CUST_301", "FIXED_DEP", 8000000), ("CUST_301", "GOLD_ETF", 2000000),
    ("CUST_302", "BLUECHIP_MF", 2500000), ("CUST_302", "DEBT_MF", 1500000),
    ("CUST_303", "MIDCAP_MF", 800000), ("CUST_303", "HEALTH_INS", 200000),
    ("CUST_304", "SIP_FLEXI", 120000),
]

for ccode, pcode, val in holdings_data:
    h = CustomerProduct(
        id=str(uuid.uuid4()), customer_id=cust_map[ccode].id, product_id=prod_map[pcode].id,
        status="ACTIVE", relationship_value=float(val),
        acquired_on=now - timedelta(days=random.randint(90, 730))
    )
    db.add(h)
db.commit()
print(f"✓ {len(holdings_data)} holdings")

# ═══════════════════════════════════════════════════════════════════
# 6. TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════

tx_types = ["DEPOSIT", "WITHDRAWAL", "SIP_INSTALLMENT", "PREMIUM_PAYMENT", "DIVIDEND", "REDEMPTION"]
tx_count = 0
for c in customers:
    n_txns = random.randint(3, 12) if c.segment != "DORMANT" else random.randint(0, 1)
    for _ in range(n_txns):
        tx = Transaction(
            id=str(uuid.uuid4()), customer_id=c.id, rm_id=c.rm_id,
            product_id=random.choice(products).id,
            transaction_type=random.choice(tx_types),
            amount=round(random.uniform(10000, 2000000), 2),
            currency="INR", status="COMPLETED",
            transaction_at=now - timedelta(days=random.randint(1, 120), hours=random.randint(0, 23))
        )
        db.add(tx)
        tx_count += 1
db.commit()
print(f"✓ {tx_count} transactions")

# ═══════════════════════════════════════════════════════════════════
# 7. INTERACTIONS
# ═══════════════════════════════════════════════════════════════════

interaction_types = ["CALL", "EMAIL", "MEETING", "VIDEO_CALL", "BRANCH_VISIT", "WHATSAPP"]
outcomes = ["POSITIVE", "NEUTRAL", "FOLLOW_UP_NEEDED", "ESCALATED", "NO_RESPONSE"]
int_count = 0
for c in customers:
    n_int = random.randint(2, 8) if c.segment != "DORMANT" else random.randint(0, 1)
    for _ in range(n_int):
        occurred = now - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23))
        i = Interaction(
            id=str(uuid.uuid4()), customer_id=c.id, rm_id=c.rm_id,
            interaction_type=random.choice(interaction_types),
            outcome=random.choice(outcomes),
            notes=random.choice([
                "Discussed portfolio rebalancing", "Annual review call",
                "Customer interested in insurance options", "Pitched PMS product",
                "Follow-up on previous lead", "Birthday courtesy call",
                "Investment review and SIP top-up discussion", None
            ]),
            occurred_at=occurred,
            next_followup_at=occurred + timedelta(days=random.randint(7, 30)) if random.random() > 0.3 else None
        )
        db.add(i)
        int_count += 1
db.commit()
print(f"✓ {int_count} interactions")

# ═══════════════════════════════════════════════════════════════════
# 8. LEADS
# ═══════════════════════════════════════════════════════════════════

lead_sources = ["REFERRAL", "DIGITAL", "BRANCH_WALK_IN", "CAMPAIGN", "CROSS_SELL_ENGINE", "PARTNER"]
lead_stages = ["NEW", "CONTACTED", "QUALIFIED", "PROPOSAL", "NEGOTIATION"]
leads = []
for c in customers:
    n_leads = random.randint(1, 3) if c.segment not in ["DORMANT", "RETAIL"] else random.randint(0, 1)
    for j in range(n_leads):
        stage = random.choice(lead_stages)
        status = "CONVERTED" if random.random() < 0.2 else random.choice(["OPEN", "IN_PROGRESS"])
        lead = Lead(
            id=str(uuid.uuid4()), lead_code=f"LEAD-{c.customer_code}-{j+1}",
            customer_id=c.id, rm_id=c.rm_id,
            source=random.choice(lead_sources), stage=stage, status=status,
            potential_value=round(random.uniform(50000, c.potential_value * 0.3), 2),
            priority=random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            created_at=now - timedelta(days=random.randint(5, 60)),
            last_contact_at=now - timedelta(days=random.randint(1, 20)) if random.random() > 0.3 else None,
            next_followup_at=now + timedelta(days=random.randint(1, 14)) if status != "CONVERTED" else None,
            converted_at=now - timedelta(days=random.randint(1, 10)) if status == "CONVERTED" else None
        )
        leads.append(lead)
        db.add(lead)
db.commit()
print(f"✓ {len(leads)} leads")

# ═══════════════════════════════════════════════════════════════════
# 9. OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════════

opp_types = ["CROSS_SELL", "UPSELL", "DORMANT_REACTIVATION", "HIGH_INTENT_LEAD", "PRODUCT_GAP"]
opp_statuses = ["DETECTED", "ASSIGNED", "CONTACT_PENDING", "CONTACTED", "INTERESTED", "CONVERTED", "LOST"]
opportunities = []

for c in customers:
    n_opps = random.randint(1, 4) if c.segment in ["ULTRA_HNI", "HNI"] else random.randint(0, 2)
    for j in range(n_opps):
        opp_type = random.choice(opp_types)
        if c.segment == "DORMANT":
            opp_type = "DORMANT_REACTIVATION"
        score = round(random.uniform(0.35, 0.95), 3)
        status = random.choices(opp_statuses, weights=[30, 20, 15, 10, 10, 10, 5])[0]

        opp = Opportunity(
            id=str(uuid.uuid4()), customer_id=c.id, rm_id=c.rm_id,
            product_id=random.choice(products).id,
            source_event_id=str(uuid.uuid4()),
            opportunity_type=opp_type, status=status,
            potential_value=round(random.uniform(100000, c.potential_value * 0.4), 2),
            score=score,
            reason=f"Intelligence detected {opp_type.lower().replace('_', ' ')} for {c.full_name} ({c.segment})",
            detected_at=now - timedelta(days=random.randint(1, 30)),
            expires_at=now + timedelta(days=random.randint(7, 60)),
            converted_at=now - timedelta(days=random.randint(1, 5)) if status == "CONVERTED" else None,
        )
        opportunities.append(opp)
        db.add(opp)
db.commit()
print(f"✓ {len(opportunities)} opportunities")

# ═══════════════════════════════════════════════════════════════════
# 10. ACTIONS
# ═══════════════════════════════════════════════════════════════════

action_types = ["CALL_CUSTOMER", "SCHEDULE_MEETING", "SEND_PROPOSAL", "FOLLOW_UP", "REVIEW_PORTFOLIO", "PITCH_PRODUCT"]
actions = []

for opp in opportunities:
    if opp.status == "DETECTED":
        continue
    n_actions = 1 if opp.status in ["ASSIGNED", "CONTACT_PENDING"] else random.randint(1, 2)
    for j in range(n_actions):
        a_status = "COMPLETED" if opp.status == "CONVERTED" else random.choices(
            ["ASSIGNED", "IN_PROGRESS", "SNOOZED", "COMPLETED"], weights=[30, 30, 15, 25]
        )[0]
        due = now + timedelta(days=random.randint(-5, 14))
        action = Action(
            id=str(uuid.uuid4()), customer_id=opp.customer_id, rm_id=opp.rm_id,
            opportunity_id=opp.id, lead_id=None,
            action_type=random.choice(action_types),
            title=f"{random.choice(action_types).replace('_', ' ').title()} — {opp.opportunity_type.replace('_', ' ').title()}",
            description=opp.reason,
            priority=("CRITICAL" if opp.score >= 0.85 else "HIGH" if opp.score >= 0.7 else "MEDIUM" if opp.score >= 0.5 else "LOW"),
            status=a_status,
            due_date=due,
            metadata_json={"source": "intelligence_agent", "opp_score": opp.score},
        )
        actions.append(action)
        db.add(action)

        # History
        h1 = ActionHistory(
            id=str(uuid.uuid4()), action_id=action.id,
            from_status=None, to_status="ASSIGNED",
            changed_by_id="system", reason="Auto-assigned by intelligence agent",
            created_at=action.created_at
        )
        db.add(h1)
        if a_status in ["IN_PROGRESS", "COMPLETED", "SNOOZED"]:
            h2 = ActionHistory(
                id=str(uuid.uuid4()), action_id=action.id,
                from_status="ASSIGNED", to_status=a_status,
                changed_by_id=opp.rm_id, reason="RM updated status",
                created_at=now - timedelta(hours=random.randint(1, 48))
            )
            db.add(h2)

        # Outcome for completed
        if a_status == "COMPLETED":
            outcome_type = "CONVERTED" if opp.status == "CONVERTED" else random.choice(["CONVERTED", "INTERESTED_FOLLOWUP", "REJECTED", "NOT_REACHABLE"])
            conv_val = round(random.uniform(50000, opp.potential_value * 0.5), 2) if outcome_type == "CONVERTED" else 0
            ao = ActionOutcome(
                id=str(uuid.uuid4()), action_id=action.id,
                outcome_type=outcome_type,
                converted_product_id=opp.product_id if outcome_type == "CONVERTED" else None,
                converted_value=conv_val,
                commission_eligible=outcome_type == "CONVERTED",
                notes=random.choice([
                    "Customer agreed to proceed with investment",
                    "Need follow-up in 2 weeks",
                    "Customer not interested at this time",
                    "Could not reach customer",
                    "Converted successfully — documents submitted"
                ]),
                recorded_at=now - timedelta(hours=random.randint(24, 168))
            )
            db.add(ao)

db.commit()
print(f"✓ {len(actions)} actions with history + outcomes")

# ═══════════════════════════════════════════════════════════════════
# 11. PERFORMANCE TARGETS & SNAPSHOTS
# ═══════════════════════════════════════════════════════════════════

q_start = date(2026, 7, 1)
q_end = date(2026, 9, 30)

for rm in all_rms:
    rm_actions = [a for a in actions if a.rm_id == rm.id]
    rm_opps = [o for o in opportunities if o.rm_id == rm.id]
    completed = [a for a in rm_actions if a.status == "COMPLETED"]
    converted_opps = [o for o in rm_opps if o.status == "CONVERTED"]
    overdue = [a for a in rm_actions if a.status in ["ASSIGNED", "IN_PROGRESS"] and a.due_date and a.due_date < now_naive]

    target_val = random.choice([5000000, 8000000, 10000000, 12000000])
    achievement_val = round(sum(o.potential_value for o in converted_opps) * random.uniform(0.3, 0.8), 2)
    pct = round((achievement_val / target_val) * 100, 2) if target_val else 0
    conv_rate = round(len(converted_opps) / max(len(rm_opps), 1), 3)
    status = "EXCEPTIONAL" if pct >= 100 else "HEALTHY" if pct >= 70 else "AT_RISK" if pct >= 40 else "CRITICAL"

    # Target (uses Date columns)
    t = Target(
        id=str(uuid.uuid4()), rm_id=rm.id, org_unit_id=rm.org_unit_id,
        metric_code="REVENUE", period_type="QUARTER",
        period_start=q_start, period_end=q_end,
        target_value=float(target_val), unit="INR", is_active=True
    )
    db.add(t)

    # RMPerformanceSnapshot (uses contributing_factors JSON for period/status/drivers)
    ps = RMPerformanceSnapshot(
        id=str(uuid.uuid4()), rm_id=rm.id,
        snapshot_date=today,
        target_value=float(target_val),
        achieved_value=achievement_val,
        achievement_percent=pct,
        expected_run_rate_percent=round(target_val * 0.33 / max(target_val, 1) * 100, 2),
        conversion_rate=conv_rate,
        activity_count=len(rm_actions),
        overdue_action_count=len(overdue),
        pipeline_value=round(sum(o.potential_value for o in rm_opps if o.status not in ["CONVERTED", "LOST"]), 2),
        sla_breach_count=float(len(overdue)),
        contributing_factors={
            "period": "2026-Q3",
            "status": status,
            "primary_drivers": ["conversion_rate", "pipeline_growth"] if pct >= 70 else ["overdue_actions", "low_activity"],
            "secondary_drivers": ["sla_compliance"] if len(overdue) > 2 else ["customer_satisfaction"],
            "recommended_intervention": "Maintain momentum, focus on PMS upsells" if pct >= 70 else "Prioritize overdue actions, increase customer contact frequency",
        }
    )
    db.add(ps)

    # Achievement badge
    if pct >= 50:
        ach = Achievement(
            id=str(uuid.uuid4()), rm_id=rm.id,
            achievement_type="QUARTERLY_TARGET" if pct >= 100 else "CONSISTENT_PERFORMER",
            title="Q3 Target Achieved" if pct >= 100 else "Steady Performer",
            description=f"Achieved {pct:.0f}% of quarterly target",
            period="2026-Q3", milestone_value=achievement_val,
            awarded_at=now
        )
        db.add(ach)

db.commit()
print("✓ Performance targets, snapshots, achievements")

# ═══════════════════════════════════════════════════════════════════
# 12. AUDIT RECORDS (hash chain)
# ═══════════════════════════════════════════════════════════════════

prev_hash = "0" * 64
audit_entities = (
    [(opp, "OPPORTUNITY", "CREATED") for opp in opportunities[:10]] +
    [(act, "ACTION", "CREATED") for act in actions[:8]] +
    [(act, "ACTION", "STATUS_CHANGED") for act in actions[:5] if act.status == "COMPLETED"]
)

for entity, etype, action_name in audit_entities:
    payload = {"entity_type": etype, "entity_id": entity.id, "action": action_name, "ts": now.isoformat()}
    payload_str = json.dumps(payload, sort_keys=True)
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
    current_hash = hashlib.sha256(f"{prev_hash}{payload_hash}".encode()).hexdigest()

    ar = AuditRecord(
        id=str(uuid.uuid4()), entity_type=etype, entity_id=entity.id,
        action=action_name, actor_id=getattr(entity, "rm_id", "system"),
        previous_hash=prev_hash, current_hash=current_hash, payload_hash=payload_hash,
        canonical_payload=payload,
        correlation_id=str(uuid.uuid4()),
        created_at=now - timedelta(hours=random.randint(1, 120))
    )
    db.add(ar)
    prev_hash = current_hash

db.commit()
print(f"✓ {len(audit_entities)} audit records")

# ═══════════════════════════════════════════════════════════════════
db.close()
print("\n" + "=" * 60)
print(" DATABASE SEEDED SUCCESSFULLY")
print("=" * 60)
print(f"  Org Units:      2")
print(f"  Profiles:       4 (1 manager, 3 RMs)")
print(f"  Products:       {len(products)}")
print(f"  Customers:      {len(customers)}")
print(f"  Holdings:       {len(holdings_data)}")
print(f"  Transactions:   {tx_count}")
print(f"  Interactions:   {int_count}")
print(f"  Leads:          {len(leads)}")
print(f"  Opportunities:  {len(opportunities)}")
print(f"  Actions:        {len(actions)}")
print(f"  Audit Records:  {len(audit_entities)}")
print("=" * 60)
print("\nDemo logins:")
print("  RM:      priya@crm.com  (Priya Sharma, 5 customers)")
print("  RM:      arjun@crm.com  (Arjun Mehta, 5 customers)")
print("  RM:      neha@crm.com   (Neha Kapoor, 5 customers)")
print("  Manager: vikram@crm.com (Vikram Seth)")
print()
print("Start backend:  .venv/Scripts/python -m uvicorn backend.services.core_server.main:app --port 8000")
print("Start frontend: cd frontend && npm run dev")
