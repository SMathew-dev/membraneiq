from fastapi.testclient import TestClient

from membraneiq.api import app


def test_customer_web_app_is_served():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "MembraneIQ" in response.text
    assert "Upload process data" in response.text
    assert "Connect live plant" in response.text

    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200
    assert js.status_code == 200


def test_commissioning_preview_exposes_full_evidence_based_topology():
    client = TestClient(app)
    response = client.post(
        "/v1/commissioning/preview-columns",
        json={
            "system_id": "UF-01",
            "columns": [
                "UF01_Stage1_Vessel1_Feed_Pressure_bar",
                "UF01_Stage1_Vessel1_Permeate_Flow_LPH",
                "UF01_Retentate_Pressure_bar",
                "UF01_Permeate_Pressure_bar",
                "UF01_Temperature_degC",
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topology"]["stages_detected"] == 1
    assert "S1" in data["topology_model"]["stages"]
    assert "V1" in data["topology_model"]["stages"]["S1"]["vessels"]
