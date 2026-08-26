from pathlib import Path

from membraneiq.engineering import enrich_process_data
from membraneiq.health import assess_health, establish_baseline
from membraneiq.simulator import SimulatorConfig, simulate_membrane_run


def main() -> None:
    raw = simulate_membrane_run("incomplete_cip_recovery", SimulatorConfig(seed=7))
    data = enrich_process_data(raw)
    baseline = establish_baseline(data)
    assessment = assess_health(data, baseline)

    output_dir = Path("data/generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "demo_run.csv"
    data.to_csv(csv_path, index=False)

    print("MembraneIQ Assessment")
    print("---------------------")
    print(f"Health score: {assessment.health_score:.1f} / 100")
    print(f"Status: {assessment.status}")
    print(f"Normalized permeability loss: {assessment.normalized_permeability_loss_pct:.1f}%")
    print(f"TMP increase: {assessment.tmp_change_pct:.1f}%")
    print(f"Pressure-drop increase: {assessment.pressure_drop_change_pct:.1f}%")
    if assessment.latest_cip_recovery_pct is not None:
        print(f"Latest CIP recovery: {assessment.latest_cip_recovery_pct:.1f}%")
    print(f"Fouling trend: {assessment.fouling_trend_pct_per_hour:.2f}%/h")
    print(f"Diagnosis: {assessment.diagnosis}")
    print(f"Recommendation: {assessment.recommendation}")
    print(f"Generated dataset: {csv_path}")


if __name__ == "__main__":
    main()
