"""Configurable Versioned Business Rule Engine."""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import Rule, RuleVersion
from backend.services.shared.repositories.rule_repo import RuleRepository


class BusinessRuleEngine:
    """Evaluates business rules against customer, transaction, and RM context."""

    DEFAULT_RULES = {
        "CROSS_SELL_INSURANCE": {
            "name": "Insurance Cross-Sell on Large Payin",
            "category": "OPPORTUNITY",
            "description": "Detects insurance cross-sell when customer makes a significant deposit but holds no insurance.",
            "conditions": {"min_payin_amount": 50000, "missing_category": "INSURANCE"},
            "weights": {"payin_weight": 0.4, "segment_weight": 0.3, "product_gap_weight": 0.3},
            "thresholds": {"min_score_for_opportunity": 0.60},
            "event_types": ["PAYIN_RECEIVED"]
        },
        "UPSELL_PORTFOLIO": {
            "name": "Portfolio Wealth Upsell",
            "category": "OPPORTUNITY",
            "description": "Detects high net-worth expansion opportunity on high AUM or deposit.",
            "conditions": {"min_payin_amount": 200000, "min_aum": 500000},
            "weights": {"aum_weight": 0.5, "payin_weight": 0.3, "intent_weight": 0.2},
            "thresholds": {"min_score_for_opportunity": 0.65},
            "event_types": ["PAYIN_RECEIVED", "CUSTOMER_ACTIVITY"]
        },
        "DORMANT_REACTIVATION": {
            "name": "Dormant Customer Reactivation",
            "category": "OPPORTUNITY",
            "description": "Identifies reactivation potential for dormant customers when activity occurs.",
            "conditions": {"target_status": "DORMANT"},
            "weights": {"relationship_weight": 0.6, "activity_weight": 0.4},
            "thresholds": {"min_score_for_opportunity": 0.50},
            "event_types": ["CUSTOMER_ACTIVITY", "DIGITAL_ACTIVITY", "PAYIN_RECEIVED"]
        },
        "HIGH_INTENT_LEAD": {
            "name": "High Intent Lead Prioritization",
            "category": "OPPORTUNITY",
            "description": "Prioritizes actionable leads showing high commercial intent.",
            "conditions": {"min_intent_score": 0.70},
            "weights": {"intent_weight": 0.7, "value_weight": 0.3},
            "thresholds": {"min_score_for_opportunity": 0.70},
            "event_types": ["LEAD_CREATED", "LEAD_UPDATED"]
        },
        "PERFORMANCE_RISK": {
            "name": "RM Performance Risk Detection",
            "category": "PERFORMANCE",
            "description": "Flags RMs lagging behind run-rate with declining conversion or high overdue SLAs.",
            "conditions": {"min_run_rate_gap_pct": 0.15, "max_sla_breaches": 2},
            "weights": {"target_lag_weight": 0.4, "sla_breach_weight": 0.3, "conversion_decline_weight": 0.3},
            "thresholds": {"risk_score_threshold": 0.60},
            "event_types": ["CONVERSION_COMPLETED", "ACTION_COMPLETED", "ACTION_SNOOZED"]
        },
        "TARGET_ACHIEVED": {
            "name": "Early Target Achievement",
            "category": "PERFORMANCE",
            "description": "Detects RM achieving quarterly or monthly target early.",
            "conditions": {"min_achievement_pct": 1.00},
            "weights": {"achievement_weight": 1.0},
            "thresholds": {"achievement_threshold": 1.00},
            "event_types": ["CONVERSION_COMPLETED"]
        }
    }

    @classmethod
    def get_rule_config(cls, db: Session, rule_code: str) -> Dict[str, Any]:
        """Loads rule configuration from database or falls back to standard defaults."""
        rule = RuleRepository.get_by_code(db, rule_code)
        if rule:
            version = RuleRepository.get_active_version(db, rule.id)
            if version:
                return {
                    "rule_id": rule.id,
                    "rule_version_id": version.id,
                    "version_number": version.version,
                    "code": rule.code,
                    "conditions": version.conditions,
                    "weights": version.weights,
                    "thresholds": version.thresholds,
                }

        # Fallback to default in-memory rules
        default = cls.DEFAULT_RULES.get(rule_code, {})
        return {
            "rule_id": f"default_{rule_code.lower()}",
            "rule_version_id": f"v1_{rule_code.lower()}",
            "version_number": 1,
            "code": rule_code,
            "conditions": default.get("conditions", {}),
            "weights": default.get("weights", {}),
            "thresholds": default.get("thresholds", {}),
        }
