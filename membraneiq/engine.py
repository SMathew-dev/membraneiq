from __future__ import annotations

from dataclasses import dataclass, asdict

from membraneiq.anomaly import assess_anomalies
from membraneiq.baseline import CleanBaseline
from membraneiq.cip_effectiveness import assess_cip_recovery
from membraneiq.decision_engine import recommend_action
from membraneiq.degradation import DegradationTrend
from membraneiq.economics import PlantEconomics, assess_economics
from membraneiq.intervention import compare_clean_vs_run


@dataclass
class AnalysisResult:
    system_id: str
    asset_id: str
    anomaly: dict
    trends: list[dict]
    cip: dict | None
    decision: dict
    economics: dict | None
    intervention: dict | None

    def to_dict(self) -> dict:
        return asdict(self)


class MembraneIQEngine:
    """Application-level orchestration of MembraneIQ intelligence modules."""

    def analyze(
        self,
        system_id: str,
        asset_id: str,
        current_metrics: dict[str, float],
        baseline: CleanBaseline,
        trends: list[DegradationTrend] | None = None,
        pre_cip_value: float | None = None,
        post_cip_value: float | None = None,
        cip_baseline_value: float | None = None,
        cip_higher_is_better: bool = True,
        healthy_permeate_flow_lph: float | None = None,
        current_permeate_flow_lph: float | None = None,
        plant_economics: PlantEconomics | None = None,
    ) -> AnalysisResult:
        trends = trends or []
        anomaly = assess_anomalies(current_metrics, baseline)

        cip = None
        latest_recovery = None
        if None not in (pre_cip_value, post_cip_value, cip_baseline_value):
            cip_obj = assess_cip_recovery(
                pre_cip_value,
                post_cip_value,
                cip_baseline_value,
                higher_is_better=cip_higher_is_better,
            )
            cip = cip_obj.to_dict()
            latest_recovery = cip_obj.recovery_pct

        decision = recommend_action(anomaly, trends, latest_cip_recovery_pct=latest_recovery)

        economics = None
        intervention = None
        if (
            plant_economics is not None
            and healthy_permeate_flow_lph is not None
            and current_permeate_flow_lph is not None
        ):
            economic_obj = assess_economics(
                healthy_permeate_flow_lph,
                current_permeate_flow_lph,
                plant_economics,
            )
            economics = economic_obj.to_dict()
            intervention = compare_clean_vs_run(economic_obj).to_dict()

        return AnalysisResult(
            system_id=system_id,
            asset_id=asset_id,
            anomaly=anomaly.to_dict(),
            trends=[trend.to_dict() for trend in trends],
            cip=cip,
            decision=decision.to_dict(),
            economics=economics,
            intervention=intervention,
        )
