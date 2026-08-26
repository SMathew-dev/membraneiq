from __future__ import annotations

import json
from pathlib import Path

from membraneiq.records import HealthSnapshot, MaintenanceEvent, MembraneHealthRecord


class HealthRecordStore:
    """Simple JSON persistence layer for MembraneIQ asset histories.

    v0.2 intentionally uses a portable file store. The API boundary allows the
    implementation to be replaced by SQLite/PostgreSQL without changing the
    analytics layer.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, records: list[MembraneHealthRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {record.asset_id: record.to_dict() for record in records}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> dict[str, MembraneHealthRecord]:
        if not self.path.exists():
            return {}

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        records: dict[str, MembraneHealthRecord] = {}
        for asset_id, data in payload.items():
            snapshots = [HealthSnapshot(**item) for item in data.pop("snapshots", [])]
            events = [MaintenanceEvent(**item) for item in data.pop("maintenance_events", [])]
            record = MembraneHealthRecord(**data)
            record.snapshots = snapshots
            record.maintenance_events = events
            records[asset_id] = record
        return records

    def upsert(self, record: MembraneHealthRecord) -> None:
        records = self.load()
        records[record.asset_id] = record
        self.save(list(records.values()))
