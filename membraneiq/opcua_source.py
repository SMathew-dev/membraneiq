from __future__ import annotations

from membraneiq.live_sources import LiveTag, ReadOnlyLiveSource


class OPCUAReadOnlySource(ReadOnlyLiveSource):
    """Read-only OPC UA adapter for MembraneIQ.

    Requires the optional `asyncua` package. The adapter intentionally exposes
    browse/read behavior only; MembraneIQ does not write control values to PLCs.

    This first adapter accepts configured node IDs. Automatic server-wide browse
    can be layered on later because OPC UA namespaces vary significantly across
    plants and vendors.
    """

    source_type = "opc_ua"

    def __init__(self, endpoint: str, node_ids: dict[str, str]):
        super().__init__(endpoint)
        self.node_ids = node_ids
        self._client = None

    def connect(self) -> None:
        try:
            from asyncua.sync import Client
        except ImportError as exc:
            raise RuntimeError(
                "OPC UA support requires the optional 'asyncua' dependency"
            ) from exc
        self._client = Client(self.endpoint)
        self._client.connect()

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.disconnect()
            self._client = None

    def _require_client(self):
        if self._client is None:
            raise RuntimeError("OPC UA source is not connected")
        return self._client

    def browse_tags(self) -> list[LiveTag]:
        # For v0.2, configured nodes are the safe commissioning boundary.
        # Server-wide recursive discovery comes next.
        self._require_client()
        return [LiveTag(name=name) for name in self.node_ids]

    def read_tags(self, names: list[str]) -> list[LiveTag]:
        client = self._require_client()
        result: list[LiveTag] = []
        for name in names:
            node_id = self.node_ids.get(name)
            if node_id is None:
                result.append(LiveTag(name=name, quality="BAD"))
                continue
            try:
                node = client.get_node(node_id)
                value = node.read_value()
                result.append(LiveTag(name=name, value=value, quality="GOOD"))
            except Exception:
                result.append(LiveTag(name=name, quality="BAD"))
        return result
