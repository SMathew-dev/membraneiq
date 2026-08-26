from __future__ import annotations

from dataclasses import dataclass

from membraneiq.live_sources import LiveTag, ReadOnlyLiveSource


@dataclass(frozen=True)
class OPCUABrowseLimits:
    max_nodes: int = 500
    max_depth: int = 6


class OPCUAReadOnlySource(ReadOnlyLiveSource):
    """Read-only OPC UA adapter for MembraneIQ.

    The adapter supports either explicitly configured node IDs or bounded
    recursive discovery under the OPC UA Objects node. Discovery is deliberately
    limited by node count and depth so commissioning cannot recursively crawl an
    arbitrarily large plant namespace.

    No write/value-setting method is exposed by this class.
    """

    source_type = "opc_ua"

    def __init__(
        self,
        endpoint: str,
        node_ids: dict[str, str] | None = None,
        browse_limits: OPCUABrowseLimits | None = None,
    ):
        super().__init__(endpoint)
        self.node_ids = dict(node_ids or {})
        self.browse_limits = browse_limits or OPCUABrowseLimits()
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

    @staticmethod
    def _browse_name(node) -> str:
        try:
            browse_name = node.read_browse_name()
            return str(getattr(browse_name, "Name", browse_name))
        except Exception:
            return "UnknownNode"

    @staticmethod
    def _node_id(node) -> str:
        node_id = getattr(node, "nodeid", None)
        if node_id is None:
            return str(node)
        to_string = getattr(node_id, "to_string", None)
        return to_string() if callable(to_string) else str(node_id)

    @staticmethod
    def _is_readable_value(node) -> bool:
        try:
            node.read_value()
            return True
        except Exception:
            return False

    def _discover_from_root(self, root) -> dict[str, str]:
        discovered: dict[str, str] = {}
        visited = 0
        stack: list[tuple[object, list[str], int]] = [(root, [], 0)]

        while stack and visited < self.browse_limits.max_nodes:
            node, parent_path, depth = stack.pop()
            visited += 1
            name = self._browse_name(node)
            path = [*parent_path, name] if name else list(parent_path)

            children = []
            if depth < self.browse_limits.max_depth:
                try:
                    children = list(node.get_children())
                except Exception:
                    children = []

            # Only nodes that can be read as values become process tag candidates.
            # Objects/folders may still be traversed but are not presented as tags.
            if depth > 0 and self._is_readable_value(node):
                display_name = "/".join(part for part in path if part)
                if display_name:
                    discovered[display_name] = self._node_id(node)

            if depth < self.browse_limits.max_depth:
                for child in reversed(children):
                    if visited + len(stack) >= self.browse_limits.max_nodes:
                        break
                    stack.append((child, path, depth + 1))

        return discovered

    def discover_node_ids(self) -> dict[str, str]:
        client = self._require_client()
        nodes = getattr(client, "nodes", None)
        root = getattr(nodes, "objects", None)
        if root is None:
            raise RuntimeError("OPC UA client does not expose an Objects node for discovery")
        discovered = self._discover_from_root(root)
        self.node_ids.update(discovered)
        return dict(discovered)

    def browse_tags(self) -> list[LiveTag]:
        self._require_client()
        if not self.node_ids:
            self.discover_node_ids()
        return [LiveTag(name=name) for name in sorted(self.node_ids)]

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
