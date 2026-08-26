from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


@dataclass
class Assessment:
    health_score: float
    status: str
    normalized_permeability_loss_pct: float
    tmp_change_pct: float
    pressure_drop_change_pct: float
    rejection_change_pct_points: float
    latest_cip_recovery_pct: float | None
    fouling_trend_pct_per_hour: float
    diagnosis: str
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


def _mean_valid(series: pd.Series) -> float:
    return float(series.dropna().mean())


def establish_baseline(df: pd.DataFrame, baseline_hours: float = 4.0) -> dict[str, float]:
    prod = df[~df["cip_active"]].copy()
    baseline = prod[prod["elapsed_hours"] <= baseline_hours]
    if baseline.empty:
        raise ValueError("No valid baseline data.")
    return {
        "normalized_permeability": _mean_valid(baseline["normalized_permeability_lmh_bar"]),
        "tmp": _mean_valid(baseline["tmp_bar"]),
        "pressure_drop": _mean_valid(baseline["pressure_drop_bar"]),
        "rejection": _mean_valid(baseline["rejection_fraction"]),
    }


def calculate_latest_cip_recovery(df: pd.DataFrame, baseline: dict[str, float], post_cip_window_hours: float = 2.0) -> float | None:
    cip_rows = df[df["cip_active"]]
    if cip_rows.empty:
        return None
    cip_end = cip_rows["elapsed_hours"].max()
    post = df[(~df["cip_active"]) & (df["elapsed_hours"] > cip_end) & (df["elapsed_hours"] <= cip_end + post_cip_window_hours)]
    if post.empty:
        return None
    post_perm = _mean_valid(post["normalized_permeability_lmh_bar"])
    recovery = 100.0 * post_perm / baseline["normalized_permeability"]
    return float(np.clip(recovery, 0.0, 120.0))


def _recent_mean(df: pd.DataFrame, column: str, recent_hours: float = 2.0) -> float:
    prod = df[~df["cip_active"]].dropna(subset=[column])
    end_h = prod["elapsed_hours"].max()
    recent = prod[prod["elapsed_hours"] >= end_h - recent_hours]
    return _mean_valid(recent[column])


def _fouling_trend_pct_per_hour(df: pd.DataFrame, baseline: dict[str, float], recent_hours: float = 6.0) -> float:
    prod = df[~df["cip_active"]].dropna(subset=["normalized_permeability_lmh_bar"]).copy()
    end_h = prod["elapsed_hours"].max()
    recent = prod[prod["elapsed_hours"] >= end_h - recent_hours]
    if len(recent) < 3:
        return 0.0
    x = recent["elapsed_hours"].to_numpy()
    y = 100.0 * recent["normalized_permeability_lmh_bar"].to_numpy() / baseline["normalized_permeability"]
    return float(np.polyfit(x, y, 1)[0])


def assess_health(df: pd.DataFrame, baseline: dict[str, float]) -> Assessment:
    latest_perm = _recent_mean(df, "normalized_permeability_lmh_bar")
    latest_tmp = _recent_mean(df, "tmp_bar")
    latest_dp = _recent_mean(df, "pressure_drop_bar")
    latest_rejection = _recent_mean(df, "rejection_fraction")

    perm_loss = max(0.0, (1.0 - latest_perm / baseline["normalized_permeability"]) * 100.0)
    tmp_change = max(0.0, (latest_tmp / baseline["tmp"] - 1.0) * 100.0)
    dp_change = max(0.0, (latest_dp / baseline["pressure_drop"] - 1.0) * 100.0)
    rejection_change_pp = (latest_rejection - baseline["rejection"]) * 100.0
    cip_recovery = calculate_latest_cip_recovery(df, baseline)
    trend = _fouling_trend_pct_per_hour(df, baseline)

    penalty_perm = min(40.0, perm_loss * 1.5)
    penalty_tmp = min(20.0, tmp_change * 0.55)
    penalty_dp = min(20.0, dp_change * 0.45)
    penalty_rej = min(8.0, abs(min(rejection_change_pp, 0.0)) * 4.0)
    penalty_trend = min(7.0, max(0.0, -trend) * 2.0)
    penalty_cip = 0.0 if cip_recovery is None or cip_recovery >= 98.0 else min(20.0, (98.0 - cip_recovery) * 0.8)

    health = float(np.clip(100.0 - (penalty_perm + penalty_tmp + penalty_dp + penalty_rej + penalty_trend + penalty_cip), 0.0, 100.0))
    status = "HEALTHY" if health >= 85 else "WATCH" if health >= 65 else "DEGRADED" if health >= 45 else "CRITICAL"

    if cip_recovery is not None and cip_recovery < 90 and perm_loss > 10:
        diagnosis = "Progressive fouling with incomplete recovery"
        recommendation = "Monitor closely and inspect if post-CIP recovery continues to decline."
    elif perm_loss > 20 or dp_change > 25:
        diagnosis = "Significant hydraulic performance deterioration"
        recommendation = "Evaluate cleaning need and investigate abnormal resistance increase."
    elif perm_loss > 8 or tmp_change > 8:
        diagnosis = "Developing fouling trend"
        recommendation = "Continue monitoring and compare against normal run trajectory."
    else:
        diagnosis = "Performance near established clean baseline"
        recommendation = "Continue normal operation and trend monitoring."

    return Assessment(round(health, 1), status, round(perm_loss, 1), round(tmp_change, 1), round(dp_change, 1), round(rejection_change_pp, 2), None if cip_recovery is None else round(cip_recovery, 1), round(trend, 2), diagnosis, recommendation)
