"""Configurable Weighted Scoring for Opportunities."""

from typing import Any, Dict, List, Tuple


class OpportunityScorer:
    @classmethod
    def calculate_score(
        cls,
        weights: Dict[str, float],
        signals: Dict[str, float]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculates a deterministic composite score between 0.0 and 1.0 from normalized signal values.

        Returns (score, signal_breakdown)
        """
        total_weight = 0.0
        weighted_sum = 0.0
        breakdown = {}

        for signal_key, signal_val in signals.items():
            # Match weight with default fallback
            weight = weights.get(f"{signal_key}_weight", weights.get(signal_key, 0.2))
            normalized_val = max(0.0, min(1.0, float(signal_val)))
            contribution = normalized_val * weight

            weighted_sum += contribution
            total_weight += weight
            breakdown[signal_key] = {
                "raw_value": signal_val,
                "normalized": round(normalized_val, 3),
                "weight": round(weight, 3),
                "contribution": round(contribution, 3)
            }

        final_score = round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.50
        return final_score, breakdown

    @staticmethod
    def map_priority(score: float) -> str:
        if score >= 0.85:
            return "CRITICAL"
        elif score >= 0.70:
            return "HIGH"
        elif score >= 0.50:
            return "MEDIUM"
        return "LOW"
