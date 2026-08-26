from fastapi.testclient import TestClient

from membraneiq.api import app
from membraneiq.observability import assess_observability


def test_observability_refuses_vessel_claim_without_vessel_evidence():
    result = assess_observability(
        {"feed_pressure", "retentate_pressure", "permeate_pressure", "permeate_flow", "temperature"},
        stages_detected=2,
        vessels_detected=0,
    )
    assert result.resolution == "STAGE"
    assert "vessel_localization" in result.unsupported_capabilities


def test_api_health_and_observability():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post(
        "/v1/observability",
        json={
            "mapped_signals": [
                "feed_pressure",
                "retentate_pressure",
                "permeate_pressure",
                "permeate_flow",
                "temperature",
                "permeate_conductivity",
                "cip_state",
            ],
            "stages_detected": 3,
            "vessels_detected": 7,
        },
    )
    assert response.status_code == 200
    assert response.json()["resolution"] == "VESSEL"
