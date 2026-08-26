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
    source_type: str = "unknown"
    sheet_name: str | None = None


class CSVIngestor:
    """Historical CSV adapter feeding the same mapping pipeline as live sources."""

    source_type = "csv"

    def preview(self, path: str | Path) -> IngestionPreview:
        df = self.load(path)
        proposals = discover_signals(df.columns)
        return IngestionPreview(
            rows=len(df),
            columns=len(df.columns),
            proposals=proposals,
            readiness=data_readiness(proposals),
            source_type=self.source_type,
        )

    def load(self, path: str | Path) -> pd.DataFrame:
        return pd.read_csv(path)


class ExcelIngestor:
    """Historical Excel adapter. Requires the optional `openpyxl` dependency."""

    source_type = "excel"

    def __init__(self, sheet_name: str | int | None = 0):
        self.sheet_name = sheet_name

    def preview(self, path: str | Path) -> IngestionPreview:
        df = self.load(path)
        proposals = discover_signals(df.columns)
        return IngestionPreview(
            rows=len(df),
            columns=len(df.columns),
            proposals=proposals,
            readiness=data_readiness(proposals),
            source_type=self.source_type,
            sheet_name=str(self.sheet_name) if self.sheet_name is not None else None,
        )

    def load(self, path: str | Path) -> pd.DataFrame:
        try:
            return pd.read_excel(path, sheet_name=self.sheet_name, engine="openpyxl")
        except ImportError as exc:
            raise RuntimeError(
                "Excel ingestion requires the optional 'openpyxl' dependency"
            ) from exc


def ingestor_for_path(path: str | Path, sheet_name: str | int | None = 0):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return CSVIngestor()
    if suffix in {".xlsx", ".xlsm"}:
        return ExcelIngestor(sheet_name=sheet_name)
    raise ValueError(f"Unsupported historical file type: {suffix or '<none>'}")


def preview_historical_file(path: str | Path, sheet_name: str | int | None = 0) -> IngestionPreview:
    return ingestor_for_path(path, sheet_name=sheet_name).preview(path)


def canonical_mapping(proposals: list[SignalProposal], confidence_floor: float = 0.85) -> dict[str, str]:
    """Return source-column -> canonical-signal mappings safe enough to auto-accept.

    Ambiguous/lower-confidence mappings are intentionally omitted for human review.
    """
    return {
        p.source_name: p.canonical_signal
        for p in proposals
        if p.canonical_signal is not None and p.confidence >= confidence_floor
    }
