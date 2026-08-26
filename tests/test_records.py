from membraneiq.records import HealthSnapshot, MaintenanceEvent, MembraneHealthRecord
from membraneiq.topology import rank_assets_for_attention, summarize_stage, summarize_vessel


def snapshot(score: float, status: str = "HEALTHY") -> HealthSnapshot:
    return HealthSnapshot(
        timestamp="2026-01-01T00:00:00Z",
        health_score=score,
        status=status,
        normalized_permeability_loss_pct=0.0,
        tmp_change_pct=0.0,
        pressure_drop_change_pct=0.0,
        latest_cip_recovery_pct=None,
        diagnosis="test",
    )


def test_health_record_tracks_cip_and_current_health():
    record = MembraneHealthRecord(
        asset_id="E-101",
        asset_type="element",
        system_id="UF-01",
        stage_id="S1",
        vessel_id="V1",
        operating_hours=500.0,
    )
    record.add_snapshot(snapshot(96.0))
    record.add_snapshot(snapshot(82.0, "WATCH"))
    record.add_maintenance_event(
        MaintenanceEvent(
            timestamp="2026-01-02T00:00:00Z",
            event_type="CIP",
            recovery_pct=91.0,
        )
    )

    assert record.current_health_score == 82.0
    assert record.current_status == "WATCH"
    assert record.cip_count == 1
    assert record.latest_cip_recovery_pct == 91.0
    assert record.degradation_rate_points_per_100h() == 2.8


def test_vessel_and_stage_summary_identify_degraded_location():
    a = MembraneHealthRecord("E1", "element", "UF-01", "S1", "V1")
    b = MembraneHealthRecord("E2", "element", "UF-01", "S1", "V1")
    c = MembraneHealthRecord("E3", "element", "UF-01", "S1", "V2")
    a.add_snapshot(snapshot(50.0, "DEGRADED"))
    b.add_snapshot(snapshot(60.0, "DEGRADED"))
    c.add_snapshot(snapshot(94.0))

    records = [a, b, c]
    vessel = summarize_vessel("V1", "S1", records)
    stage = summarize_stage("S1", records)

    assert vessel.health_score == 55.0
    assert vessel.status == "DEGRADED"
    assert stage.vessel_count == 2
    assert "V1" in stage.degraded_vessels


def test_attention_ranking_puts_worst_asset_first():
    good = MembraneHealthRecord("GOOD", "element", "UF-01")
    bad = MembraneHealthRecord("BAD", "element", "UF-01")
    unknown = MembraneHealthRecord("UNKNOWN", "element", "UF-01")
    good.add_snapshot(snapshot(95.0))
    bad.add_snapshot(snapshot(42.0, "CRITICAL"))

    ranked = rank_assets_for_attention([good, unknown, bad])
    assert [record.asset_id for record in ranked] == ["BAD", "GOOD", "UNKNOWN"]
