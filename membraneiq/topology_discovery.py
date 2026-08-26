from __future__ import annotations

from dataclasses import dataclass, field, asdict
from collections import defaultdict

from membraneiq.autocommission import SignalProposal


@dataclass
class SensorBinding:
    source_name: str
    canonical_signal: str
    confidence: float
    confirmed: bool = False


@dataclass
class VesselProposal:
    vessel_id: str
    sensors: list[SensorBinding] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class StageProposal:
    stage_id: str
    vessels: dict[str, VesselProposal] = field(default_factory=dict)
    sensors: list[SensorBinding] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class TopologyProposal:
    system_id: str
    stages: dict[str, StageProposal]
    skid_sensors: list[SensorBinding]
    unresolved_signals: list[str]
    confidence: float
    requires_confirmation: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _binding(p: SignalProposal) -> SensorBinding:
    return SensorBinding(
        source_name=p.source_name,
        canonical_signal=p.canonical_signal or "unknown",
        confidence=p.confidence,
        confirmed=False,
    )


def reconstruct_topology(
    proposals: list[SignalProposal],
    system_id: str = "MEMBRANE-01",
    confidence_floor: float = 0.65,
) -> TopologyProposal:
    """Build only topology explicitly supported by discovered signal metadata.

    This function deliberately does not infer physical stages/vessels from
    process behavior alone. Missing topology must be confirmed/provided during
    commissioning rather than hallucinated.
    """
    stage_map: dict[str, StageProposal] = {}
    skid_sensors: list[SensorBinding] = []
    unresolved: list[str] = []

    for p in proposals:
        if not p.canonical_signal or p.confidence < confidence_floor:
            unresolved.append(p.source_name)
            continue

        sensor = _binding(p)
        if p.stage_hint:
            stage = stage_map.setdefault(p.stage_hint, StageProposal(stage_id=p.stage_hint))
            if p.vessel_hint:
                vessel = stage.vessels.setdefault(
                    p.vessel_hint, VesselProposal(vessel_id=p.vessel_hint)
                )
                vessel.sensors.append(sensor)
            else:
                stage.sensors.append(sensor)
        elif p.vessel_hint:
            # A vessel without stage context is retained as unresolved topology.
            unresolved.append(p.source_name)
        else:
            skid_sensors.append(sensor)

    evidence_scores: list[float] = []
    for stage in stage_map.values():
        stage_scores = [s.confidence for s in stage.sensors]
        for vessel in stage.vessels.values():
            vessel_scores = [s.confidence for s in vessel.sensors]
            vessel.confidence = round(sum(vessel_scores) / len(vessel_scores), 2) if vessel_scores else 0.0
            evidence_scores.extend(vessel_scores)
            stage_scores.extend(vessel_scores)
        stage.confidence = round(sum(stage_scores) / len(stage_scores), 2) if stage_scores else 0.0
        evidence_scores.extend([s.confidence for s in stage.sensors])

    evidence_scores.extend(s.confidence for s in skid_sensors)
    overall = round(sum(evidence_scores) / len(evidence_scores), 2) if evidence_scores else 0.0

    # Auto-discovered topology remains a proposal until a commissioning user confirms it.
    requires_confirmation = bool(stage_map or unresolved) or overall < 0.95

    return TopologyProposal(
        system_id=system_id,
        stages=dict(sorted(stage_map.items())),
        skid_sensors=skid_sensors,
        unresolved_signals=sorted(set(unresolved)),
        confidence=overall,
        requires_confirmation=requires_confirmation,
    )


def topology_summary(topology: TopologyProposal) -> dict:
    vessels = sum(len(stage.vessels) for stage in topology.stages.values())
    bound_sensors = len(topology.skid_sensors)
    for stage in topology.stages.values():
        bound_sensors += len(stage.sensors)
        bound_sensors += sum(len(v.sensors) for v in stage.vessels.values())

    return {
        "system_id": topology.system_id,
        "stages_detected": len(topology.stages),
        "vessels_detected": vessels,
        "signals_bound": bound_sensors,
        "unresolved_signals": len(topology.unresolved_signals),
        "topology_confidence": topology.confidence,
        "requires_confirmation": topology.requires_confirmation,
    }
