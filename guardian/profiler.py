"""Per-node profiling: tokens, latency, cost, and historical trends."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class NodeSample:
    """A single profiling observation for a node execution."""

    node_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    node_title: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NodeProfile:
    """Aggregate stats for a single workflow node across runs."""

    node_id: str
    node_title: str = ""
    samples: list[NodeSample] = field(default_factory=list, repr=False)

    def record(self, sample: NodeSample) -> None:
        self.samples.append(sample)
        if sample.node_title and not self.node_title:
            self.node_title = sample.node_title

    @property
    def run_count(self) -> int:
        return len(self.samples)

    @property
    def avg_input_tokens(self) -> float:
        return statistics.mean(s.input_tokens for s in self.samples) if self.samples else 0.0

    @property
    def avg_output_tokens(self) -> float:
        return statistics.mean(s.output_tokens for s in self.samples) if self.samples else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return statistics.mean(s.latency_ms for s in self.samples) if self.samples else 0.0

    @property
    def avg_cost(self) -> float:
        return statistics.mean(s.cost_usd for s in self.samples) if self.samples else 0.0

    @property
    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.samples)

    @property
    def total_tokens(self) -> int:
        return sum(s.input_tokens + s.output_tokens for s in self.samples)

    @property
    def input_output_ratio(self) -> float:
        avg_out = self.avg_output_tokens
        return self.avg_input_tokens / avg_out if avg_out > 0 else float("inf")

    def cost_trend(self, last_n: int = 10) -> list[float]:
        return [s.cost_usd for s in self.samples[-last_n:]]

    def latency_trend(self, last_n: int = 10) -> list[float]:
        return [s.latency_ms for s in self.samples[-last_n:]]

    def is_degrading(self, window: int = 5) -> bool:
        """Return *True* if latency is trending upward over the last *window* runs."""
        if len(self.samples) < window * 2:
            return False
        recent = [s.latency_ms for s in self.samples[-window:]]
        earlier = [s.latency_ms for s in self.samples[-window * 2:-window]]
        return statistics.mean(recent) > statistics.mean(earlier) * 1.2


class Profiler:
    """Collects and queries per-node profiles."""

    def __init__(self) -> None:
        self._profiles: dict[str, NodeProfile] = {}

    def record(self, sample: NodeSample) -> None:
        profile = self._profiles.get(sample.node_id)
        if profile is None:
            profile = NodeProfile(node_id=sample.node_id, node_title=sample.node_title)
            self._profiles[sample.node_id] = profile
        profile.record(sample)

    def get(self, node_id: str) -> Optional[NodeProfile]:
        return self._profiles.get(node_id)

    def all_profiles(self) -> list[NodeProfile]:
        return list(self._profiles.values())

    def top_by_cost(self, n: int = 5) -> list[NodeProfile]:
        return sorted(self._profiles.values(), key=lambda p: p.total_cost, reverse=True)[:n]

    def top_by_tokens(self, n: int = 5) -> list[NodeProfile]:
        return sorted(self._profiles.values(), key=lambda p: p.total_tokens, reverse=True)[:n]
