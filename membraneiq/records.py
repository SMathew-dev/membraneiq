from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal


AssetType = Literal["skid", "stage", "vessel", "element"]


@dataclass
class HealthSnapshot:
    timestamp: str
    health_score: float
    status: str
    normalized_permeability_loss_pct: float
    tmp_change_pct: float
    pressure_drop_change_pct: float
    latest_cip_recovery_pct: float | None
    diagnosis: str


@dataclass
class MaintenanceEvent:
    timestamp: str
    event_type: Literal["INSTALL", "CIP", "INSPECTION", "REPLACEMENT", "MOVE"]
    notes: str = ""
    recovery_pct: float | None = None


@dataclass
class MembraneHealthRecord:
    """Persistent operating and condition history for one membrane asset."""

    asset_id: str
    asset_type: AssetType
    system_id: str
    stage_id: str | None = None
    vessel_id: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    installed_at: str | None = None
    operating_hours: float = 0.0
    cip_count: int = 0
    snapshots: list[HealthSnapshot] = field(default_factory=list)
    maintenance_events: list[MaintenanceEvent] = field(default_factory=list)

    def add_snapshot(self, snapshot: HealthSnapshot) -> None:
        self.snapshots.append(snapshot)

    def add_maintenance_event(self, event: MaintenanceEvent) -> None:
        self.maintenance_events.append(event)
        if event.event_type == "CIP":
            self.cip_count += 1

    @property
    def current_health_score(self) -> float | None:
        if not self.snapshots:
            return None
        return self.snapshots[-1].health_score

    @property
    def current_status(self) -> str:
        if not self.snapshots:
            return "UNKNOWN"
        return self.snapshots[-1].status

    @property
    def latest_cip_recovery_pct(self) -> float | None:
        cip_events = [
            event.recovery_pct
            for event in self.maintenance_events
            if event.event_type == "CIP" and event.recovery_pct is not None
        ]
        if cip_events:
            return cip_events[-1]

        if self.snapshots:
            return self.snapshots[-1].latest_cip_recovery_pct
        return None

    def degradation_rate_points_per_100h(self) -> float | None:
        """Estimate health-score decline per 100 operating hours from snapshots."""
        if len(self.snapshots) < 2 or self.operating_hours <= 0:
            return None

        first = self.snapshots[0].health_score
        latest = self.snapshots[-1].health_score
        decline = first - latest
        return round((decline / self.operating_hours) * 100.0, 2)

    def to_dict(self) -> dict:
        return asdict(self)


def snapshot_from_assessment(assessment, timestamp: str | None = None) -> HealthSnapshot:
    """Create a persistent snapshot from the v0.1 health assessment object."""
    timestamp = timestamp or datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return HealthSnapshot(
        timestamp=timestamp,
        health_score=assessment.health_score,
        status=assessment.status,
        normalized_permeability_loss_pct=assessment.normalized_permeability_loss_pct,
        tmp_change_pct=assessment.tmp_change_pct,
        pressure_drop_change_pct=assessment.pressure_drop_change_pct,
        latest_cip_recovery_pct=assessment.latest_cip_recovery_pct,
        diagnosis=assessment.diagnosis,
    )
