"""Unit tests for Agent #2 — Performance Agent."""

from datetime import date, datetime, timedelta, timezone
import pytest
from backend.services.event_intelligence_server.agents.performance_agent import PerformanceAgent
from backend.services.shared.models import Target, Action, Lead, Achievement


@pytest.mark.asyncio
async def test_performance_at_risk_diagnosis(db_session):
    rm_id = "rm_lagging_1"
    period = "2026-Q1"

    # 1. Target = ₹50L, Achieved = ₹20L (below expected run-rate ₹30L)
    target = Target(
        rm_id=rm_id,
        period=period,
        target_amount=5_000_000.0,
        achieved_amount=2_000_000.0,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31)
    )
    db_session.add(target)

    # 2. Add 4 overdue actions to trigger SLA breaches
    for i in range(4):
        act = Action(
            id=f"act_overdue_{i}",
            customer_id="cust_test_101",
            assigned_rm_id=rm_id,
            title=f"Overdue Followup {i}",
            action_type="CALL_CUSTOMER",
            status="ASSIGNED",
            priority="HIGH",
            due_date=datetime.now(timezone.utc) - timedelta(days=2),
            correlation_id="corr_sla_1"
        )
        db_session.add(act)

    db_session.commit()

    snapshot = await PerformanceAgent.evaluate_rm(db_session, rm_id=rm_id, period=period)

    assert snapshot.status in ["AT_RISK", "CRITICAL"]
    assert snapshot.achievement == 2_000_000.0
    assert snapshot.sla_score < 0.80
    assert any("LAGGING_RUN_RATE" in d for d in snapshot.primary_drivers)
    assert any("SLA_BREACHES" in d for d in snapshot.secondary_drivers)
    assert snapshot.recommended_intervention is not None


@pytest.mark.asyncio
async def test_performance_early_achievement_detection(db_session):
    rm_id = "rm_star_1"
    period = "2026-Q1"

    # Target = ₹10L, Achieved = ₹12L
    target = Target(
        rm_id=rm_id,
        period=period,
        target_amount=1_000_000.0,
        achieved_amount=1_200_000.0,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31)
    )
    db_session.add(target)
    db_session.commit()

    snapshot = await PerformanceAgent.evaluate_rm(db_session, rm_id=rm_id, period=period)

    assert snapshot.status == "EXCEPTIONAL"
    assert "EARLY_TARGET_ACHIEVEMENT" in snapshot.primary_drivers

    # Verify Achievement record was inserted in DB
    ach = db_session.query(Achievement).filter(
        Achievement.rm_id == rm_id,
        Achievement.achievement_type == "EARLY_TARGET_ACHIEVEMENT"
    ).first()
    assert ach is not None
    assert ach.metric_value == 1_200_000.0
