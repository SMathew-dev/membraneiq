from __future__ import annotations

from pydantic import BaseModel, Field


class BaselineMetricInput(BaseModel):
    median: float
    mad: float
    samples: int = Field(ge=1)


class TrendInput(BaseModel):
    metric: str
    slope_per_day: float
    change_pct_per_30d: float | None = None
    r_squared: float = Field(ge=0.0, le=1.0)
    direction: str
    samples: int = Field(ge=1)


class PlantEconomicsInput(BaseModel):
    product_value_per_liter: float = 0.0
    production_hours_per_day: float = 20.0
    cip_water_m3: float = 0.0
    water_cost_per_m3: float = 0.0
    cip_chemical_cost: float = 0.0
    cip_energy_cost: float = 0.0
    cip_labor_cost: float = 0.0
    cip_downtime_hours: float = 0.0
    membrane_replacement_cost: float = 0.0


class AnalysisRequest(BaseModel):
    system_id: str
    asset_id: str
    current_metrics: dict[str, float]
    baseline_metrics: dict[str, BaselineMetricInput]
    baseline_sample_count: int = Field(default=20, ge=1)
    trends: list[TrendInput] = Field(default_factory=list)
    pre_cip_value: float | None = None
    post_cip_value: float | None = None
    cip_baseline_value: float | None = None
    cip_higher_is_better: bool = True
    healthy_permeate_flow_lph: float | None = None
    current_permeate_flow_lph: float | None = None
    plant_economics: PlantEconomicsInput | None = None
