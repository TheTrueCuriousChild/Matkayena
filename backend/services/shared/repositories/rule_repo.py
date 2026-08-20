"""Repository for Business Rules, Versions, and Rule Evaluations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import (
    Rule, RuleVersion, RuleEventType, RuleEvaluation
)


class RuleRepository:
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Rule]:
        return db.query(Rule).filter(Rule.code == code, Rule.is_active.is_(True)).first()

    @staticmethod
    def get_active_version(db: Session, rule_id: str) -> Optional[RuleVersion]:
        return db.query(RuleVersion).filter(
            RuleVersion.rule_id == rule_id,
            RuleVersion.is_active.is_(True)
        ).order_by(RuleVersion.version.desc()).first()

    @staticmethod
    def get_rules_for_event(db: Session, event_type_code: str) -> List[Rule]:
        rule_ids = db.query(RuleEventType.rule_id).filter(
            RuleEventType.event_type_code == event_type_code
        ).subquery()

        return db.query(Rule).filter(
            Rule.id.in_(rule_ids),
            Rule.is_active.is_(True)
        ).all()

    @staticmethod
    def record_evaluation(db: Session, eval_record: RuleEvaluation) -> RuleEvaluation:
        db.add(eval_record)
        db.commit()
        db.refresh(eval_record)
        return eval_record

    @staticmethod
    def save_rule_with_version(
        db: Session,
        code: str,
        name: str,
        category: str,
        description: str,
        conditions: dict,
        weights: dict,
        thresholds: dict,
        event_types: List[str]
    ) -> Rule:
        rule = db.query(Rule).filter(Rule.code == code).first()
        if not rule:
            rule = Rule(
                code=code,
                name=name,
                category=category,
                description=description,
                is_active=True
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)

            # Link event types
            for et in event_types:
                ret = RuleEventType(rule_id=rule.id, event_type_code=et)
                db.add(ret)
            db.commit()

            version_num = 1
        else:
            latest_v = db.query(RuleVersion).filter(RuleVersion.rule_id == rule.id).order_by(RuleVersion.version.desc()).first()
            version_num = (latest_v.version + 1) if latest_v else 1
            if latest_v:
                latest_v.is_active = False

        new_version = RuleVersion(
            rule_id=rule.id,
            version=version_num,
            conditions=conditions,
            weights=weights,
            thresholds=thresholds,
            is_active=True
        )
        db.add(new_version)
        db.commit()
        db.refresh(rule)
        return rule
