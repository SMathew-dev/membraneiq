from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

REFERENCE_TEMPERATURE_C = 20.0


@dataclass(frozen=True)
class EngineeringContext:
    membrane_area_m2: float | None = None
    reference_temperature_c: float = REFERENCE_TEMPERATURE_C


def calculate_tmp(feed_pressure_bar: pd.Series, retentate_pressure_bar: pd.Series, permeate_pressure_bar: pd.Series) -> pd.Series:
    """Simplified average-feed-side TMP in bar."""
    return ((feed_pressure_bar + retentate_pressure_bar) / 2.0) - permeate_pressure_bar


def calculate_flux(permeate_flow_lph: pd.Series, membrane_area_m2: pd.Series) -> pd.Series:
    """Flux in L/m²/h."""
    safe_area = membrane_area_m2.replace(0, np.nan)
    return permeate_flow_lph / safe_area


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


def enrich_available_process_data(
    df: pd.DataFrame,
    context: EngineeringContext | None = None,
) -> pd.DataFrame:
    """Calculate every defensible engineering metric supported by available data.

    Real plants have different instrumentation. Missing conductivity or membrane
    area must reduce capability rather than crash the entire analysis pipeline.
    """
    context = context or EngineeringContext()
    out = df.copy()

    if {"feed_pressure_bar", "retentate_pressure_bar", "permeate_pressure_bar"}.issubset(out.columns):
        out["tmp_bar"] = calculate_tmp(
            out["feed_pressure_bar"],
            out["retentate_pressure_bar"],
            out["permeate_pressure_bar"],
        )

    if {"feed_pressure_bar", "retentate_pressure_bar"}.issubset(out.columns):
        out["pressure_drop_bar"] = calculate_pressure_drop(
            out["feed_pressure_bar"],
            out["retentate_pressure_bar"],
        )

    if "permeate_flow_lph" in out.columns:
        if "membrane_area_m2" not in out.columns and context.membrane_area_m2 is not None:
            out["membrane_area_m2"] = float(context.membrane_area_m2)
        if "membrane_area_m2" in out.columns:
            out["flux_lmh"] = calculate_flux(out["permeate_flow_lph"], out["membrane_area_m2"])

    if {"flux_lmh", "tmp_bar"}.issubset(out.columns):
        out["permeability_lmh_bar"] = calculate_permeability(out["flux_lmh"], out["tmp_bar"])

    if {"permeability_lmh_bar", "temperature_c"}.issubset(out.columns):
        out["normalized_permeability_lmh_bar"] = calculate_normalized_permeability(
            out["permeability_lmh_bar"],
            out["temperature_c"],
            reference_temperature_c=context.reference_temperature_c,
        )

    if {"feed_conductivity_ms_cm", "permeate_conductivity_ms_cm"}.issubset(out.columns):
        out["rejection_fraction"] = calculate_rejection(
            out["feed_conductivity_ms_cm"],
            out["permeate_conductivity_ms_cm"],
        )

    return out


def enrich_process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible strict v0.1 enrichment."""
    required = {
        "feed_pressure_bar",
        "retentate_pressure_bar",
        "permeate_pressure_bar",
        "permeate_flow_lph",
        "membrane_area_m2",
        "temperature_c",
        "feed_conductivity_ms_cm",
        "permeate_conductivity_ms_cm",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(f"Strict enrichment missing required columns: {missing}")
    return enrich_available_process_data(df)
