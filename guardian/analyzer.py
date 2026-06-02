"""Analyze workflow DAG for inefficiencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkflowNode:
    id: str
    type: str  # e.g. "llm", "tool", "if-else", "code"
    title: str = ""
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)


@dataclass
class WorkflowDAG:
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)
    entry_node: Optional[str] = None

    @classmethod
    def from_dict(cls, raw: dict) -> "WorkflowDAG":
        """Build a DAG from Dify's workflow JSON (graph.nodes list)."""
        dag = cls()
        graph = raw.get("graph", raw)
        nodes_list = graph.get("nodes", [])
        edges = graph.get("edges", [])

        node_map: dict[str, WorkflowNode] = {}
        for n in nodes_list:
            node = WorkflowNode(
                id=n["id"],
                type=n.get("data", {}).get("type", n.get("type", "unknown")),
                title=n.get("data", {}).get("title", n.get("title", "")),
                data=n.get("data", {}),
            )
            node_map[node.id] = node

        for edge in edges:
            src = edge.get("sourceId") or edge.get("source")
            tgt = edge.get("targetId") or edge.get("target")
            if src in node_map and tgt in node_map:
                node_map[src].downstream.append(tgt)
                node_map[tgt].upstream.append(src)

        dag.nodes = node_map
        entries = [nid for nid, n in node_map.items() if not n.upstream]
        dag.entry_node = entries[0] if entries else None
        return dag

    def llm_nodes(self) -> list[WorkflowNode]:
        return [n for n in self.nodes.values() if n.type == "llm"]

    def redundant_llm_calls(self) -> list[tuple[WorkflowNode, WorkflowNode]]:
        """Detect LLM nodes that appear to do the same work.

        Heuristic: same model, overlapping prompt templates, and same upstream source.
        """
        llms = self.llm_nodes()
        redundant: list[tuple[WorkflowNode, WorkflowNode]] = []
        for i, a in enumerate(llms):
            for b in llms[i + 1:]:
                if (
                    a.data.get("model", {}).get("provider") == b.data.get("model", {}).get("provider")
                    and a.data.get("model", {}).get("name") == b.data.get("model", {}).get("name")
                    and set(a.upstream) == set(b.upstream)
                ):
                    redundant.append((a, b))
        return redundant

    def dead_branches(self) -> list[list[str]]:
        """Return paths that can never execute.

        Simplified heuristic: branches from if-else nodes that lead only to
        leaf (sink) nodes with no further processing.
        """
        dead: list[list[str]] = []
        for node in self.nodes.values():
            if node.type != "if-else":
                continue
            for child_id in node.downstream:
                path = self._walk_to_end(child_id)
                if not path:
                    continue
                if all(len(self.nodes[nid].downstream) == 0 for nid in path if nid in self.nodes):
                    dead.append([node.id] + path)
        return dead

    def _walk_to_end(self, start_id: str) -> list[str]:
        visited: list[str] = []
        current = start_id
        while current and current not in visited:
            visited.append(current)
            node = self.nodes.get(current)
            if not node or not node.downstream:
                break
            current = node.downstream[0]
        return visited
