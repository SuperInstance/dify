"""Waste detection: find nodes that burn tokens without proportional value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .profiler import NodeProfile, Profiler


@dataclass
class WasteFinding:
    node_id: str
    node_title: str
    category: str  # "overprompted", "idle", "expensive_model", "redundant"
    severity: str  # "low", "medium", "high"
    message: str
    suggestion: str


DEFAULT_MAX_IO_RATIO = 15.0
DEFAULT_IDLE_THRESHOLD = 0.1
DEFAULT_EXPENSIVE_MODEL_RATIO = 0.6


class WasteDetector:
    """Analyze profiler data to surface actionable waste findings."""

    def __init__(
        self,
        profiler: Profiler,
        *,
        max_io_ratio: float = DEFAULT_MAX_IO_RATIO,
        idle_threshold: float = DEFAULT_IDLE_THRESHOLD,
    ) -> None:
        self.profiler = profiler
        self.max_io_ratio = max_io_ratio
        self.idle_threshold = idle_threshold

    def detect(self) -> list[WasteFinding]:
        findings: list[WasteFinding] = []
        profiles = self.profiler.all_profiles()
        if not profiles:
            return findings

        total_cost = sum(p.total_cost for p in profiles)

        for p in profiles:
            findings.extend(self._check_overprompted(p))
            findings.extend(self._check_idle(p, total_cost))

        findings.extend(self._check_expensive_model_concentration(profiles, total_cost))
        return findings

    def _check_overprompted(self, p: NodeProfile) -> list[WasteFinding]:
        ratio = p.input_output_ratio
        if ratio > self.max_io_ratio and p.avg_input_tokens > 200:
            return [WasteFinding(
                node_id=p.node_id,
                node_title=p.node_title,
                category="overprompted",
                severity="high" if ratio > 30 else "medium",
                message=(
                    f"Node '{p.node_title or p.node_id}' receives {p.avg_input_tokens:,.0f} tokens avg "
                    f"but outputs {p.avg_output_tokens:,.0f} (ratio {ratio:.1f}×)."
                ),
                suggestion="Consider extractive pre-filtering, summarization, or reducing the prompt template size.",
            )]
        return []

    def _check_idle(self, p: NodeProfile, total_cost: float) -> list[WasteFinding]:
        if total_cost == 0:
            return []
        fraction = p.total_cost / total_cost
        if fraction < self.idle_threshold and p.run_count > 5:
            return [WasteFinding(
                node_id=p.node_id,
                node_title=p.node_title,
                category="idle",
                severity="low",
                message=f"Node '{p.node_title or p.node_id}' accounts for only {fraction:.1%} of cost over {p.run_count} runs.",
                suggestion="Consider removing or conditionally bypassing this node.",
            )]
        return []

    def _check_expensive_model_concentration(
        self, profiles: list[NodeProfile], total_cost: float
    ) -> list[WasteFinding]:
        findings: list[WasteFinding] = []
        if not profiles or total_cost == 0:
            return findings

        top = self.profiler.top_by_cost(3)
        top_cost = sum(p.total_cost for p in top)
        fraction = top_cost / total_cost

        if fraction > DEFAULT_EXPENSIVE_MODEL_RATIO and len(top) <= 2:
            names = ", ".join(f"'{p.node_title or p.node_id}'" for p in top)
            findings.append(WasteFinding(
                node_id=",".join(p.node_id for p in top),
                node_title=names,
                category="expensive_model",
                severity="high",
                message=(
                    f"Two nodes ({names}) account for {fraction:.0%} of tokens. "
                    f"If they use an expensive model, consider downgrading for simple tasks."
                ),
                suggestion=(
                    "Tasks like classification, extraction, or short summarization "
                    "often run fine on cheaper models (gpt-4o-mini, claude-3-haiku)."
                ),
            ))
        return findings
