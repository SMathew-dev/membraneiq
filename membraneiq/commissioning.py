from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

from membraneiq.autocommission import data_readiness, discover_signals
from membraneiq.ingestion import CSVIngestor
from membraneiq.live_sources import ReadOnlyLiveSource
from membraneiq.topology_discovery import reconstruct_topology, topology_summary


@dataclass
class CommissioningReport:
    system_id: str
    source_mode: Literal["upload", "live"]
    source_label: str
    readiness: dict
    topology: dict
    auto_accepted_mappings: dict[str, str]
    review_required: list[dict]
    can_start_analysis: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _report(system_id: str, mode: str, label: str, proposals) -> CommissioningReport:
    readiness = data_readiness(proposals)
    topology = reconstruct_topology(proposals, system_id=system_id)
    accepted = {
        p.source_name: p.canonical_signal
        for p in proposals
        if p.canonical_signal and p.confidence >= 0.85
    }
    review = [
        {
            "source_name": p.source_name,
            "proposed_signal": p.canonical_signal,
            "confidence": p.confidence,
            "stage_hint": p.stage_hint,
            "vessel_hint": p.vessel_hint,
        }
        for p in proposals
        if not p.canonical_signal or p.confidence < 0.85
    ]
    return CommissioningReport(
        system_id=system_id,
        source_mode=mode,
        source_label=label,
        readiness=readiness,
        topology=topology_summary(topology),
        auto_accepted_mappings=accepted,
        review_required=review,
        can_start_analysis=readiness["ready_for_core_analysis"],
    )


def commission_csv(path: str | Path, system_id: str = "MEMBRANE-01") -> CommissioningReport:
    preview = CSVIngestor().preview(path)
    return _report(system_id, "upload", str(path), preview.proposals)


def commission_live(source: ReadOnlyLiveSource, system_id: str = "MEMBRANE-01") -> CommissioningReport:
    preview = source.commissioning_preview(system_id=system_id)
    return _report(system_id, "live", source.endpoint, preview.proposals)
