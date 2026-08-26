from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd

from membraneiq.anomaly import assess_anomalies
from membraneiq.baseline import learn_clean_baseline
from membraneiq.decision_engine import recommend_action
from membraneiq.degradation import estimate_trend


METRIC_DIRECTION = {
    "normalized_permeability_lmh_bar": False,
    "permeability_lmh_bar": False,
    "permeate_flow_lph": False,
    "pressure_drop_bar": True,
    "tmp_bar": True,
    "rejection_fraction": False,
}


@dataclass
class HistoricalAnalysisReport:
    baseline_strategy: str
    baseline_samples: int
    current_window_samples: int
    metrics_used: list[str]
    anomaly: dict
    trends: list[dict]
    decision: dict
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_historical_condition(
    prepared_df: pd.DataFrame,
    baseline_samples: int = 30,
    current_window_samples: int = 10,
) -> HistoricalAnalysisReport:
    """Run a conservative first-pass analysis on a prepared historical dataset.

    The earliest stable production samples are used only as a *proposed* clean
    baseline. Real commissioning should let an engineer confirm or replace that
    window when known-clean commissioning/CIP data are available.
    """
    if "operating_state" not in prepared_df.columns:
        raise ValueError("Prepared dataset must contain operating_state")

    production = prepared_df[prepared_df["operating_state"] == "PRODUCTION"].copy()
    if len(production) < max(20, current_window_samples + 5):
        raise ValueError("Insufficient stable production data for historical condition analysis")

    metrics = [metric for metric in METRIC_DIRECTION if metric in production.columns]
    if not metrics:
        raise ValueError("No supported membrane performance metrics are available")

    actual_baseline_samples = min(baseline_samples, max(20, len(production) // 3))
    baseline_frame = production.iloc[:actual_baseline_samples].copy()
    baseline = learn_clean_baseline(
        baseline_frame,
        metrics,
        minimum_samples=min(20, actual_baseline_samples),
    )
    metrics = [metric for metric in metrics if metric in baseline.metrics]

    current = production.iloc[-min(current_window_samples, len(production)):]
    current_values = {
        metric: float(pd.to_numeric(current[metric], errors="coerce").median())
        for metric in metrics
        if pd.to_numeric(current[metric], errors="coerce").notna().any()
    }
    anomaly = assess_anomalies(current_values, baseline)

    warnings = [
        "Baseline is inferred from earliest stable production and should be confirmed against known-clean operation."
    ]
    trends = []
    if "timestamp" in production.columns and production["timestamp"].notna().sum() >= 8:
        timed = production.dropna(subset=["timestamp"]).sort_values("timestamp")
        elapsed_days = (
            (timed["timestamp"] - timed["timestamp"].iloc[0]).dt.total_seconds() / 86400.0
        ).tolist()
        if max(elapsed_days, default=0.0) > 0:
            for metric in metrics:
                values = pd.to_numeric(timed[metric], errors="coerce")
                valid = values.notna()
                if valid.sum() < 8:
                    continue
                try:
                    trends.append(
                        estimate_trend(
                            metric,
                            [day for day, keep in zip(elapsed_days, valid.tolist()) if keep],
                            values[valid].tolist(),
                            higher_is_worse=METRIC_DIRECTION[metric],
                        )
                    )
                except ValueError:
                    continue
    else:
        warnings.append("No reliable timestamp available; time-based degradation rate was not estimated.")

    decision = recommend_action(anomaly, trends)
    return HistoricalAnalysisReport(
        baseline_strategy="earliest_stable_production_proposed",
        baseline_samples=actual_baseline_samples,
        current_window_samples=len(current),
        metrics_used=metrics,
        anomaly=anomaly.to_dict(),
        trends=[trend.to_dict() for trend in trends],
        decision=decision.to_dict(),
        warnings=warnings,
    )
