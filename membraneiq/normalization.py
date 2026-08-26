from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class NormalizedValue:
    value: float
    unit: str


PRESSURE_TO_BAR = {
    "bar": 1.0,
    "kpa": 0.01,
    "mpa": 10.0,
    "psi": 0.0689475729,
}

FLOW_TO_LPH = {
    "l/h": 1.0,
    "lph": 1.0,
    "l/min": 60.0,
    "m3/h": 1000.0,
    "m³/h": 1000.0,
    "gpm": 227.124707,
}

CONDUCTIVITY_TO_MSCM = {
    "ms/cm": 1.0,
    "us/cm": 0.001,
    "µs/cm": 0.001,
}


def _finite(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Process value must be finite")
    return value


def normalize_pressure(value: float, unit: str) -> NormalizedValue:
    key = unit.strip().lower()
    if key not in PRESSURE_TO_BAR:
        raise ValueError(f"Unsupported pressure unit: {unit}")
    return NormalizedValue(_finite(value) * PRESSURE_TO_BAR[key], "bar")


def normalize_flow(value: float, unit: str) -> NormalizedValue:
    key = unit.strip().lower()
    if key not in FLOW_TO_LPH:
        raise ValueError(f"Unsupported flow unit: {unit}")
    return NormalizedValue(_finite(value) * FLOW_TO_LPH[key], "L/h")


def normalize_temperature(value: float, unit: str) -> NormalizedValue:
    key = unit.strip().lower()
    value = _finite(value)
    if key in {"c", "°c", "degc", "celsius"}:
        return NormalizedValue(value, "C")
    if key in {"f", "°f", "degf", "fahrenheit"}:
        return NormalizedValue((value - 32.0) * 5.0 / 9.0, "C")
    if key in {"k", "kelvin"}:
        return NormalizedValue(value - 273.15, "C")
    raise ValueError(f"Unsupported temperature unit: {unit}")


def normalize_conductivity(value: float, unit: str) -> NormalizedValue:
    key = unit.strip().lower()
    if key not in CONDUCTIVITY_TO_MSCM:
        raise ValueError(f"Unsupported conductivity unit: {unit}")
    return NormalizedValue(_finite(value) * CONDUCTIVITY_TO_MSCM[key], "mS/cm")
