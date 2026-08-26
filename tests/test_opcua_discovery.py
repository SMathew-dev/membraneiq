from membraneiq.opcua_source import OPCUABrowseLimits, OPCUAReadOnlySource


class FakeBrowseName:
    def __init__(self, name):
        self.Name = name


class FakeNodeId:
    def __init__(self, value):
        self.value = value

    def to_string(self):
        return self.value


class FakeNode:
    def __init__(self, name, node_id, value=None, children=None, readable=False):
        self.name = name
        self.nodeid = FakeNodeId(node_id)
        self.value = value
        self.children = children or []
        self.readable = readable

    def read_browse_name(self):
        return FakeBrowseName(self.name)

    def get_children(self):
        return self.children

    def read_value(self):
        if not self.readable:
            raise RuntimeError("Object node")
        return self.value


def test_recursive_discovery_returns_readable_process_nodes_only():
    pressure = FakeNode("Feed_Pressure_bar", "ns=2;s=UF.P1", 4.2, readable=True)
    flow = FakeNode("Permeate_Flow_LPH", "ns=2;s=UF.F1", 2100, readable=True)
    vessel = FakeNode("Vessel1", "ns=2;s=UF.V1", children=[pressure, flow])
    stage = FakeNode("Stage1", "ns=2;s=UF.S1", children=[vessel])
    root = FakeNode("Objects", "i=85", children=[stage])

    source = OPCUAReadOnlySource("opc.tcp://example:4840")
    discovered = source._discover_from_root(root)

    assert "Objects/Stage1/Vessel1/Feed_Pressure_bar" in discovered
    assert "Objects/Stage1/Vessel1/Permeate_Flow_LPH" in discovered
    assert "Objects/Stage1" not in discovered
    assert discovered["Objects/Stage1/Vessel1/Feed_Pressure_bar"] == "ns=2;s=UF.P1"


def test_recursive_discovery_respects_depth_limit():
    deep = FakeNode("TooDeep", "ns=2;s=deep", 10, readable=True)
    level2 = FakeNode("Level2", "ns=2;s=l2", children=[deep])
    level1 = FakeNode("Level1", "ns=2;s=l1", children=[level2])
    root = FakeNode("Objects", "i=85", children=[level1])

    source = OPCUAReadOnlySource(
        "opc.tcp://example:4840",
        browse_limits=OPCUABrowseLimits(max_nodes=50, max_depth=2),
    )
    discovered = source._discover_from_root(root)
    assert "Objects/Level1/Level2/TooDeep" not in discovered
