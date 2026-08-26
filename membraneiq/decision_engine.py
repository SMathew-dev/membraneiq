from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum

from membraneiq.anomaly import AnomalyAssessment, Severity
from membraneiq.degradation import DegradationTrend


class RecommendedAction(str, Enum):
    RUN = "RUN"
    MONITOR = "MONITOR"
    CLEAN = "CLEAN"
    INSPECT = "INSPECT"


@dataclass(frozen=True)
class Decision:
    action: RecommendedAction
    confidence: float
    reasons: list[str]
    requires_operator_review: bool = True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["action"] = self.action.value
        return data


def recommend_action(
    anomalies: AnomalyAssessment,
    trends: list[DegradationTrend],
    latest_cip_recovery_pct: float | None = None,
) -> Decision:
    """Advisory-only decision support; never issues equipment commands."""
    degrading = [t for t in trends if t.direction == "DEGRADING" and t.r_squared >= 0.5]
    reasons: list[str] = []

    if anomalies.overall_severity == Severity.CRITICAL:
        reasons.append("One or more process metrics are critically outside the learned baseline")
        if latest_cip_recovery_pct is not None and latest_cip_recovery_pct < 80:
            reasons.append(f"Recent CIP recovery is weak ({latest_cip_recovery_pct:.1f}%)")
            return Decision(RecommendedAction.INSPECT, 0.9, reasons)
        return Decision(RecommendedAction.CLEAN, 0.82, reasons)

    if anomalies.overall_severity == Severity.WARNING:
        reasons.append("Process metrics materially deviate from the learned baseline")
        if degrading:
            reasons.append("Persistent degradation trend supports intervention")
            return Decision(RecommendedAction.CLEAN, 0.78, reasons)
        return Decision(RecommendedAction.MONITOR, 0.68, reasons)

    if anomalies.overall_severity == Severity.WATCH or degrading:
        reasons.append("Early deviation or degradation trend detected")
        return Decision(RecommendedAction.MONITOR, 0.7, reasons)

    reasons.append("Current production behavior remains within the learned baseline")
    return Decision(RecommendedAction.RUN, 0.88, reasons)
