import pandas as pd

from membraneiq.historical_analysis import analyze_historical_condition


def test_historical_analysis_detects_late_degradation():
    timestamps = pd.date_range("2026-01-01", periods=90, freq="6h", tz="UTC")
    permeability = [100.0] * 30 + [100.0 - 0.35 * (i - 30) for i in range(30, 90)]
    pressure_drop = [1.0] * 30 + [1.0 + 0.008 * (i - 30) for i in range(30, 90)]
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "operating_state": ["PRODUCTION"] * 90,
            "normalized_permeability_lmh_bar": permeability,
            "pressure_drop_bar": pressure_drop,
        }
    )

    report = analyze_historical_condition(df, baseline_samples=30, current_window_samples=10)

    assert "normalized_permeability_lmh_bar" in report.metrics_used
    assert report.anomaly["overall_severity"] in {"WARNING", "CRITICAL"}
    assert any(trend["direction"] == "DEGRADING" for trend in report.trends)
    assert report.decision["action"] in {"MONITOR", "CLEAN", "INSPECT"}


def test_historical_analysis_warns_when_timestamp_missing():
    df = pd.DataFrame(
        {
            "operating_state": ["PRODUCTION"] * 40,
            "permeate_flow_lph": [2400.0] * 40,
        }
    )
    report = analyze_historical_condition(df, baseline_samples=20, current_window_samples=10)
    assert any("timestamp" in warning.lower() for warning in report.warnings)
