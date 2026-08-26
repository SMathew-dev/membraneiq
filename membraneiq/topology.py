from __future__ import annotations

from dataclasses import dataclass, field

from membraneiq.records import MembraneHealthRecord


@dataclass
class VesselCondition:
    vessel_id: str
    stage_id: str
    health_score: float | None
    status: str
    latest_cip_recovery_pct: float | None
    element_count: int


@dataclass
class StageCondition:
    stage_id: str
    health_score: float | None
    status: str
    vessel_count: int
    degraded_vessels: list[str] = field(default_factory=list)


def _status_from_score(score: float | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 85:
        return "HEALTHY"
    if score >= 65:
        return "WATCH"
    if score >= 45:
        return "DEGRADED"
    return "CRITICAL"


def summarize_vessel(
    vessel_id: str,
    stage_id: str,
    records: list[MembraneHealthRecord],
) -> VesselCondition:
    """
    Summarize a vessel from the element records assigned to it.

    v0.2 uses the mean of available element health scores as a vessel summary.
    This is an aggregation model, not a claim that element condition can be
    inferred from normal skid instrumentation.
    """
    members = [
        record
        for record in records
        if record.vessel_id == vessel_id and record.stage_id == stage_id
    ]
    scores = [
        record.current_health_score
        for record in members
        if record.current_health_score is not None
    ]
    recoveries = [
        record.latest_cip_recovery_pct
        for record in members
        if record.latest_cip_recovery_pct is not None
    ]

    health = round(sum(scores) / len(scores), 1) if scores else None
    recovery = round(sum(recoveries) / len(recoveries), 1) if recoveries else None

    return VesselCondition(
        vessel_id=vessel_id,
        stage_id=stage_id,
        health_score=health,
        status=_status_from_score(health),
        latest_cip_recovery_pct=recovery,
        element_count=len(members),
    )


def summarize_stage(
    stage_id: str,
    records: list[MembraneHealthRecord],
) -> StageCondition:
    vessel_ids = sorted(
        {
            record.vessel_id
            for record in records
            if record.stage_id == stage_id and record.vessel_id is not None
        }
    )

    vessels = [summarize_vessel(vessel_id, stage_id, records) for vessel_id in vessel_ids]
    scores = [v.health_score for v in vessels if v.health_score is not None]
    health = round(sum(scores) / len(scores), 1) if scores else None
    degraded = [v.vessel_id for v in vessels if v.status in {"DEGRADED", "CRITICAL"}]

    return StageCondition(
        stage_id=stage_id,
        health_score=health,
        status=_status_from_score(health),
        vessel_count=len(vessels),
        degraded_vessels=degraded,
    )


def rank_assets_for_attention(records: list[MembraneHealthRecord]) -> list[MembraneHealthRecord]:
    """Return worst-known assets first; unknown-condition assets come last."""
    return sorted(
        records,
        key=lambda record: (
            record.current_health_score is None,
            record.current_health_score if record.current_health_score is not None else 999.0,
        ),
    )
