from __future__ import annotations

from pathlib import Path
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from membraneiq.autocommission import data_readiness, discover_signals
from membraneiq.ingestion import preview_historical_file
from membraneiq.observability import assess_observability
from membraneiq.system_config import CommissionedSystem, SystemConfigStore
from membraneiq.topology_discovery import reconstruct_topology, topology_summary


app = FastAPI(
    title="MembraneIQ API",
    version="0.2.0",
    description="Vendor-neutral membrane commissioning and condition intelligence API",
)

SYSTEM_STORE = SystemConfigStore(Path("data/config/systems.json"))
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class ObservabilityRequest(BaseModel):
    mapped_signals: list[str] = Field(default_factory=list)
    stages_detected: int = 0
    vessels_detected: int = 0


class ColumnCommissioningRequest(BaseModel):
    system_id: str = "MEMBRANE-01"
    columns: list[str] = Field(default_factory=list)


class SaveSystemRequest(BaseModel):
    system_id: str
    name: str
    source_mode: str
    source_reference: str = ""
    mappings: dict[str, str]
    topology: dict
    observability: dict
    metadata: dict = Field(default_factory=dict)


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


@app.post("/v1/commissioning/preview-columns")
def preview_columns(request: ColumnCommissioningRequest) -> dict:
    proposals = discover_signals(request.columns)
    topology = reconstruct_topology(proposals, system_id=request.system_id)
    mapped = {
        proposal.canonical_signal
        for proposal in proposals
        if proposal.canonical_signal and proposal.confidence >= 0.65
    }
    topology_info = topology_summary(topology)
    observability_info = assess_observability(
        mapped,
        stages_detected=topology_info["stages_detected"],
        vessels_detected=topology_info["vessels_detected"],
    )
    return {
        "system_id": request.system_id,
        "readiness": data_readiness(proposals),
        "topology": topology_info,
        "observability": observability_info.to_dict(),
        "proposals": [proposal.to_dict() for proposal in proposals],
    }


@app.post("/v1/commissioning/upload")
async def commissioning_upload(
    file: UploadFile = File(...),
    system_id: str = "MEMBRANE-01",
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm"}:
        raise HTTPException(status_code=415, detail="Supported uploads: CSV, XLSX, XLSM")

    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds 25 MB commissioning limit")
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(raw)
            temp_path = Path(handle.name)
        preview = preview_historical_file(temp_path)
        topology = reconstruct_topology(preview.proposals, system_id=system_id)
        topology_info = topology_summary(topology)
        mapped = {
            proposal.canonical_signal
            for proposal in preview.proposals
            if proposal.canonical_signal and proposal.confidence >= 0.65
        }
        return {
            "system_id": system_id,
            "filename": file.filename,
            "source_type": preview.source_type,
            "rows": preview.rows,
            "columns": preview.columns,
            "readiness": preview.readiness,
            "topology": topology_info,
            "observability": assess_observability(
                mapped,
                stages_detected=topology_info["stages_detected"],
                vessels_detected=topology_info["vessels_detected"],
            ).to_dict(),
            "proposals": [proposal.to_dict() for proposal in preview.proposals],
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


@app.post("/v1/systems")
def save_system(request: SaveSystemRequest) -> dict:
    system = CommissionedSystem(**request.model_dump())
    SYSTEM_STORE.save(system)
    return system.to_dict()


@app.get("/v1/systems")
def list_systems() -> list[dict]:
    return [system.to_dict() for system in SYSTEM_STORE.list()]


@app.get("/v1/systems/{system_id}")
def get_system(system_id: str) -> dict:
    system = SYSTEM_STORE.get(system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Membrane system not found")
    return system.to_dict()


@app.delete("/v1/systems/{system_id}")
def delete_system(system_id: str) -> dict:
    if not SYSTEM_STORE.delete(system_id):
        raise HTTPException(status_code=404, detail="Membrane system not found")
    return {"deleted": True, "system_id": system_id}
