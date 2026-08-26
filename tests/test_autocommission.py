from membraneiq.autocommission import data_readiness, discover_signals, propose_signal_mapping


def test_explicit_signal_mapping():
    proposal = propose_signal_mapping("UF01_Stage2_Vessel3_Feed_Pressure_bar")
    assert proposal.canonical_signal == "feed_pressure"
    assert proposal.stage_hint == "S2"
    assert proposal.vessel_hint == "V3"
    assert proposal.detected_unit == "bar"
    assert proposal.confidence >= 0.85


def test_readiness_with_core_signals():
    columns = [
        "UF01_Feed_Pressure_bar",
        "UF01_Retentate_Pressure_bar",
        "UF01_Permeate_Pressure_bar",
        "UF01_Permeate_Flow_LPH",
        "UF01_Temperature_degC",
        "UF01_Permeate_Conductivity_mS/cm",
    ]
    readiness = data_readiness(discover_signals(columns))
    assert readiness["ready_for_core_analysis"] is True
    assert readiness["core_coverage_pct"] == 100.0


def test_missing_signals_are_reported_not_invented():
    readiness = data_readiness(discover_signals(["UF01_Feed_Pressure_bar", "Timestamp"]))
    assert readiness["ready_for_core_analysis"] is False
    assert "permeate_flow" in readiness["missing_core_signals"]
