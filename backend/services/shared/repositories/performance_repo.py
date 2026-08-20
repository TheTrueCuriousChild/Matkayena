"""Repository for RM Targets, Benchmarks, Performance Snapshots, and Achievements."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import (
    Target, Benchmark, RMPerformanceSnapshot, Achievement
)


class PerformanceRepository:
    @staticmethod
    def get_target(db: Session, rm_id: str, period: str) -> Optional[Target]:
        targets = db.query(Target).filter(Target.rm_id == rm_id).all()
        for t in targets:
            if t.period == period or getattr(t, "_period", "") == period:
                return t
        return targets[0] if targets else None

    @staticmethod
    def upsert_target(db: Session, target: Target) -> Target:
        targets = db.query(Target).filter(Target.rm_id == target.rm_id).all()
        existing = next((t for t in targets if t.period == target.period or getattr(t, "_period", "") == target.period), None)
        if existing:
            existing.target_amount = target.target_amount
            existing.achieved_amount = target.achieved_amount
            existing.target_leads = getattr(target, "target_leads", 0)
            existing.achieved_leads = getattr(target, "achieved_leads", 0)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            db.add(target)
            db.commit()
            db.refresh(target)
            return target

    @staticmethod
    def get_benchmark(db: Session, metric_name: str, period: str, org_unit_id: Optional[str] = None) -> Optional[Benchmark]:
        benchmarks = db.query(Benchmark).all()
        for b in benchmarks:
            if (b.metric_code == metric_name or getattr(b, "metric_name", "") == metric_name):
                if not org_unit_id or b.org_unit_id == org_unit_id:
                    return b
        return None

    @staticmethod
    def save_snapshot(db: Session, snapshot: RMPerformanceSnapshot) -> RMPerformanceSnapshot:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get_latest_snapshot(db: Session, rm_id: str, period: str) -> Optional[RMPerformanceSnapshot]:
        snaps = db.query(RMPerformanceSnapshot).filter(RMPerformanceSnapshot.rm_id == rm_id).all()
        filtered = [s for s in snaps if s.period == period or getattr(s, "_period", "") == period]
        return filtered[-1] if filtered else None


    @staticmethod
    def record_achievement(db: Session, achievement: Achievement) -> Achievement:
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        return achievement

    @staticmethod
    def list_achievements(db: Session, rm_id: Optional[str] = None, limit: int = 50) -> List[Achievement]:
        query = db.query(Achievement)
        if rm_id:
            query = query.filter(Achievement.rm_id == rm_id)
        return query.order_by(Achievement.created_at.desc()).limit(limit).all()
