import pandas as pd

from membraneiq.anomaly import Severity, assess_anomalies
from membraneiq.baseline import learn_clean_baseline
from membraneiq.decision_engine import RecommendedAction, recommend_action
from membraneiq.degradation import estimate_trend


def _baseline():
    df = pd.DataFrame({
        "normalized_permeability": [100 + ((i % 5) - 2) * 0.3 for i in range(30)],
        "pressure_drop": [1.0 + ((i % 5) - 2) * 0.01 for i in range(30)],
    })
    return learn_clean_baseline(df, ["normalized_permeability", "pressure_drop"])


def test_anomaly_engine_detects_large_permeability_loss():
    result = assess_anomalies({"normalized_permeability": 90.0}, _baseline())
    assert result.overall_severity in {Severity.WARNING, Severity.CRITICAL}
    assert result.anomalies[0].direction == "LOW"


def test_degradation_trend_detects_declining_permeability():
    days = list(range(10))
    values = [100 - day * 0.8 for day in days]
    trend = estimate_trend("normalized_permeability", days, values, higher_is_worse=False)
    assert trend.direction == "DEGRADING"
    assert trend.r_squared > 0.95


def test_decision_engine_escalates_critical_anomaly_and_weak_cip():
    anomalies = assess_anomalies({"normalized_permeability": 80.0}, _baseline())
    decision = recommend_action(anomalies, [], latest_cip_recovery_pct=65.0)
    assert decision.action == RecommendedAction.INSPECT
    assert decision.requires_operator_review is True
