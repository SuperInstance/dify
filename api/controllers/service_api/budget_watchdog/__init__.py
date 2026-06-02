"""
Budget Watchdog — API spending limits for Dify workflows.

Dify makes building AI apps easy. This makes running them affordable.
Set a budget. Get warned before you exceed it. Models auto-downgrade
when you're close.

Architecture:
    Spending is a one-sided conservation law: consumption increases
    monotonically within a window. When consumption passes configurable
    thresholds (60% → warning, 85% → throttle, 100% → stop), the
    watchdog enters a new phase and reacts accordingly.
"""

from .model import ModelId, ModelTier, downgrade_model
from .phase import BudgetPhase, Thresholds, detect_phase
from .budget import BudgetWindow, WorkflowBudget
from .alert import AlertLevel, AlertRecord, AlertStore
from .team import TeamBudget, TeamMember
from .error import WatchdogError, WatchdogResult
from .layer import BudgetWatchdogLayer

__version__ = "0.1.0"

__all__ = [
    "ModelId",
    "ModelTier",
    "downgrade_model",
    "BudgetPhase",
    "Thresholds",
    "detect_phase",
    "BudgetWindow",
    "WorkflowBudget",
    "AlertLevel",
    "AlertRecord",
    "AlertStore",
    "TeamBudget",
    "TeamMember",
    "WatchdogError",
    "WatchdogResult",
    "BudgetWatchdogLayer",
]
