import pandas as pd

from membraneiq.commissioning import commission_live
from membraneiq.data_quality import assess_dataframe
from membraneiq.live_sources import SimulatedPlantSource


def test_live_commissioning_produces_actionable_report():
    source = SimulatedPlantSource()
    source.connect()
    report = commission_live(source, system_id="UF-01")
    source.disconnect()

    assert report.source_mode == "live"
    assert report.can_start_analysis is True
    assert report.topology["stages_detected"] >= 2
    assert len(report.auto_accepted_mappings) > 0


def test_data_quality_flags_missing_and_stuck_signals():
    df = pd.DataFrame(
        {
            "feed_pressure": [4.2, 4.2, 4.2, 4.2, 4.2],
            "permeate_flow": [2000, None, None, 1800, None],
            "temperature": [20.0, 20.2, 20.1, 20.3, 20.2],
        }
    )
    report = assess_dataframe(df)

    assert report.score < 100
    assert any("constant/stuck" in warning for warning in report.warnings)
    assert any("missing" in warning for warning in report.warnings)
