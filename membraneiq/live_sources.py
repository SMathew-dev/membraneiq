from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from membraneiq.autocommission import SignalProposal, data_readiness, discover_signals
from membraneiq.topology_discovery import TopologyProposal, reconstruct_topology


@dataclass(frozen=True)
class LiveTag:
    name: str
    value: Any = None
    unit: str | None = None
    quality: str = "UNKNOWN"
    timestamp: str | None = None


@dataclass
class LiveCommissioningPreview:
    source_type: str
    endpoint: str
    tags: list[LiveTag]
    proposals: list[SignalProposal]
    readiness: dict
    topology: TopologyProposal


class ReadOnlyLiveSource(ABC):
    """Common boundary for plant data sources.

    MembraneIQ's initial industrial integration is deliberately read-only.
    Implementations may browse/read tags but must not expose PLC write methods.
    """

    source_type = "generic"

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def browse_tags(self) -> list[LiveTag]:
        raise NotImplementedError

    @abstractmethod
    def read_tags(self, names: list[str]) -> list[LiveTag]:
        raise NotImplementedError

    def commissioning_preview(self, system_id: str = "MEMBRANE-01") -> LiveCommissioningPreview:
        tags = self.browse_tags()
        labels = [f"{tag.name} {tag.unit or ''}".strip() for tag in tags]
        proposals = discover_signals(labels)
        topology = reconstruct_topology(proposals, system_id=system_id)
        return LiveCommissioningPreview(
            source_type=self.source_type,
            endpoint=self.endpoint,
            tags=tags,
            proposals=proposals,
            readiness=data_readiness(proposals),
            topology=topology,
        )


class SimulatedPlantSource(ReadOnlyLiveSource):
    """Deterministic source used to exercise the live commissioning pipeline."""

    source_type = "simulated_plc"

    def __init__(self, endpoint: str = "sim://uf-01"):
        super().__init__(endpoint)
        self.connected = False
        self._values = {
            "UF01_Stage1_Vessel1_Feed_Pressure": (4.2, "bar"),
            "UF01_Stage1_Vessel1_Permeate_Flow": (2410.0, "L/h"),
            "UF01_Stage2_Vessel3_Feed_Pressure": (5.1, "bar"),
            "UF01_Stage2_Vessel3_Permeate_Flow": (1840.0, "L/h"),
            "UF01_Retentate_Pressure": (3.6, "bar"),
            "UF01_Permeate_Pressure": (0.4, "bar"),
            "UF01_Temperature": (19.8, "C"),
            "UF01_Permeate_Conductivity": (0.42, "mS/cm"),
            "UF01_CIP_State": (0, None),
        }

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def _require_connection(self) -> None:
        if not self.connected:
            raise RuntimeError("Live source is not connected")

    def browse_tags(self) -> list[LiveTag]:
        self._require_connection()
        return [LiveTag(name=name, unit=unit) for name, (_, unit) in self._values.items()]

    def read_tags(self, names: list[str]) -> list[LiveTag]:
        self._require_connection()
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for name in names:
            if name not in self._values:
                result.append(LiveTag(name=name, quality="BAD", timestamp=now))
                continue
            value, unit = self._values[name]
            result.append(
                LiveTag(name=name, value=value, unit=unit, quality="GOOD", timestamp=now)
            )
        return result
