from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

Scenario = Literal["healthy", "gradual_fouling", "severe_fouling", "incomplete_cip_recovery"]


@dataclass
class SimulatorConfig:
    seed: int = 42
    membrane_area_m2: float = 120.0
    sample_minutes: int = 10
    total_hours: int = 48
    cip_start_hour: float = 32.0
    cip_duration_hour: float = 1.0


def _noise(rng: np.random.Generator, n: int, scale: float) -> np.ndarray:
    return rng.normal(0.0, scale, n)


def simulate_membrane_run(scenario: Scenario = "gradual_fouling", config: SimulatorConfig | None = None) -> pd.DataFrame:
    config = config or SimulatorConfig()
    rng = np.random.default_rng(config.seed)
    points = int(config.total_hours * 60 / config.sample_minutes) + 1
    elapsed_h = np.arange(points) * config.sample_minutes / 60.0

    cip_active = (elapsed_h >= config.cip_start_hour) & (elapsed_h < config.cip_start_hour + config.cip_duration_hour)
    pre = np.clip(elapsed_h / config.cip_start_hour, 0.0, 1.0)

    if scenario == "healthy":
        severity = 0.05 * pre
        recovery = 1.00
    elif scenario == "gradual_fouling":
        severity = 0.55 * (pre ** 1.7)
        recovery = 0.98
    elif scenario == "severe_fouling":
        severity = 0.90 * (pre ** 2.1)
        recovery = 0.93
    elif scenario == "incomplete_cip_recovery":
        severity = 0.72 * (pre ** 1.9)
        recovery = 0.82
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    post_cip = elapsed_h >= (config.cip_start_hour + config.cip_duration_hour)
    post_elapsed = np.maximum(elapsed_h - (config.cip_start_hour + config.cip_duration_hour), 0.0)
    residual = (1.0 - recovery) * severity.max()
    refouling = 0.18 * np.clip(post_elapsed / max(config.total_hours - config.cip_start_hour - config.cip_duration_hour, 1), 0, 1) ** 1.5
    severity = np.where(post_cip, residual + refouling, severity)
    severity = np.where(cip_active, np.nan, severity)

    temperature_c = 20.0 + 1.8 * np.sin(elapsed_h / 3.5) + _noise(rng, points, 0.18)
    feed_flow_lph = 4800.0 + 120.0 * np.sin(elapsed_h / 2.8) + _noise(rng, points, 35.0)
    feed_pressure_bar = 3.20 + 1.05 * np.nan_to_num(severity) + _noise(rng, points, 0.025)
    pressure_drop = 0.42 + 0.62 * np.nan_to_num(severity) + _noise(rng, points, 0.015)
    retentate_pressure_bar = feed_pressure_bar - pressure_drop
    permeate_pressure_bar = 0.18 + _noise(rng, points, 0.008)
    permeate_flow_lph = 2450.0 * (1.0 - 0.48 * np.nan_to_num(severity)) * (1.0 + 0.008 * (temperature_c - 20.0)) + _noise(rng, points, 18.0)

    feed_cond = 8.5 + 0.35 * np.sin(elapsed_h / 6.0) + _noise(rng, points, 0.04)
    rejection = 0.94 - 0.025 * np.nan_to_num(severity)
    permeate_cond = feed_cond * (1.0 - rejection) + _noise(rng, points, 0.01)

    for arr in (feed_flow_lph, feed_pressure_bar, retentate_pressure_bar, permeate_pressure_bar, permeate_flow_lph, feed_cond, permeate_cond):
        arr[cip_active] = np.nan

    timestamps = pd.date_range("2026-01-01", periods=points, freq=f"{config.sample_minutes}min")

    return pd.DataFrame({
        "timestamp": timestamps,
        "elapsed_hours": elapsed_h,
        "scenario": scenario,
        "cip_active": cip_active,
        "membrane_area_m2": config.membrane_area_m2,
        "temperature_c": temperature_c,
        "feed_flow_lph": feed_flow_lph,
        "feed_pressure_bar": feed_pressure_bar,
        "retentate_pressure_bar": retentate_pressure_bar,
        "permeate_pressure_bar": permeate_pressure_bar,
        "permeate_flow_lph": permeate_flow_lph,
        "feed_conductivity_ms_cm": feed_cond,
        "permeate_conductivity_ms_cm": permeate_cond,
        "true_fouling_state": severity,
    })
