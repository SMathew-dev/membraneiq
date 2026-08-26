from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np


@dataclass(frozen=True)
class DegradationTrend:
    metric: str
    slope_per_day: float
    change_pct_per_30d: float | None
    r_squared: float
    direction: str
    samples: int

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_trend(
    metric: str,
    elapsed_days: list[float],
    values: list[float],
    higher_is_worse: bool,
    minimum_samples: int = 8,
) -> DegradationTrend:
    if len(elapsed_days) != len(values):
        raise ValueError("elapsed_days and values must have equal length")
    if len(values) < minimum_samples:
        raise ValueError(f"Need at least {minimum_samples} samples for degradation trend")

    x = np.asarray(elapsed_days, dtype=float)
    y = np.asarray(values, dtype=float)
    if np.ptp(x) <= 0:
        raise ValueError("Trend requires observations spanning time")

    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    start = float(predicted[0])
    pct30 = None if abs(start) < 1e-12 else float((slope * 30.0 / abs(start)) * 100.0)
    worsening = slope > 0 if higher_is_worse else slope < 0
    direction = "DEGRADING" if worsening else "IMPROVING" if abs(slope) > 1e-12 else "STABLE"

    return DegradationTrend(
        metric=metric,
        slope_per_day=round(float(slope), 6),
        change_pct_per_30d=None if pct30 is None else round(pct30, 2),
        r_squared=round(r2, 3),
        direction=direction,
        samples=len(values),
    )
