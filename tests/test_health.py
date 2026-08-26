from membraneiq.engineering import enrich_process_data
from membraneiq.health import assess_health, establish_baseline
from membraneiq.simulator import SimulatorConfig, simulate_membrane_run


def make_assessment(scenario: str):
    df = simulate_membrane_run(scenario, SimulatorConfig(seed=123, total_hours=48, cip_start_hour=32))
    df = enrich_process_data(df)
    baseline = establish_baseline(df)
    return assess_health(df, baseline)


def test_healthy_scores_better_than_incomplete_recovery():
    healthy = make_assessment("healthy")
    degraded = make_assessment("incomplete_cip_recovery")
    assert healthy.health_score > degraded.health_score


def test_incomplete_recovery_detected():
    degraded = make_assessment("incomplete_cip_recovery")
    assert degraded.latest_cip_recovery_pct is not None
    assert degraded.latest_cip_recovery_pct < 95


def test_severe_fouling_not_healthy():
    severe = make_assessment("severe_fouling")
    assert severe.status != "HEALTHY"
