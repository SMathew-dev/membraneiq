from __future__ import annotations

from membraneiq.multistage import skid_condition_report, simulate_multistage_run


def main() -> None:
    df = simulate_multistage_run(seed=7)
    report = skid_condition_report(df)

    print("MembraneIQ Multi-Stage UF Condition")
    print("----------------------------------")
    for row in report["stages"].itertuples(index=False):
        print(
            f"{row.stage_id}: {row.health_score:.1f}/100 "
            f"[{row.status}] | worst vessel {row.worst_vessel_health:.1f}/100"
        )

    print("\nVessel ranking (lowest health first)")
    for row in report["vessels"].itertuples(index=False):
        print(
            f"{row.vessel_id} ({row.stage_id}): "
            f"{row.health_score:.1f}/100 [{row.status}]"
        )

    print(
        f"\nPriority asset: {report['worst_asset']} in {report['worst_stage']} "
        f"({report['worst_health']:.1f}/100, {report['worst_status']})"
    )


if __name__ == "__main__":
    main()
