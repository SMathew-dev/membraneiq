from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum

from membraneiq.baseline import CleanBaseline, robust_deviation


class Severity(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class MetricAnomaly:
    metric: str
    value: float
    baseline: float
    deviation: float
    severity: Severity
    direction: str


@dataclass
class AnomalyAssessment:
    anomalies: list[MetricAnomaly]
    overall_severity: Severity
    anomaly_score: float

    def to_dict(self) -> dict:
        return {
            "anomalies": [asdict(item) for item in self.anomalies],
            "overall_severity": self.overall_severity.value,
            "anomaly_score": self.anomaly_score,
        }


def _severity(abs_deviation: float) -> Severity:
    if abs_deviation >= 6:
        return Severity.CRITICAL
    if abs_deviation >= 4:
        return Severity.WARNING
    if abs_deviation >= 2.5:
        return Severity.WATCH
    return Severity.NORMAL


def assess_anomalies(values: dict[str, float], baseline: CleanBaseline) -> AnomalyAssessment:
    anomalies: list[MetricAnomaly] = []
    max_abs = 0.0
    rank = {Severity.NORMAL: 0, Severity.WATCH: 1, Severity.WARNING: 2, Severity.CRITICAL: 3}
    overall = Severity.NORMAL

    for metric, value in values.items():
        if metric not in baseline.metrics:
            continue
        reference = baseline.metrics[metric]
        deviation = robust_deviation(value, reference)
        abs_dev = abs(deviation)
        severity = _severity(abs_dev)
        max_abs = max(max_abs, min(abs_dev, 10.0))
        if rank[severity] > rank[overall]:
            overall = severity
        anomalies.append(
            MetricAnomaly(
                metric=metric,
                value=float(value),
                baseline=reference.median,
                deviation=round(deviation, 2),
                severity=severity,
                direction="HIGH" if deviation > 0 else "LOW" if deviation < 0 else "NORMAL",
            )
        )

    return AnomalyAssessment(
        anomalies=anomalies,
        overall_severity=overall,
        anomaly_score=round(min(100.0, max_abs * 10.0), 1),
    )
