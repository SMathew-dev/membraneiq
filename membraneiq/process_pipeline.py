from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd

from membraneiq.autocommission import SignalProposal
from membraneiq.data_quality import assess_dataframe
from membraneiq.engineering import EngineeringContext, enrich_available_process_data
from membraneiq.operating_state import detect_state
from membraneiq.standardization import standardize_dataframe


@dataclass
class ProcessPreparationReport:
    raw_rows: int
    standardized_columns: list[str]
    calculated_columns: list[str]
    data_quality: dict
    standardization: dict
    production_rows: int
    cip_rows: int
    unknown_rows: int

    def to_dict(self) -> dict:
        return asdict(self)


def _state_for_row(row: pd.Series) -> str:
    result = detect_state(
        permeate_flow_lph=row.get("permeate_flow_lph"),
        feed_pressure_bar=row.get("feed_pressure_bar"),
        cip_state=row.get("cip_state"),
    )
    return result.state.value


def prepare_process_dataframe(
    raw_df: pd.DataFrame,
    proposals: list[SignalProposal],
    confirmed_mappings: dict[str, str] | None = None,
    unit_overrides: dict[str, str] | None = None,
    membrane_area_m2: float | None = None,
) -> tuple[pd.DataFrame, ProcessPreparationReport]:
    standardized, standardization_report = standardize_dataframe(
        raw_df,
        proposals,
        confirmed_mappings=confirmed_mappings,
        unit_overrides=unit_overrides,
    )
    quality = assess_dataframe(standardized)

    standardized["operating_state"] = standardized.apply(_state_for_row, axis=1)
    enriched = enrich_available_process_data(
        standardized,
        EngineeringContext(membrane_area_m2=membrane_area_m2),
    )

    calculated = [column for column in enriched.columns if column not in standardized.columns]
    counts = enriched["operating_state"].value_counts().to_dict()

    report = ProcessPreparationReport(
        raw_rows=len(raw_df),
        standardized_columns=[column for column in standardized.columns if column != "operating_state"],
        calculated_columns=calculated,
        data_quality=quality.to_dict(),
        standardization=standardization_report.to_dict(),
        production_rows=int(counts.get("PRODUCTION", 0)),
        cip_rows=int(counts.get("CIP", 0)),
        unknown_rows=int(counts.get("UNKNOWN", 0)),
    )
    return enriched, report
