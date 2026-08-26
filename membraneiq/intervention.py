from __future__ import annotations

from dataclasses import dataclass, asdict

from membraneiq.economics import EconomicAssessment


@dataclass(frozen=True)
class InterventionAssessment:
    days_to_cip_break_even: float | None
    clean_now_economically_supported: bool
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


def compare_clean_vs_run(economics: EconomicAssessment) -> InterventionAssessment:
    daily_loss = economics.estimated_daily_throughput_value_loss
    cip_cost = economics.estimated_total_cip_cost

    if daily_loss <= 0:
        return InterventionAssessment(
            days_to_cip_break_even=None,
            clean_now_economically_supported=False,
            rationale="No modeled throughput value loss; economics alone do not justify CIP.",
        )

    days = cip_cost / daily_loss if daily_loss else None
    supported = days is not None and days <= 1.0
    rationale = (
        f"Modeled CIP cost equals approximately {days:.2f} days of current throughput value loss."
        if days is not None
        else "Break-even could not be calculated."
    )
    return InterventionAssessment(
        days_to_cip_break_even=None if days is None else round(days, 2),
        clean_now_economically_supported=supported,
        rationale=rationale,
    )
