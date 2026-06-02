"""
Conservation phases a workflow passes through as it approaches its budget limit.

Phase model is **one-sided**: spending only ever increases within a window,
so transitions always go forward:

    Normal → PreTransition → Transitioning → PostTransition

Phase meanings:

    | Phase | Trigger | Behaviour |
    |---|---|---|
    | Normal | < 60% used | Business as usual — premium models allowed |
    | PreTransition | ≥ 60% used | Log warning, recommend reviewing spend |
    | Transitioning | ≥ 85% used | Auto-downgrade models to cheaper tier |
    | PostTransition | Budget resets | System recovers, premium models restored |
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BudgetPhase(Enum):
    """Conservation phases a workflow passes through."""

    NORMAL = "normal"
    """< 60% consumed — full freedom."""

    PRE_TRANSITION = "pre_transition"
    """60%–84% consumed — warning zone. Logged, not yet constrained."""

    TRANSITIONING = "transitioning"
    """85%–100% consumed — active budget preservation. Models auto-downgraded."""

    POST_TRANSITION = "post_transition"
    """Budget has been reset (new window). Models restore."""

    def is_restricted(self) -> bool:
        """Returns True if the phase restricts model usage."""
        return self in (BudgetPhase.TRANSITIONING, BudgetPhase.POST_TRANSITION)

    def description(self) -> str:
        """Human-readable description."""
        return _DESCRIPTIONS[self]

    def sort_key(self) -> int:
        """Numeric sort key for comparing phases (0 = most relaxed)."""
        return _SORT_KEYS[self]


_DESCRIPTIONS = {
    BudgetPhase.NORMAL: "Normal operation — no restrictions",
    BudgetPhase.PRE_TRANSITION: "Pre-transition — 60%+ budget used, consider reviewing spend",
    BudgetPhase.TRANSITIONING: "Transitioning — 85%+ budget used, models auto-downgraded",
    BudgetPhase.POST_TRANSITION: "Post-transition — budget reset, models restored",
}

_SORT_KEYS = {
    BudgetPhase.NORMAL: 0,
    BudgetPhase.PRE_TRANSITION: 1,
    BudgetPhase.TRANSITIONING: 2,
    BudgetPhase.POST_TRANSITION: 3,
}


@dataclass
class Thresholds:
    """Thresholds that define phase boundaries. Expressed as fractions of 1.0."""

    pre_transition: float = 0.60
    """Fraction of budget that triggers PreTransition. Default: 0.60"""

    transitioning: float = 0.85
    """Fraction of budget that triggers Transitioning. Default: 0.85"""


# Default global thresholds
DEFAULT_THRESHOLDS = Thresholds()


def detect_phase(consumed: float, limit: float, thresholds: Thresholds = DEFAULT_THRESHOLDS) -> BudgetPhase:
    """Detect the current phase given consumption out of a limit.

    Args:
        consumed: Amount consumed (tokens or cost).
        limit: Total available.
        thresholds: Phase threshold config (defaults to 60%/85%).

    Returns:
        The current BudgetPhase. Returns PostTransition when limit is zero.
    """
    if limit <= 0:
        return BudgetPhase.POST_TRANSITION

    ratio = consumed / limit

    if ratio >= thresholds.transitioning:
        return BudgetPhase.TRANSITIONING
    elif ratio >= thresholds.pre_transition:
        return BudgetPhase.PRE_TRANSITION
    else:
        return BudgetPhase.NORMAL
