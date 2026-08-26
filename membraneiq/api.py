from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from membraneiq.observability import assess_observability


app = FastAPI(
    title="MembraneIQ API",
    version="0.2.0",
    description="Vendor-neutral membrane commissioning and condition intelligence API",
)


class ObservabilityRequest(BaseModel):
    mapped_signals: list[str] = Field(default_factory=list)
    stages_detected: int = 0
    vessels_detected: int = 0


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "membraneiq", "version": "0.2.0"}


@app.post("/v1/observability")
def observability(request: ObservabilityRequest) -> dict:
    return assess_observability(
        set(request.mapped_signals),
        stages_detected=request.stages_detected,
        vessels_detected=request.vessels_detected,
    ).to_dict()
