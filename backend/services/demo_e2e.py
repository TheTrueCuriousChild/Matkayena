"""Interactive End-to-End Demo Script for PS-02 Closed Loop.

Demonstrates:
1. Payin Event Ingestion
2. Opportunity Agent (Insurance Cross-Sell Detection & Scoring)
3. Action Lifecycle (Assignment & Completion)
4. Deterministic Commission Calculation (0% LLM)
5. Performance Agent Re-evaluation
6. Manager Agent Intelligence & Alert Synthesis
7. SHA-256 Hash Chain Audit & Blockchain Anchoring Proof
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

# Add project root to Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.services.shared.database import Base, init_db, SessionLocal
from backend.services.shared.models import Customer, Product, CustomerProduct, Target
from backend.services.event_intelligence_server.agents.opportunity_agent import OpportunityAgent
from backend.services.event_intelligence_server.agents.performance_agent import PerformanceAgent
from backend.services.event_intelligence_server.agents.manager_agent import ManagerAgent
from backend.services.action_commission_server.commission.engine import DeterministicCommissionEngine
from backend.services.audit_blockchain_server.audit.hash_chain import AuditHashChainService
from backend.services.audit_blockchain_server.blockchain.queue import BlockchainAnchorWorker
from backend.services.shared.events import EventEnvelope, EventTypeEnum


def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def run_demo():
    print_section("PS-02 LIVE CLOSED-LOOP DEMONSTRATION")
    init_db()
    db = SessionLocal()

    try:
        # Step 0: Setup Demo Products & Customer
        print("\n[Step 0] Initializing Customer & Products Context...")
        if not db.query(Product).filter(Product.category == "INSURANCE").first():
            ins = Product(id="prod_ins_demo", code="TERM_LIFE", name="Term Life Protection", category="INSURANCE", base_commission_rate=0.05)
            mf = Product(id="prod_mf_demo", code="GROWTH_MF", name="Growth Mutual Fund", category="MUTUAL_FUND", base_commission_rate=0.015)
            db.add_all([ins, mf])
            db.commit()

        customer = db.query(Customer).filter(Customer.customer_code == "DEMO_CUST_01").first()
        if not customer:
            customer = Customer(
                id="cust_demo_01",
                customer_code="DEMO_CUST_01",
                first_name="Vikram",
                last_name="Malhotra",
                segment="ULTRA_HNI",
                relationship_value=2500000.0,
                primary_rm_id="rm_demo_priya",
                status="ACTIVE"
            )
            db.add(customer)
            db.commit()

        # Add initial MF holding (Customer has MF, but NO Insurance)
        holding = db.query(CustomerProduct).filter(CustomerProduct.customer_id == customer.id).first()
        if not holding:
            holding = CustomerProduct(customer_id=customer.id, product_id="prod_mf_demo", holding_value=2500000.0)
            db.add(holding)
            db.commit()

        print(f"  ✓ Customer: {customer.first_name} {customer.last_name} ({customer.segment})")
        print(f"  ✓ Existing Holdings: Mutual Fund (₹25,00,000)")
        print(f"  ✓ Product Gap: No Insurance Holding")

        # Step 1: Customer deposits ₹5,00,000 for investment
        print_section("STEP 1: INGESTING PAYIN EVENT (₹5,00,000)")
        correlation_id = f"corr_demo_{int(datetime.now().timestamp())}"
        payin_event = EventEnvelope(
            event_type=EventTypeEnum.PAYIN_RECEIVED,
            entity_type="CUSTOMER",
            entity_id=customer.id,
            payload={"amount": 500000.0, "customer_id": customer.id},
            correlation_id=correlation_id
        )
        print(f"  Event Type:      {payin_event.event_type.value}")
        print(f"  Deposit Amount:  ₹{payin_event.payload['amount']:,}")
        print(f"  Correlation ID:  {correlation_id}")

        # Step 2: Opportunity Agent Evaluates Event
        print_section("STEP 2: AGENT #1 — OPPORTUNITY AGENT EVALUATION")
        opps = await OpportunityAgent.evaluate_event(db, payin_event)
        opp = opps[0] if opps else None
        if opp:
            print(f"  ✓ Opportunity Detected: {opp.opportunity_type}")
            print(f"  ✓ Title:                {opp.title}")
            print(f"  ✓ Score:                {opp.score:.2f} ({opp.priority} Priority)")
            print(f"  ✓ Recommended Action:   {opp.recommended_action}")
            print(f"  ✓ Reasons:              {', '.join(opp.reason_codes)}")
            print(f"  ✓ Agent Version:        {opp.evidence.get('agent_version')}")

        # Step 3: RM Executes Action & Converts Customer
        print_section("STEP 3: ACTION LIFECYCLE & CONVERSION")
        converted_value = 500000.0
        print(f"  RM 'rm_demo_priya' contacts customer Vikram Malhotra.")
        print(f"  Outcome: CONVERTED -> Customer purchases ₹{converted_value:,.2f} Insurance policy.")

        # Step 4: Deterministic Commission Engine
        print_section("STEP 4: DETERMINISTIC COMMISSION CALCULATION (0% LLM)")
        commission = DeterministicCommissionEngine.calculate(
            converted_value=converted_value,
            product_category="INSURANCE",
            customer_segment="ULTRA_HNI",
            rm_id="rm_demo_priya",
            is_eligible=True
        )
        print(f"  ✓ Base Product Rate:     {commission.base_rate * 100}%")
        print(f"  ✓ Segment Multiplier:    {commission.segment_multiplier}x (ULTRA_HNI)")
        print(f"  ✓ Volume Tier Bonus:     {commission.volume_multiplier}x (>= 5 Lakhs)")
        print(f"  ✓ Formula:               converted_value * base_rate * segment_mult * volume_mult")
        print(f"  ✓ Base Commission:       ₹{commission.base_commission_amount:,.2f}")
        print(f"  ✓ FINAL COMMISSION:      ₹{commission.final_commission_amount:,.2f}")

        # Step 5: Performance Agent Re-evaluates RM
        print_section("STEP 5: AGENT #2 — PERFORMANCE AGENT EVALUATION")
        target = db.query(Target).filter(Target.rm_id == "rm_demo_priya").first()
        if not target:
            target = Target(
                rm_id="rm_demo_priya",
                period="2026-Q1",
                target_amount=1000000.0,
                achieved_amount=converted_value,
                start_date=datetime.now().date(),
                end_date=datetime.now().date()
            )
            db.add(target)
            db.commit()
        else:
            target.achieved_amount += converted_value
            db.commit()

        snapshot = await PerformanceAgent.evaluate_rm(db, rm_id="rm_demo_priya", period="2026-Q1", correlation_id=correlation_id)
        print(f"  ✓ RM Status:             {snapshot.status}")
        print(f"  ✓ Quota Achieved:        ₹{snapshot.achievement:,.2f} / ₹{snapshot.target:,.2f} ({int((snapshot.achievement/snapshot.target)*100)}%)")
        print(f"  ✓ Conversion Rate:       {int(snapshot.conversion_rate*100)}%")
        print(f"  ✓ Primary Drivers:       {', '.join(snapshot.primary_drivers)}")

        # Step 6: Manager Agent Intelligence Synthesis
        print_section("STEP 6: AGENT #3 — MANAGER AGENT INTELLIGENCE")
        alerts = await ManagerAgent.evaluate_manager_intelligence(db, period="2026-Q1", correlation_id=correlation_id)
        if alerts:
            for a in alerts[:2]:
                print(f"  [{a.severity}] {a.alert_type}: {a.title}")
                print(f"    Summary: {a.summary}")
                print(f"    Action:  {a.recommended_action}")
        else:
            print("  ✓ All metrics healthy. No critical manager escalations active.")

        # Step 7: Cryptographic Hash Chain & Blockchain Proof
        print_section("STEP 7: SHA-256 HASH CHAIN & BLOCKCHAIN ANCHOR")
        audit_record = AuditHashChainService.create_audit_entry(
            db=db,
            entity_type="CONVERSION",
            entity_id="act_demo_conv_1",
            action="COMMISSION_AWARDED",
            payload={
                "customer": "Vikram Malhotra",
                "converted_value": converted_value,
                "commission_awarded": commission.final_commission_amount,
                "rm_id": "rm_demo_priya"
            },
            actor_id="rm_demo_priya",
            correlation_id=correlation_id
        )
        print(f"  ✓ Previous Hash:  {audit_record.previous_hash}")
        print(f"  ✓ Current Hash:   {audit_record.current_hash}")
        print(f"  ✓ Payload Hash:   {audit_record.payload_hash}")

        # Anchor proof
        b_record = await BlockchainAnchorWorker.anchor_audit_record_isolated(db, audit_record)
        print(f"  ✓ Blockchain Status:  {b_record.status}")
        print(f"  ✓ Tx Proof Hash:      {b_record.tx_hash}")
        print(f"  ✓ Network:            {b_record.blockchain_network}")

        # Verify chain integrity
        verification = AuditHashChainService.verify_chain_integrity(db)
        print(f"  ✓ Chain Verification: {verification['status']} (Valid: {verification['is_valid']}, Total Blocks: {verification['total_records']})")

        print_section("CLOSED LOOP COMPLETE — 100% TRACEABLE & AUDITABLE")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
