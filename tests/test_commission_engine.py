"""Unit tests for the Deterministic Commission Calculation Engine."""

from backend.services.action_commission_server.commission.engine import DeterministicCommissionEngine


def test_deterministic_insurance_hni_commission():
    # Value: 1,000,000 INR (10 Lakhs)
    # Product: INSURANCE -> base_rate = 0.05
    # Segment: HNI -> segment_multiplier = 1.15
    # Volume: >= 10L -> volume_multiplier = 1.10
    # Expected Base = 1,000,000 * 0.05 = 50,000
    # Expected Final = 50,000 * 1.15 * 1.10 = 63,250.0

    result = DeterministicCommissionEngine.calculate(
        converted_value=1_000_000.0,
        product_category="INSURANCE",
        customer_segment="HNI",
        rm_id="rm_agent_1",
        is_eligible=True
    )

    assert result.is_eligible is True
    assert result.base_rate == 0.05
    assert result.segment_multiplier == 1.15
    assert result.volume_multiplier == 1.10
    assert result.base_commission_amount == 50_000.0
    assert result.final_commission_amount == 63_250.0
    assert result.breakdown["is_deterministic"] is True


def test_zero_value_and_ineligible_commission():
    res_zero = DeterministicCommissionEngine.calculate(
        converted_value=0.0,
        product_category="EQUITY",
        customer_segment="RETAIL",
        rm_id="rm_1"
    )
    assert res_zero.final_commission_amount == 0.0

    res_ineligible = DeterministicCommissionEngine.calculate(
        converted_value=500_000.0,
        product_category="EQUITY",
        customer_segment="RETAIL",
        rm_id="rm_1",
        is_eligible=False
    )
    assert res_ineligible.final_commission_amount == 0.0


def test_strict_mathematical_determinism_reproducibility():
    # 100 iterations of identical input must return identical output
    expected = None
    for _ in range(100):
        out = DeterministicCommissionEngine.calculate(
            converted_value=750_000.0,
            product_category="MUTUAL_FUND",
            customer_segment="ULTRA_HNI",
            rm_id="rm_deterministic_test"
        )
        if expected is None:
            expected = out.final_commission_amount
        else:
            assert out.final_commission_amount == expected
