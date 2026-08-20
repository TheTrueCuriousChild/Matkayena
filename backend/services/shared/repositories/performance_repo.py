"""Repository for RM Targets, Benchmarks, Performance Snapshots, and Achievements."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import (
    Target, Benchmark, RMPerformanceSnapshot, Achievement
)


class PerformanceRepository:
    @staticmethod
    def get_target(db: Session, rm_id: str, period: str) -> Optional[Target]:
        return db.query(Target).filter(
            Target.rm_id == rm_id,
            Target.period == period
        ).first()

    @staticmethod
    def upsert_target(db: Session, target: Target) -> Target:
        existing = db.query(Target).filter(
            Target.rm_id == target.rm_id,
            Target.period == target.period
        ).first()
        if existing:
            existing.target_amount = target.target_amount
            existing.achieved_amount = target.achieved_amount
            existing.target_leads = target.target_leads
            existing.achieved_leads = target.achieved_leads
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
        query = db.query(Benchmark).filter(
            Benchmark.metric_name == metric_name,
            Benchmark.period == period
        )
        if org_unit_id:
            query = query.filter(Benchmark.org_unit_id == org_unit_id)
        return query.first()

    @staticmethod
    def save_snapshot(db: Session, snapshot: RMPerformanceSnapshot) -> RMPerformanceSnapshot:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get_latest_snapshot(db: Session, rm_id: str, period: str) -> Optional[RMPerformanceSnapshot]:
        return db.query(RMPerformanceSnapshot).filter(
            RMPerformanceSnapshot.rm_id == rm_id,
            RMPerformanceSnapshot.period == period
        ).order_by(RMPerformanceSnapshot.snapshot_at.desc()).first()

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
