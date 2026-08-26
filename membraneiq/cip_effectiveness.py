from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CIPAssessment:
    pre_cip_value: float
    post_cip_value: float
    clean_baseline_value: float
    recovery_pct: float
    residual_loss_pct: float
    effectiveness: str

    def to_dict(self) -> dict:
        return asdict(self)


def assess_cip_recovery(
    pre_cip_value: float,
    post_cip_value: float,
    clean_baseline_value: float,
    higher_is_better: bool = True,
) -> CIPAssessment:
    """Quantify how much lost performance a CIP restored.

    For permeability/flux, higher_is_better=True. For resistance or pressure
    drop, set False. Recovery is capped for reporting but raw values are retained.
    """
    pre = float(pre_cip_value)
    post = float(post_cip_value)
    baseline = float(clean_baseline_value)

    if higher_is_better:
        loss_before = baseline - pre
        remaining_loss = baseline - post
        restored = post - pre
    else:
        loss_before = pre - baseline
        remaining_loss = post - baseline
        restored = pre - post

    if loss_before <= 1e-12:
        recovery = 100.0 if remaining_loss <= 1e-12 else 0.0
    else:
        recovery = 100.0 * restored / loss_before

    residual_pct = 0.0 if abs(baseline) <= 1e-12 else 100.0 * max(0.0, remaining_loss) / abs(baseline)
    recovery_display = max(0.0, min(120.0, recovery))

    if recovery_display >= 90 and residual_pct <= 5:
        effectiveness = "STRONG"
    elif recovery_display >= 70:
        effectiveness = "PARTIAL"
    else:
        effectiveness = "WEAK"

    return CIPAssessment(
        pre_cip_value=pre,
        post_cip_value=post,
        clean_baseline_value=baseline,
        recovery_pct=round(recovery_display, 1),
        residual_loss_pct=round(residual_pct, 1),
        effectiveness=effectiveness,
    )
