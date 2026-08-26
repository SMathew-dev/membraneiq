from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import uuid


@dataclass
class CommissioningSession:
    system_id: str
    source_mode: str
    proposed_mappings: dict[str, str]
    confirmed_mappings: dict[str, str] = field(default_factory=dict)
    rejected_sources: list[str] = field(default_factory=list)
    topology_confirmed: bool = False
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def confirm_mapping(self, source_name: str, canonical_signal: str) -> None:
        self.confirmed_mappings[source_name] = canonical_signal
        if source_name in self.rejected_sources:
            self.rejected_sources.remove(source_name)

    def reject_mapping(self, source_name: str) -> None:
        self.confirmed_mappings.pop(source_name, None)
        if source_name not in self.rejected_sources:
            self.rejected_sources.append(source_name)

    @property
    def effective_mappings(self) -> dict[str, str]:
        mappings = dict(self.proposed_mappings)
        for source in self.rejected_sources:
            mappings.pop(source, None)
        mappings.update(self.confirmed_mappings)
        return mappings

    def confirm_topology(self) -> None:
        self.topology_confirmed = True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["effective_mappings"] = self.effective_mappings
        return data
