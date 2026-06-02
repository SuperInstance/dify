"""
Per-workflow budget tracking with token and cost limits.

Tracks consumption within daily/weekly/monthly windows. Detects conservation
phases and supports auto-downgrade of models when approaching limits.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from .alert import AlertLevel, AlertRecord, AlertStore
from .error import BudgetExceededError, WatchdogError
from .model import ModelId, downgrade_model
from .phase import BudgetPhase, Thresholds, DEFAULT_THRESHOLDS, detect_phase


class BudgetWindow(Enum):
    """Supported budget window durations."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    def end_from(self, from_dt: datetime) -> datetime:
        """Returns the end-of-window timestamp."""
        if self == BudgetWindow.DAILY:
            return from_dt + timedelta(days=1)
        elif self == BudgetWindow.WEEKLY:
            return from_dt + timedelta(weeks=1)
        else:  # MONTHLY
            return from_dt + timedelta(days=30)


class WorkflowBudget:
    """A time-aligned budget window for a single workflow.

    Tracks token and cost consumption, detects conservation phases,
    and can auto-downgrade the assigned model when approaching limits.

    Spending is one-sided — it only ever goes up within a window.
    """

    def __init__(
        self,
        workflow_name: str,
        model: ModelId,
        token_limit: int,
        cost_limit_cents: int,
        window: BudgetWindow = BudgetWindow.DAILY,
        thresholds: Thresholds = DEFAULT_THRESHOLDS,
        alert_store: Optional[AlertStore] = None,
    ) -> None:
        self.workflow_name: str = workflow_name
        self.model: ModelId = model
        self.token_limit: int = token_limit
        self.cost_limit_cents: int = cost_limit_cents
        self.tokens_consumed: int = 0
        self.cost_consumed_cents: int = 0
        self.window_start: datetime = datetime.now(timezone.utc)
        self.window_end: datetime = window.end_from(self.window_start)
        self.downgrade_count: int = 0
        self._window: BudgetWindow = window
        self._thresholds: Thresholds = thresholds
        self._alert_store: AlertStore = alert_store or AlertStore()
        self._original_model: ModelId = model

    @classmethod
    def create(
        cls,
        workflow_name: str,
        model: ModelId,
        token_limit: int,
        cost_limit_cents: int,
        window: BudgetWindow = BudgetWindow.DAILY,
    ) -> WorkflowBudget:
        """Create a new workflow budget (shorthand for __init__)."""
        return cls(workflow_name, model, token_limit, cost_limit_cents, window)

    def spend_tokens(self, tokens: int, cost_cents: int) -> BudgetPhase:
        """Record token and cost spending. Returns the current phase after spending.

        Raises BudgetExceededError if the budget is already exhausted.
        """
        self.tokens_consumed += tokens
        self.cost_consumed_cents += cost_cents

        # Check if exhausted
        if self.tokens_consumed >= self.token_limit or self.cost_consumed_cents >= self.cost_limit_cents:
            raise BudgetExceededError(
                f"Workflow '{self.workflow_name}' exceeded: tokens {self.tokens_consumed}/{self.token_limit} "
                f"or cost {self.cost_consumed_cents}/{self.cost_limit_cents}"
            )

        return self.current_phase()

    def spend_and_downgrade(self, tokens: int, cost_cents: int) -> tuple[BudgetPhase, Optional[ModelId]]:
        """Spend tokens and auto-downgrade the model if entering Transitioning phase."""
        phase = self.spend_tokens(tokens, cost_cents)

        downgraded: Optional[ModelId] = None
        if phase == BudgetPhase.TRANSITIONING:
            cheaper = downgrade_model(self.model)
            if cheaper is not None:
                self.model = cheaper
                self.downgrade_count += 1
                downgraded = cheaper

                self._alert_store.push(AlertRecord(
                    workflow=self.workflow_name,
                    level=AlertLevel.CRITICAL,
                    message=(
                        f"Workflow '{self.workflow_name}' — "
                        f"auto-downgraded from {self.model.label()} to {cheaper.label()}"
                    ),
                ))

        return phase, downgraded

    def current_phase(self) -> BudgetPhase:
        """Check the current phase without spending."""
        token_ratio = self.tokens_consumed / max(self.token_limit, 1)
        cost_ratio = self.cost_consumed_cents / max(self.cost_limit_cents, 1)

        token_phase = detect_phase(self.tokens_consumed, self.token_limit, self._thresholds)
        cost_phase = detect_phase(self.cost_consumed_cents, self.cost_limit_cents, self._thresholds)

        # Use the more restrictive phase
        phase = max(token_phase.sort_key(), cost_phase.sort_key())
        return [
            BudgetPhase.NORMAL,
            BudgetPhase.PRE_TRANSITION,
            BudgetPhase.TRANSITIONING,
            BudgetPhase.POST_TRANSITION,
        ][phase]

    def reset(self, new_limit: int, new_cost_cents: int, window: Optional[BudgetWindow] = None) -> None:
        """Reset for a new window. Model upgrades back to original."""
        self.model = self._original_model
        self.token_limit = new_limit
        self.cost_limit_cents = new_cost_cents
        self.tokens_consumed = 0
        self.cost_consumed_cents = 0
        now = datetime.now(timezone.utc)
        self.window_start = now
        w = window or self._window
        self.window_end = w.end_from(now)
        self.downgrade_count = 0

    def token_utilisation(self) -> float:
        """Compute token utilisation ratio (0.0 - 1.0)."""
        if self.token_limit == 0:
            return 1.0
        return self.tokens_consumed / self.token_limit

    def cost_utilisation(self) -> float:
        """Compute cost utilisation ratio (0.0 - 1.0)."""
        if self.cost_limit_cents == 0:
            return 1.0
        return self.cost_consumed_cents / self.cost_limit_cents

    def generate_alert(self) -> AlertRecord:
        """Generate an alert record based on current phase."""
        phase = self.current_phase()
        if phase == BudgetPhase.NORMAL:
            level = AlertLevel.INFO
            message = f"Workflow '{self.workflow_name}' operating normally"
        elif phase == BudgetPhase.PRE_TRANSITION:
            level = AlertLevel.WARNING
            message = (
                f"Workflow '{self.workflow_name}' at {self.token_utilisation() * 100:.1f}% token limit "
                f"({self.tokens_consumed}/{self.token_limit})"
            )
        elif phase == BudgetPhase.TRANSITIONING:
            level = AlertLevel.CRITICAL
            message = (
                f"Workflow '{self.workflow_name}' in Transitioning phase — "
                f"model downgraded to {self.model.label()}"
            )
        else:  # POST_TRANSITION
            level = AlertLevel.INFO
            message = f"Workflow '{self.workflow_name}' budget reset"

        record = AlertRecord(self.workflow_name, level, message)
        self._alert_store.push(record)
        return record

    def to_dict(self) -> dict:
        """Serialize to dict for API responses."""
        return {
            "workflow_name": self.workflow_name,
            "model": self.model.value,
            "model_label": self.model.label(),
            "token_limit": self.token_limit,
            "cost_limit_cents": self.cost_limit_cents,
            "tokens_consumed": self.tokens_consumed,
            "cost_consumed_cents": self.cost_consumed_cents,
            "phase": self.current_phase().value,
            "token_utilisation": round(self.token_utilisation(), 4),
            "cost_utilisation": round(self.cost_utilisation(), 4),
            "downgrade_count": self.downgrade_count,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
        }
