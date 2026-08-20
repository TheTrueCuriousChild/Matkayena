"""Unit tests for Agent #3 — Manager Agent."""

from datetime import datetime, timezone
import pytest
from backend.services.event_intelligence_server.agents.manager_agent import ManagerAgent
from backend.services.shared.models import RMPerformanceSnapshot, Profile


@pytest.mark.asyncio
async def test_manager_alert_generation_and_throttling(db_session):
    # Clear alert cache
    ManagerAgent._alert_cooldowns.clear()

    rm_profile = Profile(
        id="rm_managed_1",
        email="rm_managed@crm.com",
        full_name="Vikram Seth",
        manager_id="mgr_head_1"
    )
    db_session.add(rm_profile)

    snapshot = RMPerformanceSnapshot(
        rm_id="rm_managed_1",
        period="2026-Q1",
        target=5_000_000.0,
        achievement=1_500_000.0,
        expected_run_rate=3_000_000.0,
        projected_value=2_000_000.0,
        conversion_rate=0.15,
        productivity=5.0,
        pipeline_value=500_000.0,
        sla_score=0.65,
        benchmark_delta=-1_500_000.0,
        status="CRITICAL",
        primary_drivers=["LAGGING_RUN_RATE"],
        secondary_drivers=["SLA_BREACHES"],
        recommended_intervention="Schedule emergency pipeline review",
        snapshot_at=datetime.now(timezone.utc)
    )
    db_session.add(snapshot)
    db_session.commit()

    # First evaluation generates an escalation/alert
    alerts1 = await ManagerAgent.evaluate_manager_intelligence(
        db=db_session,
        manager_id="mgr_head_1",
        period="2026-Q1"
    )
    assert len(alerts1) >= 1
    crit_alert = next((a for a in alerts1 if a.rm_id == "rm_managed_1"), None)
    assert crit_alert is not None
    assert crit_alert.severity in ["HIGH", "CRITICAL"]
    assert "Performance Risk" in crit_alert.title
    assert "LAGGING_RUN_RATE" in crit_alert.evidence["primary_drivers"]

    # Second evaluation immediately after is suppressed by cooldown to avoid spam
    alerts2 = await ManagerAgent.evaluate_manager_intelligence(
        db=db_session,
        manager_id="mgr_head_1",
        period="2026-Q1"
    )
    managed_alerts2 = [a for a in alerts2 if a.rm_id == "rm_managed_1" and a.alert_type == crit_alert.alert_type]
    assert len(managed_alerts2) == 0
