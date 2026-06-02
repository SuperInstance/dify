"""
Team budget management with per-member quotas and aggregate tracking.

Models the entire team's API spending as a shared pool with individual
member quotas. When the team aggregate approaches limits, phase detection
cascades to member budgets.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from .alert import AlertLevel, AlertRecord, AlertStore
from .budget import BudgetWindow, WorkflowBudget
from .error import BudgetExceededError, MemberQuotaExceededError, InvalidConfigError, WatchdogError
from .phase import BudgetPhase, Thresholds, DEFAULT_THRESHOLDS, detect_phase


class TeamMember:
    """A team member with a personal quota within the team budget."""

    def __init__(self, member_id: str, token_quota: int, cost_quota_cents: int) -> None:
        self.id: str = member_id
        self.token_quota: int = token_quota
        self.cost_quota_cents: int = cost_quota_cents
        self.tokens_consumed: int = 0
        self.cost_consumed_cents: int = 0

    def spend(self, tokens: int, cost_cents: int) -> None:
        """Spend tokens for this member. Raises MemberQuotaExceededError if exceeded."""
        new_tokens = self.tokens_consumed + tokens
        new_cost = self.cost_consumed_cents + cost_cents

        if new_tokens > self.token_quota:
            raise MemberQuotaExceededError(
                f"Member '{self.id}' token quota exceeded: {new_tokens} > {self.token_quota}"
            )
        if new_cost > self.cost_quota_cents:
            raise MemberQuotaExceededError(
                f"Member '{self.id}' cost quota exceeded: {new_cost} > {self.cost_quota_cents}"
            )

        self.tokens_consumed = new_tokens
        self.cost_consumed_cents = new_cost

    def token_utilisation(self) -> float:
        """Token utilisation ratio (0.0 - 1.0)."""
        if self.token_quota == 0:
            return 1.0
        return self.tokens_consumed / self.token_quota

    def cost_utilisation(self) -> float:
        """Cost utilisation ratio (0.0 - 1.0)."""
        if self.cost_quota_cents == 0:
            return 1.0
        return self.cost_consumed_cents / self.cost_quota_cents

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "token_quota": self.token_quota,
            "cost_quota_cents": self.cost_quota_cents,
            "tokens_consumed": self.tokens_consumed,
            "cost_consumed_cents": self.cost_consumed_cents,
            "token_utilisation": round(self.token_utilisation(), 4),
            "cost_utilisation": round(self.cost_utilisation(), 4),
        }


class TeamBudget:
    """Aggregate budget across all workflows, with per-team-member quotas."""

    def __init__(
        self,
        name: str,
        team_token_limit: int,
        team_cost_limit_cents: int,
        period_days: int = 30,
        thresholds: Thresholds = DEFAULT_THRESHOLDS,
    ) -> None:
        self.name: str = name
        self.team_token_limit: int = team_token_limit
        self.team_cost_limit_cents: int = team_cost_limit_cents
        self.team_tokens_consumed: int = 0
        self.team_cost_consumed_cents: int = 0
        self.period_start: datetime = datetime.now(timezone.utc)
        self.period_end: datetime = self.period_start + timedelta(days=period_days)
        self._thresholds: Thresholds = thresholds
        self.members: dict[str, TeamMember] = {}
        self.workflows: dict[str, WorkflowBudget] = {}
        self.alerts: AlertStore = AlertStore()

    def add_member(self, member: TeamMember) -> None:
        """Add a member to the team."""
        if member.id not in self.members:
            self.members[member.id] = member

    def add_workflow(self, budget: WorkflowBudget) -> None:
        """Add a workflow budget under team management."""
        if budget.workflow_name not in self.workflows:
            self.workflows[budget.workflow_name] = budget

    def spend(self, member_id: str, workflow_name: str, tokens: int, cost_cents: int) -> BudgetPhase:
        """Spend tokens across a member's workflow.

        Updates both the member quota and the team aggregate.

        Raises BudgetExceededError if team aggregate is exhausted.
        Raises MemberQuotaExceededError if member quota is exceeded.
        """
        member = self.members.get(member_id)
        if member is None:
            raise InvalidConfigError(f"Member '{member_id}' not found")

        # Spend from member quota
        member.spend(tokens, cost_cents)

        # Spend from workflow budget if managed
        wf = self.workflows.get(workflow_name)
        if wf is not None:
            wf.spend_tokens(tokens, cost_cents)

        # Update team aggregate
        self.team_tokens_consumed += tokens
        self.team_cost_consumed_cents += cost_cents

        # Check if team aggregate is exhausted
        if self.team_tokens_consumed >= self.team_token_limit or \
           self.team_cost_consumed_cents >= self.team_cost_limit_cents:
            raise BudgetExceededError(
                f"Team '{self.name}': tokens {self.team_tokens_consumed}/{self.team_token_limit} "
                f"or cost {self.team_cost_consumed_cents}/{self.team_cost_limit_cents}"
            )

        # Detect team phase
        token_phase = detect_phase(self.team_tokens_consumed, self.team_token_limit, self._thresholds)
        cost_phase = detect_phase(self.team_cost_consumed_cents, self.team_cost_limit_cents, self._thresholds)
        phase = max(token_phase.sort_key(), cost_phase.sort_key())
        phase = [
            BudgetPhase.NORMAL,
            BudgetPhase.PRE_TRANSITION,
            BudgetPhase.TRANSITIONING,
            BudgetPhase.POST_TRANSITION,
        ][phase]

        # Generate alerts
        if phase == BudgetPhase.PRE_TRANSITION:
            self.alerts.push(AlertRecord(
                workflow=f"team:{self.name}",
                level=AlertLevel.WARNING,
                message=(
                    f"Team '{self.name}' at "
                    f"{self.team_tokens_consumed / self.team_token_limit * 100:.1f}% aggregate budget "
                    f"({self.team_tokens_consumed}/{self.team_token_limit})"
                ),
            ))
        elif phase == BudgetPhase.TRANSITIONING:
            self.alerts.push(AlertRecord(
                workflow=f"team:{self.name}",
                level=AlertLevel.CRITICAL,
                message=f"Team '{self.name}' in Transitioning — high budget consumption",
            ))

        return phase

    def member_count(self) -> int:
        """Number of team members."""
        return len(self.members)

    def workflow_count(self) -> int:
        """Number of managed workflows."""
        return len(self.workflows)

    def team_token_utilisation(self) -> float:
        """Team-level token utilisation."""
        if self.team_token_limit == 0:
            return 1.0
        return self.team_tokens_consumed / self.team_token_limit

    def team_cost_utilisation(self) -> float:
        """Team-level cost utilisation."""
        if self.team_cost_limit_cents == 0:
            return 1.0
        return self.team_cost_consumed_cents / self.team_cost_limit_cents

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "team_token_limit": self.team_token_limit,
            "team_cost_limit_cents": self.team_cost_limit_cents,
            "team_tokens_consumed": self.team_tokens_consumed,
            "team_cost_consumed_cents": self.team_cost_consumed_cents,
            "team_token_utilisation": round(self.team_token_utilisation(), 4),
            "team_cost_utilisation": round(self.team_cost_utilisation(), 4),
            "member_count": self.member_count(),
            "workflow_count": self.workflow_count(),
            "members": [m.to_dict() for m in self.members.values()],
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
        }
