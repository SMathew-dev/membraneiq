from membraneiq.autocommission import discover_signals
from membraneiq.topology_discovery import reconstruct_topology, topology_summary


def test_builds_supported_stage_and_vessel_hierarchy():
    columns = [
        "UF01_Stage1_Vessel1_Feed_Pressure_bar",
        "UF01_Stage1_Vessel1_Permeate_Flow_LPH",
        "UF01_Stage1_Vessel2_Feed_Pressure_bar",
        "UF01_Stage1_Vessel2_Permeate_Flow_LPH",
        "UF01_Stage2_Vessel3_Feed_Pressure_bar",
        "UF01_Stage2_Vessel3_Permeate_Flow_LPH",
        "UF01_Temperature_degC",
    ]
    topology = reconstruct_topology(discover_signals(columns), system_id="UF-01")
    summary = topology_summary(topology)

    assert summary["stages_detected"] == 2
    assert summary["vessels_detected"] == 3
    assert "V1" in topology.stages["S1"].vessels
    assert "V3" in topology.stages["S2"].vessels
    assert topology.requires_confirmation is True


def test_does_not_invent_vessels_without_evidence():
    columns = [
        "UF01_Feed_Pressure_bar",
        "UF01_Retentate_Pressure_bar",
        "UF01_Permeate_Flow_LPH",
        "UF01_Temperature_degC",
    ]
    topology = reconstruct_topology(discover_signals(columns), system_id="UF-01")
    summary = topology_summary(topology)

    assert summary["stages_detected"] == 0
    assert summary["vessels_detected"] == 0


def test_vessel_without_stage_is_not_assigned_arbitrarily():
    topology = reconstruct_topology(
        discover_signals(["UF01_Vessel7_Feed_Pressure_bar"]),
        system_id="UF-01",
    )
    assert len(topology.stages) == 0
    assert "UF01_Vessel7_Feed_Pressure_bar" in topology.unresolved_signals
