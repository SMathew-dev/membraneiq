from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from membraneiq.autocommission import SignalProposal, data_readiness, discover_signals


@dataclass
class IngestionPreview:
    rows: int
    columns: int
    proposals: list[SignalProposal]
    readiness: dict


class CSVIngestor:
    """Historical-data adapter feeding the same mapping pipeline as live sources."""

    def preview(self, path: str | Path) -> IngestionPreview:
        df = pd.read_csv(path)
        proposals = discover_signals(df.columns)
        return IngestionPreview(
            rows=len(df),
            columns=len(df.columns),
            proposals=proposals,
            readiness=data_readiness(proposals),
        )

    def load(self, path: str | Path) -> pd.DataFrame:
        return pd.read_csv(path)


def canonical_mapping(proposals: list[SignalProposal], confidence_floor: float = 0.85) -> dict[str, str]:
    """Return source-column -> canonical-signal mappings safe enough to auto-accept.

    Ambiguous/lower-confidence mappings are intentionally omitted for human review.
    """
    return {
        p.source_name: p.canonical_signal
        for p in proposals
        if p.canonical_signal is not None and p.confidence >= confidence_floor
    }
