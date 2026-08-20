"""Unit tests for Agent #1 — Opportunity Agent."""

import pytest
from backend.services.event_intelligence_server.agents.opportunity_agent import OpportunityAgent
from backend.services.event_intelligence_server.scoring.opportunity_scorer import OpportunityScorer
from backend.services.shared.events import EventEnvelope, EventTypeEnum
from backend.services.shared.models import Customer, CustomerProduct, Opportunity


@pytest.mark.asyncio
async def test_insurance_cross_sell_detection_on_payin(db_session):
    # Setup Customer with MF holding only
    customer = Customer(
        id="cust_test_101",
        customer_code="CUST101",
        first_name="Rahul",
        last_name="Sharma",
        segment="HNI",
        relationship_value=500000.0,
        primary_rm_id="rm_test_1",
        status="ACTIVE"
    )
    db_session.add(customer)
    holding = CustomerProduct(customer_id="cust_test_101", product_id="prod_mf_1", holding_value=500000.0)
    db_session.add(holding)
    db_session.commit()

    # Payin event of 1,50,000 INR
    event = EventEnvelope(
        event_type=EventTypeEnum.PAYIN_RECEIVED,
        entity_type="CUSTOMER",
        entity_id="cust_test_101",
        payload={"amount": 150000.0, "customer_id": "cust_test_101"},
        correlation_id="corr_payin_1"
    )

    opps = await OpportunityAgent.evaluate_event(db_session, event)
    assert len(opps) == 1
    opp = opps[0]

    assert opp.opportunity_type == "CROSS_SELL"
    assert opp.customer_id == "cust_test_101"
    assert opp.rm_id == "rm_test_1"
    assert opp.score >= 0.60
    assert "NO_INSURANCE_HOLDING" in opp.reason_codes
    assert opp.evidence["agent_version"] == "OpportunityAgent_v1.0"
    assert "signals" in opp.evidence
    assert opp.correlation_id == "corr_payin_1"


@pytest.mark.asyncio
async def test_dormant_customer_reactivation(db_session):
    customer = Customer(
        id="cust_dormant_1",
        customer_code="CUST_DORMANT",
        first_name="Amit",
        last_name="Verma",
        segment="RETAIL",
        relationship_value=100000.0,
        primary_rm_id="rm_test_1",
        status="DORMANT"
    )
    db_session.add(customer)
    db_session.commit()

    opps = await OpportunityAgent.evaluate_customer(db_session, "cust_dormant_1")
    dormant_opps = [o for o in opps if o.opportunity_type == "DORMANT_REACTIVATION"]
    assert len(dormant_opps) == 1
    assert dormant_opps[0].priority in ["LOW", "MEDIUM", "HIGH"]
    assert "DORMANT_STATUS" in dormant_opps[0].reason_codes


@pytest.mark.asyncio
async def test_opportunity_deduplication(db_session):
    customer = Customer(
        id="cust_dedup_1",
        customer_code="CUST_DEDUP",
        first_name="Pooja",
        last_name="Hegde",
        segment="HNI",
        relationship_value=300000.0,
        primary_rm_id="rm_test_1",
        status="ACTIVE"
    )
    db_session.add(customer)
    db_session.commit()

    event = EventEnvelope(
        event_type=EventTypeEnum.PAYIN_RECEIVED,
        entity_type="CUSTOMER",
        entity_id="cust_dedup_1",
        payload={"amount": 100000.0, "customer_id": "cust_dedup_1"},
        correlation_id="corr_dedup_1"
    )

    # First evaluation creates opportunity
    opps1 = await OpportunityAgent.evaluate_event(db_session, event)
    assert len(opps1) == 1

    # Second evaluation with the exact same condition suppresses duplicate creation
    opps2 = await OpportunityAgent.evaluate_event(db_session, event)
    assert len(opps2) == 0


def test_deterministic_scoring():
    weights = {"payin_weight": 0.4, "segment_weight": 0.3, "product_gap_weight": 0.3}
    signals = {"payin": 0.8, "segment": 0.9, "product_gap": 1.0}

    score1, breakdown1 = OpportunityScorer.calculate_score(weights, signals)
    score2, breakdown2 = OpportunityScorer.calculate_score(weights, signals)

    # Must be 100% deterministic
    assert score1 == score2
    assert score1 == 0.89
    assert breakdown1 == breakdown2
