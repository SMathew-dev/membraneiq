from membraneiq.live_sources import SimulatedPlantSource


def test_simulated_live_source_commissions_through_common_pipeline():
    source = SimulatedPlantSource()
    source.connect()
    preview = source.commissioning_preview(system_id="UF-01")

    assert preview.source_type == "simulated_plc"
    assert preview.readiness["ready_for_core_analysis"] is True
    assert "S1" in preview.topology.stages
    assert "V1" in preview.topology.stages["S1"].vessels
    assert any(
        proposal.source_name == "UF01_Stage1_Vessel1_Feed_Pressure"
        and proposal.detected_unit == "bar"
        for proposal in preview.proposals
    )

    values = source.read_tags([
        "UF01_Stage1_Vessel1_Feed_Pressure",
        "UF01_Temperature",
    ])
    assert all(tag.quality == "GOOD" for tag in values)
    assert values[0].value == 4.2
    source.disconnect()


def test_unknown_live_tag_returns_bad_quality_not_fake_value():
    source = SimulatedPlantSource()
    source.connect()
    result = source.read_tags(["DOES_NOT_EXIST"])[0]
    assert result.quality == "BAD"
    assert result.value is None
