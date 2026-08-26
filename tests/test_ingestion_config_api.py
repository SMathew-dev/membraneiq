import io

import pandas as pd
from fastapi.testclient import TestClient

from membraneiq.api import app
from membraneiq.ingestion import CSVIngestor
from membraneiq.system_config import CommissionedSystem, SystemConfigStore


def test_csv_ingestor_discovers_membrane_signals(tmp_path):
    path = tmp_path / "uf_run.csv"
    pd.DataFrame(
        {
            "UF01_Feed_Pressure_bar": [4.0, 4.1],
            "UF01_Retentate_Pressure_bar": [3.2, 3.3],
            "UF01_Permeate_Pressure_bar": [0.2, 0.2],
            "UF01_Permeate_Flow_LPH": [2400, 2380],
            "UF01_Temperature_degC": [20.0, 20.1],
        }
    ).to_csv(path, index=False)
    preview = CSVIngestor().preview(path)
    assert preview.source_type == "csv"
    assert preview.readiness["ready_for_core_analysis"] is True


def test_api_accepts_csv_upload_for_commissioning():
    csv_bytes = (
        "UF01_Feed_Pressure_bar,UF01_Retentate_Pressure_bar,"
        "UF01_Permeate_Pressure_bar,UF01_Permeate_Flow_LPH,UF01_Temperature_degC\n"
        "4.0,3.2,0.2,2400,20.0\n"
        "4.1,3.3,0.2,2380,20.1\n"
    ).encode()
    response = TestClient(app).post(
        "/v1/commissioning/upload?system_id=UF-CLIENT-01",
        files={"file": ("client_export.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["system_id"] == "UF-CLIENT-01"
    assert payload["source_type"] == "csv"
    assert payload["readiness"]["ready_for_core_analysis"] is True


def test_commissioned_system_round_trip(tmp_path):
    store = SystemConfigStore(tmp_path / "systems.json")
    system = CommissionedSystem(
        system_id="UF-01",
        name="Main UF",
        source_mode="live",
        source_reference="opc.tcp://example:4840",
        mappings={"PIT101": "feed_pressure"},
        topology={"stages_detected": 3, "vessels_detected": 7},
        observability={"resolution": "VESSEL", "score": 80.0},
    )
    store.save(system)
    loaded = store.get("UF-01")
    assert loaded is not None
    assert loaded.name == "Main UF"
    assert loaded.topology["vessels_detected"] == 7


def test_excel_ingestor_when_optional_dependency_available(tmp_path):
    import pytest

    pytest.importorskip("openpyxl")
    from membraneiq.ingestion import ExcelIngestor

    path = tmp_path / "uf_run.xlsx"
    pd.DataFrame({"UF01_Feed_Pressure_bar": [4.0]}).to_excel(path, index=False)
    preview = ExcelIngestor().preview(path)
    assert preview.source_type == "excel"
