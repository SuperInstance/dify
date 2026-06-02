"""Tests for WorkflowBudget."""

import pytest

from controllers.service_api.budget_watchdog.budget import BudgetWindow, WorkflowBudget
from controllers.service_api.budget_watchdog.error import BudgetExceededError
from controllers.service_api.budget_watchdog.model import ModelId
from controllers.service_api.budget_watchdog.phase import BudgetPhase


class TestWorkflowBudget:
    def test_new_budget_starts_empty(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 100_000, 50_00)
        assert b.tokens_consumed == 0
        assert b.cost_consumed_cents == 0

    def test_spend_tokens_normal(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 100_000, 50_00)
        phase = b.spend_tokens(10_000, 5_00)
        assert phase == BudgetPhase.NORMAL
        assert b.tokens_consumed == 10_000
        assert b.cost_consumed_cents == 5_00

    def test_spend_pretransition(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 1000, 10_000)
        phase = b.spend_tokens(650, 60_00)
        assert phase == BudgetPhase.PRE_TRANSITION

    def test_spend_transitioning(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 1000, 10_000)
        phase = b.spend_tokens(900, 90_00)
        assert phase == BudgetPhase.TRANSITIONING

    def test_spend_exceeds_limit(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 100, 50_00)
        with pytest.raises(BudgetExceededError) as exc_info:
            b.spend_tokens(150, 60_00)
        assert "exceeded" in str(exc_info.value)

    def test_spend_and_downgrade(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 1000, 10_000)
        phase, downgraded = b.spend_and_downgrade(900, 90_00)
        assert phase == BudgetPhase.TRANSITIONING
        assert downgraded == ModelId.GPT4O_MINI

    def test_spend_and_downgrade_twice(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 1000, 10_000)
        phase1, d1 = b.spend_and_downgrade(860, 86_00)
        assert d1 == ModelId.GPT4O_MINI

        phase2, d2 = b.spend_and_downgrade(80, 8_00)
        assert d2 == ModelId.GPT35_TURBO

    def test_current_phase(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 1000, 10_000)
        assert b.current_phase() == BudgetPhase.NORMAL
        b.spend_tokens(700, 70_00)
        assert b.current_phase() == BudgetPhase.PRE_TRANSITION
        b.spend_tokens(200, 20_00)
        assert b.current_phase() == BudgetPhase.TRANSITIONING

    def test_reset(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 100, 10_00)
        b.spend_tokens(90, 9_00)
        assert b.tokens_consumed == 90

        # Reset should clear consumption
        b.reset(200, 20_00, BudgetWindow.WEEKLY)
        assert b.tokens_consumed == 0
        assert b.token_limit == 200
        assert b.downgrade_count == 0

    def test_utilisation(self):
        b = WorkflowBudget.create("test", ModelId.GPT4O, 1000, 10_000)
        assert abs(b.token_utilisation() - 0.0) < 0.001
        assert abs(b.cost_utilisation() - 0.0) < 0.001

        b.spend_tokens(500, 5_000)
        assert abs(b.token_utilisation() - 0.5) < 0.001
        assert abs(b.cost_utilisation() - 0.5) < 0.001

    def test_window_end_times(self):
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        daily_end = BudgetWindow.DAILY.end_from(now)
        weekly_end = BudgetWindow.WEEKLY.end_from(now)
        monthly_end = BudgetWindow.MONTHLY.end_from(now)

        assert daily_end > now
        assert weekly_end > daily_end
        assert monthly_end > weekly_end
