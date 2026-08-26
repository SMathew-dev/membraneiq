import pandas as pd

from membraneiq.baseline import learn_clean_baseline, robust_deviation
from membraneiq.normalization import normalize_flow, normalize_pressure, normalize_temperature
from membraneiq.operating_state import OperatingState, detect_state


def test_engineering_unit_normalization():
    assert round(normalize_pressure(100, "psi").value, 3) == 6.895
    assert normalize_flow(10, "L/min").value == 600
    assert round(normalize_temperature(68, "F").value, 2) == 20.0


def test_operating_state_separates_cip_and_production():
    assert detect_state(2000, 4.0, cip_state=True).state == OperatingState.CIP
    assert detect_state(2000, 4.0, cip_state=False).state == OperatingState.PRODUCTION
    assert detect_state(0, 0.0, pump_running=False).state == OperatingState.OFFLINE


def test_baseline_uses_production_only_and_is_robust_to_outlier():
    rows = [
        {"operating_state": "PRODUCTION", "normalized_permeability": 100 + ((i % 5) - 2) * 0.2}
        for i in range(30)
    ]
    rows.append({"operating_state": "PRODUCTION", "normalized_permeability": 160})
    rows.extend([
        {"operating_state": "CIP", "normalized_permeability": 20},
        {"operating_state": "OFFLINE", "normalized_permeability": 0},
    ])
    baseline = learn_clean_baseline(pd.DataFrame(rows), ["normalized_permeability"])
    metric = baseline.metrics["normalized_permeability"]

    assert 99.5 < metric.median < 100.5
    assert robust_deviation(90, metric) < 0
