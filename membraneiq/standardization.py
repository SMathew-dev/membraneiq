from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd

from membraneiq.autocommission import SignalProposal
from membraneiq.normalization import (
    normalize_conductivity,
    normalize_flow,
    normalize_pressure,
    normalize_temperature,
)


CANONICAL_OUTPUT_COLUMNS = {
    "feed_pressure": "feed_pressure_bar",
    "retentate_pressure": "retentate_pressure_bar",
    "permeate_pressure": "permeate_pressure_bar",
    "feed_flow": "feed_flow_lph",
    "permeate_flow": "permeate_flow_lph",
    "temperature": "temperature_c",
    "feed_conductivity": "feed_conductivity_ms_cm",
    "permeate_conductivity": "permeate_conductivity_ms_cm",
    "cip_state": "cip_state",
}

DEFAULT_CANONICAL_UNITS = {
    "feed_pressure": "bar",
    "retentate_pressure": "bar",
    "permeate_pressure": "bar",
    "feed_flow": "L/h",
    "permeate_flow": "L/h",
    "temperature": "C",
    "feed_conductivity": "mS/cm",
    "permeate_conductivity": "mS/cm",
}


@dataclass
class StandardizationReport:
    standardized_columns: list[str]
    skipped_sources: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _convert_series(series: pd.Series, signal: str, unit: str | None) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if signal == "cip_state":
        return numeric.fillna(0).astype(int)

    effective_unit = unit or DEFAULT_CANONICAL_UNITS.get(signal)
    if effective_unit is None:
        raise ValueError(f"No unit available for {signal}")

    if signal.endswith("pressure"):
        return numeric.map(
            lambda value: normalize_pressure(value, effective_unit).value if pd.notna(value) else float("nan")
        )
    if signal.endswith("flow"):
        return numeric.map(
            lambda value: normalize_flow(value, effective_unit).value if pd.notna(value) else float("nan")
        )
    if signal == "temperature":
        return numeric.map(
            lambda value: normalize_temperature(value, effective_unit).value if pd.notna(value) else float("nan")
        )
    if "conductivity" in signal:
        return numeric.map(
            lambda value: normalize_conductivity(value, effective_unit).value if pd.notna(value) else float("nan")
        )
    return numeric


def standardize_dataframe(
    df: pd.DataFrame,
    proposals: list[SignalProposal],
    confirmed_mappings: dict[str, str] | None = None,
    unit_overrides: dict[str, str] | None = None,
    confidence_floor: float = 0.85,
) -> tuple[pd.DataFrame, StandardizationReport]:
    """Convert heterogeneous plant columns into MembraneIQ's engineering schema.

    Auto-mappings below the confidence threshold are not consumed unless the
    commissioning user explicitly confirms them. Duplicate mappings to the same
    canonical signal are rejected rather than silently choosing one sensor.
    """
    confirmed_mappings = confirmed_mappings or {}
    unit_overrides = unit_overrides or {}
    proposal_by_source = {proposal.source_name: proposal for proposal in proposals}

    selected: dict[str, tuple[str, str | None]] = {}
    warnings: list[str] = []
    skipped: list[str] = []

    for source in df.columns:
        proposal = proposal_by_source.get(str(source))
        signal = confirmed_mappings.get(str(source))
        if signal is None and proposal and proposal.canonical_signal and proposal.confidence >= confidence_floor:
            signal = proposal.canonical_signal
        if signal is None:
            skipped.append(str(source))
            continue
        if signal not in CANONICAL_OUTPUT_COLUMNS:
            warnings.append(f"{source}: unsupported canonical signal '{signal}'")
            skipped.append(str(source))
            continue

        if signal in selected:
            previous = selected[signal][0]
            raise ValueError(
                f"Multiple source columns map to '{signal}': '{previous}' and '{source}'. Confirm one explicitly."
            )
        detected_unit = proposal.detected_unit if proposal else None
        selected[signal] = (str(source), unit_overrides.get(str(source), detected_unit))

    result = pd.DataFrame(index=df.index)
    for signal, (source, unit) in selected.items():
        output_column = CANONICAL_OUTPUT_COLUMNS[signal]
        result[output_column] = _convert_series(df[source], signal, unit)

    return result, StandardizationReport(
        standardized_columns=list(result.columns),
        skipped_sources=skipped,
        warnings=warnings,
    )
