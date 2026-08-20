"""Agent #2 — Performance Agent.

Continuously evaluates RM & Team performance metrics, diagnoses risks, detects achievements,
and derives explainable performance snapshots.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from backend.services.shared.config import settings
from backend.services.shared.events import EventEnvelope
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.logging import setup_logger
from backend.services.shared.models import (
    RMPerformanceSnapshot, Target, Benchmark, Achievement, Action, Lead, Profile
)
from backend.services.shared.repositories.action_repo import ActionRepository
from backend.services.shared.repositories.lead_repo import LeadRepository
from backend.services.shared.repositories.performance_repo import PerformanceRepository

logger = setup_logger("performance_agent")
audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)


class PerformanceAgent:
    AGENT_VERSION = "PerformanceAgent_v1.0"

    @classmethod
    async def evaluate_event(cls, db: Session, event: EventEnvelope) -> Optional[RMPerformanceSnapshot]:
        """Recalculates performance for the affected RM when a relevant conversion or action event arrives."""
        rm_id = event.payload.get("rm_id") or event.actor_id
        if not rm_id:
            return None

        period = event.payload.get("period", "2026-Q1")
        return await cls.evaluate_rm(db, rm_id=rm_id, period=period, correlation_id=event.correlation_id)

    @classmethod
    async def evaluate_rm(
        cls,
        db: Session,
        rm_id: str,
        period: str = "2026-Q1",
        correlation_id: Optional[str] = None
    ) -> RMPerformanceSnapshot:
        """Evaluates all performance metrics for an RM from actual stored transactions, targets, and actions."""
        correlation_id = correlation_id or str(uuid.uuid4())
        logger.info(f"PerformanceAgent evaluating RM {rm_id} for period {period}")

        # 1. Fetch Target
        target_record = PerformanceRepository.get_target(db, rm_id=rm_id, period=period)
        target_amount = target_record.target_amount if target_record else 1_000_000.0  # 10 Lakhs default
        achieved_amount = target_record.achieved_amount if target_record else 0.0

        # Calculate achievement %
        achievement_pct = achieved_amount / target_amount if target_amount > 0 else 0.0

        # 2. Fetch Actions & SLA status
        rm_actions: List[Action] = ActionRepository.list_by_rm(db, rm_id=rm_id, limit=200)
        total_actions = len(rm_actions)
        completed_actions = [a for a in rm_actions if a.status == "COMPLETED"]
        
        # SLA score: 1.0 minus penalty for overdue tasks
        now_dt = datetime.now(timezone.utc)
        def is_action_overdue(act: Action) -> bool:
            if not act.due_date:
                return False
            d_date = act.due_date if act.due_date.tzinfo is not None else act.due_date.replace(tzinfo=timezone.utc)
            return d_date < now_dt and act.status not in ["COMPLETED", "REJECTED"]

        overdue_actions = [a for a in rm_actions if is_action_overdue(a)]
        sla_score = max(0.0, 1.0 - (len(overdue_actions) * 0.15))

        # 3. Fetch Leads & Conversion Rate
        rm_leads: List[Lead] = LeadRepository.list_by_rm(db, rm_id=rm_id, limit=200)
        total_leads = len(rm_leads)
        converted_leads = [l for l in rm_leads if l.stage == "CONVERTED"]
        conversion_rate = (len(converted_leads) / total_leads) if total_leads > 0 else 0.25

        pipeline_value = sum((l.estimated_value or 0.0) for l in rm_leads if l.stage not in ["CONVERTED", "LOST"])

        # 4. Run-rate & Projected Value
        # Assuming midway through the period (day 45 of 90)
        expected_run_rate = target_amount * 0.60
        projected_value = achieved_amount + (pipeline_value * conversion_rate)

        # 5. Benchmark Comparison
        benchmark = PerformanceRepository.get_benchmark(db, metric_name="QUARTERLY_REVENUE", period=period)
        team_avg = benchmark.team_average if benchmark else (target_amount * 0.75)
        benchmark_delta = achieved_amount - team_avg

        # 6. Diagnosis and Drivers
        primary_drivers = []
        secondary_drivers = []
        status = "ON_TRACK"
        recommended_intervention = None

        if achievement_pct >= 1.00:
            status = "EXCEPTIONAL"
            primary_drivers.append("EARLY_TARGET_ACHIEVEMENT")
            if conversion_rate > 0.40:
                secondary_drivers.append("HIGH_CONVERSION_EFFICIENCY")
            # Record Achievement
            cls._check_and_record_achievement(
                db=db,
                rm_id=rm_id,
                ach_type="EARLY_TARGET_ACHIEVEMENT",
                title="Target Achieved Early",
                metric_value=achieved_amount,
                period=period
            )
        elif achievement_pct >= 0.80 and sla_score >= 0.85:
            status = "HEALTHY"
            primary_drivers.append("STRONG_PACING_AND_HIGH_SLA")
        elif achieved_amount < expected_run_rate or len(overdue_actions) >= 3 or conversion_rate < 0.20:
            status = "AT_RISK" if achieved_amount >= (expected_run_rate * 0.6) else "CRITICAL"
            if achieved_amount < expected_run_rate:
                primary_drivers.append(f"LAGGING_RUN_RATE (₹{int(achieved_amount):,} vs expected ₹{int(expected_run_rate):,})")
            if len(overdue_actions) >= 3:
                secondary_drivers.append(f"SLA_BREACHES ({len(overdue_actions)} overdue follow-up actions)")
            if conversion_rate < 0.20:
                secondary_drivers.append(f"LOW_CONVERSION_RATE ({int(conversion_rate * 100)}%)")

            recommended_intervention = "Manager review required: Reprioritize high-value untouched pipeline leads and address overdue follow-ups."
        else:
            status = "ON_TRACK"
            primary_drivers.append("NORMAL_PACING")

        # 7. Persist Performance Snapshot
        snapshot = RMPerformanceSnapshot(
            rm_id=rm_id,
            period=period,
            target=target_amount,
            achievement=achieved_amount,
            expected_run_rate=expected_run_rate,
            projected_value=projected_value,
            conversion_rate=round(conversion_rate, 3),
            productivity=float(len(completed_actions)),
            pipeline_value=pipeline_value,
            sla_score=round(sla_score, 2),
            benchmark_delta=benchmark_delta,
            status=status,
            primary_drivers=primary_drivers,
            secondary_drivers=secondary_drivers,
            recommended_intervention=recommended_intervention,
            snapshot_at=datetime.now(timezone.utc)
        )
        snapshot = PerformanceRepository.save_snapshot(db, snapshot)

        # 8. Record Audit in Server 4
        try:
            await audit_client.post(
                "/api/v1/audit/record",
                json_data={
                    "entity_type": "PERFORMANCE_SNAPSHOT",
                    "entity_id": snapshot.id,
                    "action": "PERFORMANCE_EVALUATED",
                    "payload": {
                        "rm_id": rm_id,
                        "status": status,
                        "achievement_pct": round(achievement_pct, 2),
                        "drivers": primary_drivers + secondary_drivers,
                        "agent_version": cls.AGENT_VERSION
                    },
                    "actor_id": "performance_agent",
                    "correlation_id": correlation_id
                },
                correlation_id=correlation_id,
                source_service="event_intelligence_server"
            )
        except Exception:
            pass

        return snapshot

    @classmethod
    def _check_and_record_achievement(
        cls,
        db: Session,
        rm_id: str,
        ach_type: str,
        title: str,
        metric_value: float,
        period: str
    ) -> None:
        """Records positive RM achievement if not already awarded."""
        existing = db.query(Achievement).filter(
            Achievement.rm_id == rm_id,
            Achievement.achievement_type == ach_type,
            Achievement.period == period
        ).first()

        if not existing:
            ach = Achievement(
                rm_id=rm_id,
                achievement_type=ach_type,
                title=title,
                description=f"RM reached ₹{int(metric_value):,} revenue in {period}",
                metric_value=metric_value,
                period=period,
                evidence={"evaluated_by": cls.AGENT_VERSION}
            )
            PerformanceRepository.record_achievement(db, ach)
            logger.info(f"Achievement recorded for RM {rm_id}: {title}")
