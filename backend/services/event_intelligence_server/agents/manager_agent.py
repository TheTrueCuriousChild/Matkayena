"""Agent #3 — Manager Agent.

Translates opportunity risks, target gaps, SLA breaches, and achievements into actionable,
prioritized managerial intelligence and alerts without spamming.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.shared.config import settings
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.logging import setup_logger
from backend.services.shared.models import (
    RMPerformanceSnapshot, Opportunity, Achievement, Profile
)
from backend.services.shared.repositories.performance_repo import PerformanceRepository

logger = setup_logger("manager_agent")
audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)


class ManagerAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    manager_id: Optional[str] = None
    rm_id: str
    alert_type: str  # MANAGER_ALERT, ESCALATION, ACHIEVEMENT, COACHING_RECOMMENDATION, OPPORTUNITY_RISK
    severity: str    # INFO, LOW, MEDIUM, HIGH, CRITICAL
    title: str
    summary: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    impact: str
    recommended_action: str
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ManagerAgent:
    AGENT_VERSION = "ManagerAgent_v1.0"
    # In-memory cooldown cache to prevent manager alert spam: key = (rm_id, alert_type) -> last_sent_time
    _alert_cooldowns: Dict[str, datetime] = {}

    @classmethod
    def _is_in_cooldown(cls, rm_id: str, alert_type: str, cooldown_hours: int = 4) -> bool:
        key = f"{rm_id}_{alert_type}"
        last_sent = cls._alert_cooldowns.get(key)
        if last_sent and (datetime.now(timezone.utc) - last_sent) < timedelta(hours=cooldown_hours):
            return True
        return False

    @classmethod
    def _record_alert_sent(cls, rm_id: str, alert_type: str) -> None:
        key = f"{rm_id}_{alert_type}"
        cls._alert_cooldowns[key] = datetime.now(timezone.utc)

    @classmethod
    async def evaluate_manager_intelligence(
        cls,
        db: Session,
        manager_id: Optional[str] = None,
        period: str = "2026-Q1",
        correlation_id: Optional[str] = None
    ) -> List[ManagerAlert]:
        """Scans all performance snapshots and high-priority items to synthesize manager alerts."""
        correlation_id = correlation_id or str(uuid.uuid4())
        alerts: List[ManagerAlert] = []

        # 1. Fetch RM snapshots
        query = db.query(RMPerformanceSnapshot).filter(RMPerformanceSnapshot.period == period)
        snapshots: List[RMPerformanceSnapshot] = query.all()

        for sn in snapshots:
            rm_profile = db.query(Profile).filter(Profile.id == sn.rm_id).first()
            assigned_manager = rm_profile.manager_id if rm_profile else manager_id

            # Filter if specific manager is querying
            if manager_id and assigned_manager and assigned_manager != manager_id:
                continue

            # Case A: Critical / At Risk Performance Alert
            if sn.status in ["AT_RISK", "CRITICAL"]:
                alert_type = "ESCALATION" if sn.status == "CRITICAL" else "MANAGER_ALERT"
                if not cls._is_in_cooldown(sn.rm_id, alert_type):
                    severity = "CRITICAL" if sn.status == "CRITICAL" else "HIGH"
                    alert = ManagerAlert(
                        manager_id=assigned_manager,
                        rm_id=sn.rm_id,
                        alert_type=alert_type,
                        severity=severity,
                        title=f"Performance Risk: RM {rm_profile.full_name if rm_profile else sn.rm_id} is {sn.status}",
                        summary=f"Achievement is ₹{int(sn.achievement):,} vs expected ₹{int(sn.expected_run_rate):,}. Conversion: {int(sn.conversion_rate*100)}%, SLA Score: {sn.sla_score:.2f}.",
                        evidence={
                            "primary_drivers": sn.primary_drivers,
                            "secondary_drivers": sn.secondary_drivers,
                            "target": sn.target,
                            "achievement": sn.achievement,
                            "sla_score": sn.sla_score,
                            "agent_version": cls.AGENT_VERSION
                        },
                        impact=f"Potential shortfall of ₹{int(sn.target - sn.achievement):,} against quarterly plan.",
                        recommended_action=sn.recommended_intervention or "Schedule 1-on-1 coaching session to reprioritize high-intent leads.",
                        correlation_id=correlation_id
                    )
                    alerts.append(alert)
                    cls._record_alert_sent(sn.rm_id, alert_type)

            # Case B: Exceptional Achievement Alert
            elif sn.status == "EXCEPTIONAL":
                if not cls._is_in_cooldown(sn.rm_id, "ACHIEVEMENT"):
                    alert = ManagerAlert(
                        manager_id=assigned_manager,
                        rm_id=sn.rm_id,
                        alert_type="ACHIEVEMENT",
                        severity="INFO",
                        title=f"Target Achieved Early: RM {rm_profile.full_name if rm_profile else sn.rm_id}",
                        summary=f"RM has exceeded target with ₹{int(sn.achievement):,} ({int((sn.achievement/sn.target)*100)}% of quota).",
                        evidence={"achievement": sn.achievement, "target": sn.target},
                        impact="Boosts overall team quota attainment ahead of cycle.",
                        recommended_action="Acknowledge in team standup and assign high-ticket institutional pipeline.",
                        correlation_id=correlation_id
                    )
                    alerts.append(alert)
                    cls._record_alert_sent(sn.rm_id, "ACHIEVEMENT")

        # 2. Check for High-Value Opportunities at Risk
        high_opps = db.query(Opportunity).filter(
            Opportunity.priority == "CRITICAL",
            Opportunity.status.in_(["DETECTED", "ASSIGNED"])
        ).limit(10).all()

        for opp in high_opps:
            if not cls._is_in_cooldown(opp.rm_id, f"OPPORTUNITY_RISK_{opp.id}"):
                alert = ManagerAlert(
                    manager_id=manager_id,
                    rm_id=opp.rm_id,
                    alert_type="OPPORTUNITY_RISK",
                    severity="HIGH",
                    title=f"High-Value Opportunity Pending RM Action: {opp.title}",
                    summary=f"Critical opportunity worth ₹{int(opp.estimated_value or 0):,} has not progressed past {opp.status}.",
                    evidence={"opportunity_id": opp.id, "score": opp.score, "type": opp.opportunity_type},
                    impact=f"Risk of losing ₹{int(opp.estimated_value or 0):,} conversion window.",
                    recommended_action="Ensure RM makes immediate priority contact today.",
                    correlation_id=correlation_id
                )
                alerts.append(alert)
                cls._record_alert_sent(opp.rm_id, f"OPPORTUNITY_RISK_{opp.id}")

        return alerts
