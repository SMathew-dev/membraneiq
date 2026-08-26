from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable


SIGNAL_PATTERNS = {
    "feed_pressure": [r"feed.*press", r"inlet.*press", r"pit", r"pressure.*feed"],
    "retentate_pressure": [r"ret.*press", r"concentrate.*press", r"outlet.*press"],
    "permeate_pressure": [r"perm.*press"],
    "feed_flow": [r"feed.*flow", r"inlet.*flow", r"fit"],
    "permeate_flow": [r"perm.*flow", r"filtrate.*flow"],
    "temperature": [r"temp", r"temperature", r"tt\d*"],
    "feed_conductivity": [r"feed.*cond", r"inlet.*cond"],
    "permeate_conductivity": [r"perm.*cond", r"filtrate.*cond"],
    "cip_state": [r"cip", r"clean.*state", r"cleaning"],
}

UNIT_HINTS = {
    "bar": "bar",
    "psi": "psi",
    "kpa": "kPa",
    "lph": "L/h",
    "l/h": "L/h",
    "gpm": "gpm",
    "degc": "C",
    "°c": "C",
    "celsius": "C",
    "ms/cm": "mS/cm",
    "us/cm": "uS/cm",
}

REQUIRED_FOR_CORE = {
    "feed_pressure",
    "retentate_pressure",
    "permeate_pressure",
    "permeate_flow",
    "temperature",
}


@dataclass
class SignalProposal:
    source_name: str
    canonical_signal: str | None
    confidence: float
    detected_unit: str | None = None
    stage_hint: str | None = None
    vessel_hint: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9°/]+", " ", text.lower()).strip()


def _extract_topology_hints(name: str) -> tuple[str | None, str | None]:
    lower = name.lower()
    stage = None
    vessel = None
    stage_match = re.search(r"(?:stage|stg|s)[ _-]?(\d+)", lower)
    vessel_match = re.search(r"(?:vessel|vsl|v)[ _-]?(\d+[a-z]?)", lower)
    if stage_match:
        stage = f"S{stage_match.group(1)}"
    if vessel_match:
        vessel = f"V{vessel_match.group(1).upper()}"
    return stage, vessel


def _detect_unit(name: str) -> str | None:
    lower = name.lower()
    for token, canonical in UNIT_HINTS.items():
        if token in lower:
            return canonical
    return None


def propose_signal_mapping(source_name: str) -> SignalProposal:
    normalized = _normalize(source_name)
    candidates: list[tuple[str, float]] = []
    for signal, patterns in SIGNAL_PATTERNS.items():
        matches = sum(bool(re.search(pattern, normalized)) for pattern in patterns)
        if matches:
            confidence = min(0.98, 0.58 + 0.18 * matches)
            # More explicit names deserve higher confidence than generic ISA tags.
            if any(word in normalized for word in signal.split("_")):
                confidence = min(0.99, confidence + 0.12)
            candidates.append((signal, confidence))

    canonical, confidence = (None, 0.0)
    if candidates:
        canonical, confidence = max(candidates, key=lambda item: item[1])

    stage, vessel = _extract_topology_hints(source_name)
    return SignalProposal(
        source_name=source_name,
        canonical_signal=canonical,
        confidence=round(confidence, 2),
        detected_unit=_detect_unit(source_name),
        stage_hint=stage,
        vessel_hint=vessel,
    )


def discover_signals(source_names: Iterable[str]) -> list[SignalProposal]:
    return [propose_signal_mapping(name) for name in source_names]


def data_readiness(proposals: list[SignalProposal], confidence_floor: float = 0.65) -> dict:
    mapped = {
        p.canonical_signal
        for p in proposals
        if p.canonical_signal and p.confidence >= confidence_floor
    }
    missing = sorted(REQUIRED_FOR_CORE - mapped)
    coverage = 100.0 * (len(REQUIRED_FOR_CORE) - len(missing)) / len(REQUIRED_FOR_CORE)

    vessel_specific = any(p.vessel_hint for p in proposals if p.confidence >= confidence_floor)
    stage_specific = any(p.stage_hint for p in proposals if p.confidence >= confidence_floor)
    if vessel_specific:
        resolution = "VESSEL_CANDIDATE"
    elif stage_specific:
        resolution = "STAGE_CANDIDATE"
    else:
        resolution = "SKID"

    return {
        "core_coverage_pct": round(coverage, 1),
        "missing_core_signals": missing,
        "diagnostic_resolution_candidate": resolution,
        "ready_for_core_analysis": not missing,
        "requires_human_confirmation": any(
            p.canonical_signal is None or p.confidence < 0.85 for p in proposals
        ),
    }
