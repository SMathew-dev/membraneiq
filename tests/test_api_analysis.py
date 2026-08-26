from fastapi.testclient import TestClient

from membraneiq.api import app


client = TestClient(app)


def test_live_demo_commissions_without_plant_credentials():
    response = client.get("/v1/commissioning/live-demo?system_id=UF-01")
    assert response.status_code == 200
    body = response.json()
    assert body["system_id"] == "UF-01"
    assert body["readiness"]["ready_for_core_analysis"] is True
    assert body["topology"]["stages_detected"] >= 2


def test_analysis_endpoint_returns_explainable_decision():
    response = client.post(
        "/v1/analysis",
        json={
            "system_id": "UF-01",
            "asset_id": "V3",
            "current_metrics": {
                "normalized_permeability": 82.0,
                "pressure_drop": 1.25
            },
            "baseline_metrics": {
                "normalized_permeability": {"median": 100.0, "mad": 0.4, "samples": 40},
                "pressure_drop": {"median": 1.0, "mad": 0.02, "samples": 40}
            },
            "baseline_sample_count": 40,
            "trends": [
                {
                    "metric": "normalized_permeability",
                    "slope_per_day": -0.8,
                    "change_pct_per_30d": -24.0,
                    "r_squared": 0.95,
                    "direction": "DEGRADING",
                    "samples": 10
                }
            ],
            "pre_cip_value": 80.0,
            "post_cip_value": 89.0,
            "cip_baseline_value": 100.0,
            "healthy_permeate_flow_lph": 2500.0,
            "current_permeate_flow_lph": 2100.0,
            "plant_economics": {
                "product_value_per_liter": 0.08,
                "production_hours_per_day": 20.0,
                "cip_chemical_cost": 120.0,
                "cip_downtime_hours": 1.5
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["asset_id"] == "V3"
    assert body["decision"]["action"] in {"CLEAN", "INSPECT"}
    assert body["cip"] is not None
    assert body["economics"] is not None
