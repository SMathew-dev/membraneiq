from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperatingState(str, Enum):
    OFFLINE = "OFFLINE"
    STARTUP = "STARTUP"
    PRODUCTION = "PRODUCTION"
    CIP = "CIP"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class StateAssessment:
    state: OperatingState
    confidence: float
    reason: str


def detect_state(
    permeate_flow_lph: float | None,
    feed_pressure_bar: float | None,
    cip_state: bool | int | None = None,
    pump_running: bool | None = None,
    production_flow_threshold_lph: float = 100.0,
    pressure_threshold_bar: float = 0.3,
) -> StateAssessment:
    """Conservative rule-based state classifier for commissioning/v0.2.

    Health baselines should only learn from stable production, never CIP/offline
    periods. Later versions can learn plant-specific state models.
    """
    if cip_state is True or cip_state == 1:
        return StateAssessment(OperatingState.CIP, 0.99, "CIP state signal active")

    flow = None if permeate_flow_lph is None else float(permeate_flow_lph)
    pressure = None if feed_pressure_bar is None else float(feed_pressure_bar)

    if pump_running is False and (flow is None or flow < production_flow_threshold_lph):
        return StateAssessment(OperatingState.OFFLINE, 0.95, "Pump stopped and no production flow")

    if flow is not None and pressure is not None:
        if flow >= production_flow_threshold_lph and pressure >= pressure_threshold_bar:
            return StateAssessment(OperatingState.PRODUCTION, 0.95, "Flow and pressure indicate production")
        if pressure >= pressure_threshold_bar and flow < production_flow_threshold_lph:
            return StateAssessment(OperatingState.STARTUP, 0.75, "Pressure present before stable permeate flow")
        if flow < production_flow_threshold_lph and pressure < pressure_threshold_bar:
            return StateAssessment(OperatingState.OFFLINE, 0.9, "Low flow and low pressure")

    return StateAssessment(OperatingState.UNKNOWN, 0.35, "Insufficient signals for reliable state classification")
