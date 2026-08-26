import pandas as pd

from membraneiq.autocommission import discover_signals
from membraneiq.process_pipeline import prepare_process_dataframe
from membraneiq.standardization import standardize_dataframe


def test_standardization_converts_mixed_units():
    raw = pd.DataFrame(
        {
            "UF01_Feed_Pressure_psi": [58.0],
            "UF01_Retentate_Pressure_bar": [3.2],
            "UF01_Permeate_Pressure_kPa": [20.0],
            "UF01_Permeate_Flow_gpm": [10.0],
            "UF01_Temperature_degF": [68.0],
        }
    )
    proposals = discover_signals(raw.columns)
    standardized, report = standardize_dataframe(raw, proposals)

    assert round(standardized["feed_pressure_bar"].iloc[0], 2) == 4.0
    assert round(standardized["permeate_pressure_bar"].iloc[0], 2) == 0.2
    assert round(standardized["permeate_flow_lph"].iloc[0], 1) == 2271.2
    assert round(standardized["temperature_c"].iloc[0], 1) == 20.0
    assert "feed_pressure_bar" in report.standardized_columns


def test_process_pipeline_calculates_available_metrics_without_conductivity():
    raw = pd.DataFrame(
        {
            "UF01_Feed_Pressure_bar": [4.0, 4.1, 4.2],
            "UF01_Retentate_Pressure_bar": [3.2, 3.25, 3.3],
            "UF01_Permeate_Pressure_bar": [0.2, 0.2, 0.2],
            "UF01_Permeate_Flow_LPH": [2400, 2350, 2300],
            "UF01_Temperature_degC": [20.0, 20.1, 20.2],
            "UF01_CIP_State": [0, 0, 1],
        }
    )
    prepared, report = prepare_process_dataframe(
        raw,
        discover_signals(raw.columns),
        membrane_area_m2=120.0,
    )

    assert "tmp_bar" in prepared.columns
    assert "pressure_drop_bar" in prepared.columns
    assert "flux_lmh" in prepared.columns
    assert "normalized_permeability_lmh_bar" in prepared.columns
    assert "rejection_fraction" not in prepared.columns
    assert report.production_rows == 2
    assert report.cip_rows == 1
