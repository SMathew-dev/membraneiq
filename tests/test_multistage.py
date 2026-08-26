from membraneiq.multistage import (
    condition_status,
    latest_vessel_health,
    simulate_multistage_run,
    stage_health_summary,
)


def test_known_bad_vessel_ranks_worst():
    df = simulate_multistage_run(seed=7)
    latest = latest_vessel_health(df)
    assert latest.iloc[0]["vessel_id"] == "V3B"


def test_stage_three_is_worst_stage():
    df = simulate_multistage_run(seed=7)
    stages = stage_health_summary(df)
    assert stages.iloc[0]["stage_id"] == "S3"


def test_condition_status_thresholds():
    assert condition_status(90) == "HEALTHY"
    assert condition_status(75) == "WATCH"
    assert condition_status(55) == "DEGRADED"
    assert condition_status(30) == "CRITICAL"
