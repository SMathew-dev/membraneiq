from __future__ import annotations

import numpy as np
import pandas as pd

REFERENCE_TEMPERATURE_C = 20.0


def calculate_tmp(feed_pressure_bar: pd.Series, retentate_pressure_bar: pd.Series, permeate_pressure_bar: pd.Series) -> pd.Series:
    """Simplified average-feed-side TMP in bar."""
    return ((feed_pressure_bar + retentate_pressure_bar) / 2.0) - permeate_pressure_bar


def calculate_flux(permeate_flow_lph: pd.Series, membrane_area_m2: pd.Series) -> pd.Series:
    """Flux in L/m²/h."""
    return permeate_flow_lph / membrane_area_m2


def calculate_permeability(flux_lmh: pd.Series, tmp_bar: pd.Series) -> pd.Series:
    safe_tmp = tmp_bar.replace(0, np.nan)
    return flux_lmh / safe_tmp


def temperature_correction_factor(temperature_c: pd.Series, reference_temperature_c: float = REFERENCE_TEMPERATURE_C, coefficient: float = 0.023) -> pd.Series:
    return np.exp(coefficient * (reference_temperature_c - temperature_c))


def calculate_normalized_permeability(permeability_lmh_bar: pd.Series, temperature_c: pd.Series, reference_temperature_c: float = REFERENCE_TEMPERATURE_C) -> pd.Series:
    return permeability_lmh_bar * temperature_correction_factor(temperature_c, reference_temperature_c)


def calculate_pressure_drop(feed_pressure_bar: pd.Series, retentate_pressure_bar: pd.Series) -> pd.Series:
    return feed_pressure_bar - retentate_pressure_bar


def calculate_rejection(feed_conductivity_ms_cm: pd.Series, permeate_conductivity_ms_cm: pd.Series) -> pd.Series:
    safe_feed = feed_conductivity_ms_cm.replace(0, np.nan)
    return 1.0 - (permeate_conductivity_ms_cm / safe_feed)


def enrich_process_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["tmp_bar"] = calculate_tmp(out["feed_pressure_bar"], out["retentate_pressure_bar"], out["permeate_pressure_bar"])
    out["flux_lmh"] = calculate_flux(out["permeate_flow_lph"], out["membrane_area_m2"])
    out["permeability_lmh_bar"] = calculate_permeability(out["flux_lmh"], out["tmp_bar"])
    out["normalized_permeability_lmh_bar"] = calculate_normalized_permeability(out["permeability_lmh_bar"], out["temperature_c"])
    out["pressure_drop_bar"] = calculate_pressure_drop(out["feed_pressure_bar"], out["retentate_pressure_bar"])
    out["rejection_fraction"] = calculate_rejection(out["feed_conductivity_ms_cm"], out["permeate_conductivity_ms_cm"])
    return out
