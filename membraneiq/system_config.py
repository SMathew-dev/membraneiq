from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import json


@dataclass
class CommissionedSystem:
    system_id: str
    name: str
    source_mode: str
    source_reference: str
    mappings: dict[str, str]
    topology: dict
    observability: dict
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class SystemConfigStore:
    """Portable JSON configuration store for commissioned membrane systems.

    This keeps commissioning durable in v0.2 while preserving a clean boundary
    for later migration to PostgreSQL or another production database.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load_payload(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, system: CommissionedSystem) -> None:
        payload = self._load_payload()
        payload[system.system_id] = system.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, system_id: str) -> CommissionedSystem | None:
        data = self._load_payload().get(system_id)
        return None if data is None else CommissionedSystem(**data)

    def list(self) -> list[CommissionedSystem]:
        return [CommissionedSystem(**value) for value in self._load_payload().values()]

    def delete(self, system_id: str) -> bool:
        payload = self._load_payload()
        if system_id not in payload:
            return False
        del payload[system_id]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True
