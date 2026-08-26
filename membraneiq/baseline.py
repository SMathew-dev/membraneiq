from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BaselineMetric:
    median: float
    mad: float
    samples: int


@dataclass
class CleanBaseline:
    metrics: dict[str, BaselineMetric]
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "sample_count": self.sample_count,
            "metrics": {name: asdict(metric) for name, metric in self.metrics.items()},
        }


def learn_clean_baseline(
    df: pd.DataFrame,
    metrics: list[str],
    state_column: str = "operating_state",
    production_label: str = "PRODUCTION",
    minimum_samples: int = 20,
) -> CleanBaseline:
    """Learn a robust baseline from production-only observations.

    Median/MAD are used instead of mean/std so a few abnormal observations do
    not easily redefine what MembraneIQ considers healthy.
    """
    if state_column in df.columns:
        clean = df[df[state_column] == production_label].copy()
    else:
        clean = df.copy()

    if len(clean) < minimum_samples:
        raise ValueError(
            f"Need at least {minimum_samples} production samples to establish baseline; got {len(clean)}"
        )

    learned: dict[str, BaselineMetric] = {}
    for metric in metrics:
        if metric not in clean.columns:
            continue
        values = pd.to_numeric(clean[metric], errors="coerce").dropna().to_numpy(dtype=float)
        if len(values) < minimum_samples:
            continue
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        learned[metric] = BaselineMetric(median=median, mad=mad, samples=len(values))

    if not learned:
        raise ValueError("No requested metrics had enough valid samples for baseline learning")

    return CleanBaseline(metrics=learned, sample_count=len(clean))


def robust_deviation(value: float, baseline: BaselineMetric) -> float:
    """Return robust z-like deviation using scaled MAD."""
    scale = 1.4826 * baseline.mad
    if scale <= 1e-12:
        return 0.0 if abs(value - baseline.median) <= 1e-12 else float("inf")
    return (float(value) - baseline.median) / scale
