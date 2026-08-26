from membraneiq.history_store import HealthRecordStore
from membraneiq.records import HealthSnapshot, MaintenanceEvent, MembraneHealthRecord


def test_record_round_trip(tmp_path):
    store = HealthRecordStore(tmp_path / "records.json")
    record = MembraneHealthRecord(
        asset_id="V3B",
        asset_type="vessel",
        system_id="UF-01",
        stage_id="S3",
        vessel_id="V3B",
        operating_hours=120.0,
    )
    record.add_snapshot(
        HealthSnapshot(
            timestamp="2026-08-26T12:00:00Z",
            health_score=61.0,
            status="DEGRADED",
            normalized_permeability_loss_pct=18.0,
            tmp_change_pct=12.0,
            pressure_drop_change_pct=20.0,
            latest_cip_recovery_pct=86.0,
            diagnosis="Developing fouling trend",
        )
    )
    record.add_maintenance_event(
        MaintenanceEvent(
            timestamp="2026-08-26T11:00:00Z",
            event_type="CIP",
            recovery_pct=86.0,
        )
    )

    store.upsert(record)
    loaded = store.load()["V3B"]

    assert loaded.current_health_score == 61.0
    assert loaded.current_status == "DEGRADED"
    assert loaded.cip_count == 1
    assert loaded.latest_cip_recovery_pct == 86.0
