import pandas as pd

from membraneiq.baseline import learn_clean_baseline
from membraneiq.degradation import estimate_trend
from membraneiq.economics import PlantEconomics
from membraneiq.engine import MembraneIQEngine


def test_engine_combines_condition_cip_decision_and_economics():
    baseline = learn_clean_baseline(
        pd.DataFrame({
            "normalized_permeability": [100 + ((i % 5) - 2) * 0.3 for i in range(30)],
            "pressure_drop": [1.0 + ((i % 5) - 2) * 0.01 for i in range(30)],
        }),
        ["normalized_permeability", "pressure_drop"],
    )
    trend = estimate_trend(
        "normalized_permeability",
        list(range(10)),
        [100 - 0.8 * day for day in range(10)],
        higher_is_worse=False,
    )

    result = MembraneIQEngine().analyze(
        system_id="UF-01",
        asset_id="V3",
        current_metrics={"normalized_permeability": 82, "pressure_drop": 1.25},
        baseline=baseline,
        trends=[trend],
        pre_cip_value=80,
        post_cip_value=90,
        cip_baseline_value=100,
        healthy_permeate_flow_lph=2500,
        current_permeate_flow_lph=2100,
        plant_economics=PlantEconomics(
            product_value_per_liter=0.08,
            production_hours_per_day=20,
            cip_downtime_hours=1.5,
            cip_chemical_cost=120,
        ),
    )

    assert result.system_id == "UF-01"
    assert result.asset_id == "V3"
    assert result.cip is not None
    assert result.economics is not None
    assert result.intervention is not None
    assert result.decision["action"] in {"CLEAN", "INSPECT"}
