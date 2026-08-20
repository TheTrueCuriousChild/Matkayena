"""Repository for Leads."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import Lead


class LeadRepository:
    @staticmethod
    def get_by_id(db: Session, lead_id: str) -> Optional[Lead]:
        return db.query(Lead).filter(Lead.id == lead_id).first()

    @staticmethod
    def list_by_rm(db: Session, rm_id: str, stage: Optional[str] = None, limit: int = 100) -> List[Lead]:
        query = db.query(Lead).filter(Lead.assigned_rm_id == rm_id)
        if stage:
            query = query.filter(Lead.stage == stage)
        return query.order_by(Lead.created_at.desc()).limit(limit).all()

    @staticmethod
    def list_by_customer(db: Session, customer_id: str) -> List[Lead]:
        return db.query(Lead).filter(Lead.customer_id == customer_id).all()

    @staticmethod
    def create_lead(db: Session, lead: Lead) -> Lead:
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def update_stage(db: Session, lead_id: str, stage: str) -> Optional[Lead]:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.stage = stage
            db.commit()
            db.refresh(lead)
        return lead
