"""Repository for Commercial Opportunities."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import Opportunity


class OpportunityRepository:
    @staticmethod
    def get_by_id(db: Session, opp_id: str) -> Optional[Opportunity]:
        return db.query(Opportunity).filter(Opportunity.id == opp_id).first()

    @staticmethod
    def list_by_rm(db: Session, rm_id: str, status: Optional[str] = None, limit: int = 100) -> List[Opportunity]:
        query = db.query(Opportunity).filter(Opportunity.rm_id == rm_id)
        if status:
            query = query.filter(Opportunity.status == status)
        return query.order_by(Opportunity.score.desc(), Opportunity.created_at.desc()).limit(limit).all()

    @staticmethod
    def list_by_customer(db: Session, customer_id: str, open_only: bool = True) -> List[Opportunity]:
        query = db.query(Opportunity).filter(Opportunity.customer_id == customer_id)
        if open_only:
            query = query.filter(Opportunity.status.in_(["DETECTED", "ASSIGNED", "CONTACT_PENDING", "CONTACTED", "INTERESTED"]))
        return query.order_by(Opportunity.created_at.desc()).all()

    @staticmethod
    def find_duplicate_active(
        db: Session,
        customer_id: str,
        opportunity_type: str,
        product_id: Optional[str] = None
    ) -> Optional[Opportunity]:
        """Finds existing unresolved opportunity for the same customer, type, and product to prevent duplicates."""
        query = db.query(Opportunity).filter(
            Opportunity.customer_id == customer_id,
            Opportunity.opportunity_type == opportunity_type,
            Opportunity.status.in_(["DETECTED", "ASSIGNED", "CONTACT_PENDING", "CONTACTED", "INTERESTED"])
        )
        if product_id:
            query = query.filter(Opportunity.product_id == product_id)
        return query.first()

    @staticmethod
    def create_opportunity(db: Session, opp: Opportunity) -> Opportunity:
        db.add(opp)
        db.commit()
        db.refresh(opp)
        return opp

    @staticmethod
    def update_status(db: Session, opp_id: str, status: str) -> Optional[Opportunity]:
        opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if opp:
            opp.status = status
            db.commit()
            db.refresh(opp)
        return opp
