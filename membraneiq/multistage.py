from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VesselSpec:
    stage_id: str
    vessel_id: str
    baseline_health: float = 100.0
    fouling_rate_per_hour: float = 0.35
    anomaly_multiplier: float = 1.0
    cip_recovery_fraction: float = 0.97


def default_uf_topology() -> list[VesselSpec]:
    """Return a simple 3-stage dairy UF skid topology for prototype testing."""
    return [
        VesselSpec("S1", "V1A", fouling_rate_per_hour=0.18),
        VesselSpec("S1", "V1B", fouling_rate_per_hour=0.20),
        VesselSpec("S2", "V2A", fouling_rate_per_hour=0.28),
        VesselSpec("S2", "V2B", fouling_rate_per_hour=0.30),
        VesselSpec("S3", "V3A", fouling_rate_per_hour=0.42),
        VesselSpec(
            "S3",
            "V3B",
            fouling_rate_per_hour=0.46,
            anomaly_multiplier=2.2,
            cip_recovery_fraction=0.84,
        ),
    ]


def simulate_multistage_run(
    hours: int = 36,
    sample_minutes: int = 15,
    cip_hour: float = 24.0,
    seed: int = 42,
    topology: list[VesselSpec] | None = None,
) -> pd.DataFrame:
    """
    Simulate vessel-level condition indicators for a multi-stage UF skid.

    This is a topology/health prototype, not a validated hydraulic process model.
    It creates relative performance signals so MembraneIQ can test localization,
    stage aggregation, and post-CIP recovery behavior.
    """
    topology = topology or default_uf_topology()
    rng = np.random.default_rng(seed)
    elapsed = np.arange(0, hours + sample_minutes / 60, sample_minutes / 60)

    rows: list[dict] = []
    for spec in topology:
        for h in elapsed:
            pre_cip = h < cip_hour
            effective_h = h if pre_cip else h - cip_hour

            if pre_cip:
                degradation = spec.fouling_rate_per_hour * spec.anomaly_multiplier * h
            else:
                pre_cip_loss = (
                    spec.fouling_rate_per_hour
                    * spec.anomaly_multiplier
                    * cip_hour
                )
                residual_loss = pre_cip_loss * (1.0 - spec.cip_recovery_fraction)
                refouling = (
                    spec.fouling_rate_per_hour
                    * spec.anomaly_multiplier
                    * 0.55
                    * effective_h
                )
                degradation = residual_loss + refouling

            health = np.clip(
                spec.baseline_health - degradation + rng.normal(0, 0.6),
                0,
                100,
            )

            permeability_index = np.clip(
                1.0 - degradation / 120.0 + rng.normal(0, 0.004),
                0.45,
                1.05,
            )
            tmp_index = 1.0 + degradation / 150.0 + rng.normal(0, 0.004)
            pressure_drop_index = 1.0 + degradation / 110.0 + rng.normal(0, 0.006)

            rows.append(
                {
                    "elapsed_hours": round(float(h), 4),
                    "stage_id": spec.stage_id,
                    "vessel_id": spec.vessel_id,
                    "health_score": round(float(health), 2),
                    "normalized_permeability_index": round(float(permeability_index), 4),
                    "tmp_index": round(float(tmp_index), 4),
                    "pressure_drop_index": round(float(pressure_drop_index), 4),
                    "cip_completed": bool(h >= cip_hour),
                    "known_anomaly": spec.anomaly_multiplier > 1.5,
                }
            )

    return pd.DataFrame(rows)


def latest_vessel_health(df: pd.DataFrame) -> pd.DataFrame:
    """Return the latest health row for each vessel, ranked worst first."""
    latest_h = df["elapsed_hours"].max()
    latest = df[df["elapsed_hours"] == latest_h].copy()
    return latest.sort_values("health_score", ascending=True).reset_index(drop=True)


def stage_health_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate latest vessel health into stage-level condition summaries."""
    latest = latest_vessel_health(df)
    summary = (
        latest.groupby("stage_id", as_index=False)
        .agg(
            health_score=("health_score", "mean"),
            worst_vessel_health=("health_score", "min"),
            vessel_count=("vessel_id", "count"),
        )
        .sort_values("health_score", ascending=True)
        .reset_index(drop=True)
    )
    summary["health_score"] = summary["health_score"].round(1)
    summary["worst_vessel_health"] = summary["worst_vessel_health"].round(1)
    return summary


def condition_status(health_score: float) -> str:
    if health_score >= 85:
        return "HEALTHY"
    if health_score >= 65:
        return "WATCH"
    if health_score >= 45:
        return "DEGRADED"
    return "CRITICAL"


def skid_condition_report(df: pd.DataFrame) -> dict:
    """Build a compact operator-facing condition report for the simulated skid."""
    vessels = latest_vessel_health(df).copy()
    vessels["status"] = vessels["health_score"].map(condition_status)
    stages = stage_health_summary(df).copy()
    stages["status"] = stages["health_score"].map(condition_status)

    worst = vessels.iloc[0]
    return {
        "worst_asset": str(worst["vessel_id"]),
        "worst_stage": str(worst["stage_id"]),
        "worst_health": float(worst["health_score"]),
        "worst_status": str(worst["status"]),
        "vessels": vessels,
        "stages": stages,
    }
