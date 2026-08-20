"""Deterministic Commission Calculation Engine.

STRICT RULE:
Commission calculations are 100% mathematical and deterministic.
LLMs are NEVER allowed to compute, approve, or alter commission amounts.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from backend.services.action_commission_server.commission.provider import CommissionRuleProvider


class CommissionCalculationResult(BaseModel):
    is_eligible: bool
    converted_value: float
    product_category: str
    customer_segment: str
    base_rate: float
    segment_multiplier: float
    volume_multiplier: float
    base_commission_amount: float
    final_commission_amount: float
    rm_id: str
    rule_version: str = "1.0"
    breakdown: Dict[str, Any] = Field(default_factory=dict)


class DeterministicCommissionEngine:
    @classmethod
    def calculate(
        cls,
        converted_value: float,
        product_category: Optional[str],
        customer_segment: Optional[str],
        rm_id: str,
        is_eligible: bool = True,
        rule_version: str = "1.0"
    ) -> CommissionCalculationResult:
        """Calculates commission deterministically using verified rates and tier multipliers."""
        if not is_eligible or converted_value <= 0:
            return CommissionCalculationResult(
                is_eligible=False,
                converted_value=converted_value,
                product_category=product_category or "NONE",
                customer_segment=customer_segment or "RETAIL",
                base_rate=0.0,
                segment_multiplier=1.0,
                volume_multiplier=1.0,
                base_commission_amount=0.0,
                final_commission_amount=0.0,
                rm_id=rm_id,
                rule_version=rule_version,
                breakdown={"reason": "Conversion value is 0 or marked non-eligible"}
            )

        cat = (product_category or "DEFAULT").upper()
        seg = (customer_segment or "RETAIL").upper()

        base_rate = CommissionRuleProvider.get_base_rate(cat)
        seg_mult = CommissionRuleProvider.get_segment_multiplier(seg)
        vol_mult = CommissionRuleProvider.get_volume_multiplier(converted_value)

        base_commission = round(converted_value * base_rate, 2)
        final_commission = round(base_commission * seg_mult * vol_mult, 2)

        breakdown = {
            "formula": "converted_value * base_rate * segment_multiplier * volume_multiplier",
            "converted_value": converted_value,
            "base_rate": base_rate,
            "base_commission": base_commission,
            "segment_multiplier": seg_mult,
            "volume_multiplier": vol_mult,
            "final_commission": final_commission,
            "rule_version": rule_version,
            "is_deterministic": True
        }

        return CommissionCalculationResult(
            is_eligible=True,
            converted_value=converted_value,
            product_category=cat,
            customer_segment=seg,
            base_rate=base_rate,
            segment_multiplier=seg_mult,
            volume_multiplier=vol_mult,
            base_commission_amount=base_commission,
            final_commission_amount=final_commission,
            rm_id=rm_id,
            rule_version=rule_version,
            breakdown=breakdown
        )
