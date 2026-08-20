"""End-to-End Closed Loop Integration Test.

Tests the full closed loop:
EVENT -> INGEST -> AGENT -> OPPORTUNITY -> ACTION -> OUTCOME -> COMMISSION -> AUDIT -> BLOCKCHAIN
"""

import pytest
from backend.services.shared.auth import create_access_token, RoleEnum
from backend.services.shared.models import Customer, Product, CustomerProduct, Opportunity, Action, ActionOutcome, AuditRecord, BlockchainRecord
from backend.services.action_commission_server.commission.engine import DeterministicCommissionEngine
from backend.services.audit_blockchain_server.audit.hash_chain import AuditHashChainService
from backend.services.audit_blockchain_server.blockchain.queue import BlockchainAnchorWorker
from backend.services.event_intelligence_server.agents.opportunity_agent import OpportunityAgent
from backend.services.shared.events import EventEnvelope, EventTypeEnum


@pytest.mark.asyncio
async def test_full_closed_loop(db_session, audit_client):
    # 1. Setup Customer with Mutual Fund holding, but no Insurance
    customer = Customer(
        id="cust_closed_loop_1",
        customer_code="CUST_LOOP",
        first_name="Ananya",
        last_name="Roy",
        segment="ULTRA_HNI",
        relationship_value=2_000_000.0,
        primary_rm_id="rm_alpha",
        status="ACTIVE"
    )
    db_session.add(customer)
    holding = CustomerProduct(customer_id=customer.id, product_id="prod_mf_1", holding_value=2_000_000.0)
    db_session.add(holding)
    db_session.commit()

    correlation_id = "corr_closed_loop_e2e_1001"

    # 2. Ingest Large Investment Event (₹5,00,000)
    payin_event = EventEnvelope(
        event_type=EventTypeEnum.PAYIN_RECEIVED,
        entity_type="CUSTOMER",
        entity_id=customer.id,
        payload={"amount": 500000.0, "customer_id": customer.id},
        correlation_id=correlation_id
    )

    # 3. Opportunity Agent processes event
    opps = await OpportunityAgent.evaluate_event(db_session, payin_event)
    assert len(opps) == 1
    opp = opps[0]
    assert opp.opportunity_type == "CROSS_SELL"
    assert opp.customer_id == customer.id
    assert opp.rm_id == "rm_alpha"
    assert opp.correlation_id == correlation_id

    # 4. Action is assigned to RM
    action = Action(
        id="act_closed_loop_1",
        opportunity_id=opp.id,
        customer_id=customer.id,
        assigned_rm_id="rm_alpha",
        title=f"Follow-up: {opp.title}",
        action_type="OFFER_PRODUCT",
        status="ASSIGNED",
        priority=opp.priority,
        correlation_id=correlation_id
    )
    db_session.add(action)
    db_session.commit()

    # 5. RM executes action and customer converts (₹5,00,000 Insurance Policy)
    action.status = "COMPLETED"
    outcome = ActionOutcome(
        action_id=action.id,
        outcome_type="CONVERTED",
        converted_product_id="prod_ins_1",
        converted_value=500000.0,
        commission_eligible=True
    )
    db_session.add(outcome)
    db_session.commit()

    # 6. Commission Engine calculates deterministic commission
    # Product: INSURANCE (5%), Segment: ULTRA_HNI (1.25x), Volume >= 5L (1.05x)
    # Base: 500,000 * 0.05 = 25,000
    # Final: 25,000 * 1.25 * 1.05 = 32,812.50
    commission = DeterministicCommissionEngine.calculate(
        converted_value=500000.0,
        product_category="INSURANCE",
        customer_segment="ULTRA_HNI",
        rm_id="rm_alpha",
        is_eligible=True
    )
    assert commission.final_commission_amount == 32812.50

    # 7. Audit hash-chain record is created
    audit_rec = AuditHashChainService.create_audit_entry(
        db=db_session,
        entity_type="CONVERSION_COMMISSION",
        entity_id=action.id,
        action="CONVERSION_COMPLETED",
        payload={
            "action_id": action.id,
            "opportunity_id": opp.id,
            "converted_value": 500000.0,
            "commission_amount": commission.final_commission_amount
        },
        actor_id="rm_alpha",
        correlation_id=correlation_id
    )
    assert audit_rec.id is not None
    assert len(audit_rec.current_hash) == 64

    # 8. Blockchain / Integrity Ledger Anchoring
    blockchain_rec = await BlockchainAnchorWorker.anchor_audit_record_isolated(db_session, audit_rec)
    assert blockchain_rec.status == "ANCHORED"
    assert blockchain_rec.tx_hash.startswith("0x")

    # 9. Verify hash chain integrity across the system
    chain_status = AuditHashChainService.verify_chain_integrity(db_session)
    assert chain_status["is_valid"] is True
    assert chain_status["status"] == "VERIFIED_UNBROKEN"
