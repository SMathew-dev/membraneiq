from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ObservabilityAssessment:
    resolution: str
    score: float
    supported_capabilities: list[str]
    unsupported_capabilities: list[str]
    recommended_measurements: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def assess_observability(
    mapped_signals: set[str],
    stages_detected: int = 0,
    vessels_detected: int = 0,
) -> ObservabilityAssessment:
    supported: list[str] = []
    unsupported: list[str] = []
    recommendations: list[str] = []

    core = {"feed_pressure", "retentate_pressure", "permeate_pressure", "permeate_flow", "temperature"}
    if core.issubset(mapped_signals):
        supported.append("core_performance_normalization")
    else:
        unsupported.append("core_performance_normalization")
        for signal in sorted(core - mapped_signals):
            recommendations.append(f"Add or map {signal}")

    if "permeate_conductivity" in mapped_signals:
        supported.append("permeate_quality_tracking")
    else:
        unsupported.append("permeate_quality_tracking")
        recommendations.append("Add or map permeate_conductivity")

    if "cip_state" in mapped_signals:
        supported.append("automatic_cip_segmentation")
    else:
        unsupported.append("automatic_cip_segmentation")
        recommendations.append("Expose CIP state/phase signal")

    if vessels_detected > 0:
        resolution = "VESSEL"
        supported.append("vessel_contextualization")
    elif stages_detected > 0:
        resolution = "STAGE"
        unsupported.append("vessel_localization")
        recommendations.append("Expose vessel-specific pressure/flow instrumentation for vessel localization")
    else:
        resolution = "SKID"
        unsupported.extend(["stage_localization", "vessel_localization"])
        recommendations.append("Provide stage/vessel topology or stage-specific instrumentation")

    score = 100.0 * len(supported) / max(1, len(supported) + len(unsupported))
    return ObservabilityAssessment(
        resolution=resolution,
        score=round(score, 1),
        supported_capabilities=supported,
        unsupported_capabilities=unsupported,
        recommended_measurements=list(dict.fromkeys(recommendations)),
    )
