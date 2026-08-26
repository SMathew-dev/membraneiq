from __future__ import annotations

from pathlib import Path

from membraneiq.baseline import CleanBaseline
from membraneiq.commissioning import commission_csv, commission_live
from membraneiq.degradation import DegradationTrend
from membraneiq.economics import PlantEconomics
from membraneiq.engine import MembraneIQEngine
from membraneiq.live_sources import ReadOnlyLiveSource


class MembraneIQService:
    """Stable boundary intended for the future web API and UI."""

    def __init__(self):
        self.engine = MembraneIQEngine()

    def preview_upload(self, path: str | Path, system_id: str = "MEMBRANE-01") -> dict:
        return commission_csv(path, system_id=system_id).to_dict()

    def preview_live(self, source: ReadOnlyLiveSource, system_id: str = "MEMBRANE-01") -> dict:
        return commission_live(source, system_id=system_id).to_dict()

    def analyze_asset(
        self,
        system_id: str,
        asset_id: str,
        current_metrics: dict[str, float],
        baseline: CleanBaseline,
        trends: list[DegradationTrend] | None = None,
        plant_economics: PlantEconomics | None = None,
        healthy_permeate_flow_lph: float | None = None,
        current_permeate_flow_lph: float | None = None,
        **cip_inputs,
    ) -> dict:
        return self.engine.analyze(
            system_id=system_id,
            asset_id=asset_id,
            current_metrics=current_metrics,
            baseline=baseline,
            trends=trends,
            plant_economics=plant_economics,
            healthy_permeate_flow_lph=healthy_permeate_flow_lph,
            current_permeate_flow_lph=current_permeate_flow_lph,
            **cip_inputs,
        ).to_dict()
