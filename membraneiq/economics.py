from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PlantEconomics:
    product_value_per_liter: float = 0.0
    production_hours_per_day: float = 20.0
    cip_water_m3: float = 0.0
    water_cost_per_m3: float = 0.0
    cip_chemical_cost: float = 0.0
    cip_energy_cost: float = 0.0
    cip_labor_cost: float = 0.0
    cip_downtime_hours: float = 0.0
    membrane_replacement_cost: float = 0.0


@dataclass(frozen=True)
class EconomicAssessment:
    estimated_daily_throughput_value_loss: float
    estimated_cip_direct_cost: float
    estimated_cip_downtime_value: float
    estimated_total_cip_cost: float
    membrane_replacement_cost: float
    assumptions: dict

    def to_dict(self) -> dict:
        return asdict(self)


def assess_economics(
    healthy_permeate_flow_lph: float,
    current_permeate_flow_lph: float,
    economics: PlantEconomics,
) -> EconomicAssessment:
    """Transparent scenario economics, not an accounting claim.

    All plant-specific values are explicit inputs so MembraneIQ never invents
    customer costs or savings.
    """
    healthy = max(0.0, float(healthy_permeate_flow_lph))
    current = max(0.0, float(current_permeate_flow_lph))
    lost_lph = max(0.0, healthy - current)

    daily_loss = (
        lost_lph
        * max(0.0, economics.production_hours_per_day)
        * max(0.0, economics.product_value_per_liter)
    )
    direct_cip = (
        max(0.0, economics.cip_water_m3) * max(0.0, economics.water_cost_per_m3)
        + max(0.0, economics.cip_chemical_cost)
        + max(0.0, economics.cip_energy_cost)
        + max(0.0, economics.cip_labor_cost)
    )
    downtime_value = (
        healthy
        * max(0.0, economics.cip_downtime_hours)
        * max(0.0, economics.product_value_per_liter)
    )

    return EconomicAssessment(
        estimated_daily_throughput_value_loss=round(daily_loss, 2),
        estimated_cip_direct_cost=round(direct_cip, 2),
        estimated_cip_downtime_value=round(downtime_value, 2),
        estimated_total_cip_cost=round(direct_cip + downtime_value, 2),
        membrane_replacement_cost=round(max(0.0, economics.membrane_replacement_cost), 2),
        assumptions=asdict(economics),
    )
