"""Deterministic Commission Rule Provider and Configuration Interface.

MISSING DATABASE INTEGRATION POINT:
As specified in Section 19 of the architecture specification, since the protected schema
does not contain a dedicated table for commission rules, this service-level Provider
abstracts and defines the deterministic commission rate calculation policies.
"""

from typing import Dict, Optional
from pydantic import BaseModel


class CommissionRuleConfig(BaseModel):
    product_category: str
    base_rate: float
    min_threshold: float = 0.0
    max_cap: Optional[float] = None
    description: str


class CommissionRuleProvider:
    """Configurable provider for product base commission rates and multipliers."""

    # Default category rates
    CATEGORY_BASE_RATES: Dict[str, float] = {
        "INSURANCE": 0.050,      # 5.0%
        "MUTUAL_FUND": 0.015,    # 1.5%
        "EQUITY": 0.010,         # 1.0%
        "FIXED_INCOME": 0.008,   # 0.8%
        "LOAN": 0.020,           # 2.0%
        "DEFAULT": 0.020         # 2.0%
    }

    # Customer Segment Multipliers
    SEGMENT_MULTIPLIERS: Dict[str, float] = {
        "ULTRA_HNI": 1.25,
        "HNI": 1.15,
        "CORPORATE": 1.10,
        "RETAIL": 1.00,
    }

    @classmethod
    def get_base_rate(cls, product_category: Optional[str]) -> float:
        if not product_category:
            return cls.CATEGORY_BASE_RATES["DEFAULT"]
        return cls.CATEGORY_BASE_RATES.get(product_category.upper(), cls.CATEGORY_BASE_RATES["DEFAULT"])

    @classmethod
    def get_segment_multiplier(cls, segment: Optional[str]) -> float:
        if not segment:
            return 1.00
        return cls.SEGMENT_MULTIPLIERS.get(segment.upper(), 1.00)

    @classmethod
    def get_volume_multiplier(cls, value: float) -> float:
        """Applies volume tier bonus multiplier based on conversion deal size."""
        if value >= 5_000_000:    # >= 50 Lakhs
            return 1.20
        elif value >= 1_000_000:  # >= 10 Lakhs
            return 1.10
        elif value >= 500_000:    # >= 5 Lakhs
            return 1.05
        return 1.00
