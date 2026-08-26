from membraneiq.cip_effectiveness import assess_cip_recovery
from membraneiq.economics import PlantEconomics, assess_economics
from membraneiq.intervention import compare_clean_vs_run


def test_cip_recovery_quantifies_partial_cleaning():
    result = assess_cip_recovery(80, 94, 100, higher_is_better=True)
    assert result.recovery_pct == 70.0
    assert result.residual_loss_pct == 6.0
    assert result.effectiveness == "PARTIAL"


def test_economics_uses_explicit_customer_assumptions():
    assumptions = PlantEconomics(
        product_value_per_liter=0.05,
        production_hours_per_day=20,
        cip_water_m3=10,
        water_cost_per_m3=2,
        cip_chemical_cost=120,
        cip_energy_cost=40,
        cip_labor_cost=60,
        cip_downtime_hours=2,
        membrane_replacement_cost=12000,
    )
    result = assess_economics(2500, 2200, assumptions)
    assert result.estimated_daily_throughput_value_loss == 300.0
    assert result.estimated_cip_direct_cost == 240.0
    assert result.estimated_total_cip_cost == 490.0


def test_intervention_reports_break_even_not_fake_savings():
    economics = assess_economics(
        2500,
        2000,
        PlantEconomics(
            product_value_per_liter=0.10,
            production_hours_per_day=20,
            cip_downtime_hours=1,
            cip_chemical_cost=100,
        ),
    )
    decision = compare_clean_vs_run(economics)
    assert decision.days_to_cip_break_even is not None
    assert "days" in decision.rationale
