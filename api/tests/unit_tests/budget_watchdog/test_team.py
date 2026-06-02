"""Tests for TeamBudget and TeamMember."""

import pytest

from controllers.service_api.budget_watchdog.budget import WorkflowBudget
from controllers.service_api.budget_watchdog.error import (
    BudgetExceededError,
    InvalidConfigError,
    MemberQuotaExceededError,
)
from controllers.service_api.budget_watchdog.model import ModelId
from controllers.service_api.budget_watchdog.phase import BudgetPhase
from controllers.service_api.budget_watchdog.team import TeamBudget, TeamMember


class TestTeamMember:
    def test_spend(self):
        member = TeamMember("alice", 100_000, 5_000)
        member.spend(10_000, 5_00)
        assert member.tokens_consumed == 10_000
        assert member.cost_consumed_cents == 5_00

    def test_exceed_quota(self):
        member = TeamMember("bob", 1000, 10_00)
        with pytest.raises(MemberQuotaExceededError) as exc_info:
            member.spend(2000, 20_00)
        assert "quota exceeded" in str(exc_info.value)

    def test_utilisation(self):
        member = TeamMember("carol", 1000, 10_000)
        assert abs(member.token_utilisation() - 0.0) < 0.001
        member.spend(500, 5_000)
        assert abs(member.token_utilisation() - 0.5) < 0.001
        assert abs(member.cost_utilisation() - 0.5) < 0.001


class TestTeamBudget:
    def test_new_budget(self):
        team = TeamBudget("engineering", 1_000_000, 50_000, 30)
        assert team.name == "engineering"
        assert team.team_tokens_consumed == 0
        assert team.member_count() == 0

    def test_spend_normal(self):
        team = TeamBudget("eng", 100_000, 10_000, 30)
        team.add_member(TeamMember("alice", 50_000, 5_000))
        team.add_workflow(WorkflowBudget.create("chat", ModelId.GPT4O, 100_000, 10_000))

        phase = team.spend("alice", "chat", 10_000, 10_00)
        assert phase == BudgetPhase.NORMAL
        assert team.team_tokens_consumed == 10_000

    def test_exceeds_limit(self):
        team = TeamBudget("eng", 1000, 10_00, 30)
        team.add_member(TeamMember("alice", 1000, 10_00))
        team.add_workflow(WorkflowBudget.create("chat", ModelId.GPT4O, 1000, 10_00))

        with pytest.raises((BudgetExceededError, MemberQuotaExceededError)):
            team.spend("alice", "chat", 2000, 20_00)

    def test_pretransition_alert(self):
        team = TeamBudget("eng", 1000, 10_000, 30)
        team.add_member(TeamMember("alice", 1000, 10_000))
        team.add_workflow(WorkflowBudget.create("chat", ModelId.GPT4O, 1000, 10_000))

        phase = team.spend("alice", "chat", 700, 70_00)
        assert phase == BudgetPhase.PRE_TRANSITION
        assert not team.alerts.is_empty()

    def test_member_not_found(self):
        team = TeamBudget("eng", 1000, 10_00, 30)
        with pytest.raises(InvalidConfigError) as exc_info:
            team.spend("nonexistent", "chat", 100, 1_00)
        assert "not found" in str(exc_info.value)

    def test_member_count(self):
        team = TeamBudget("eng", 100_000, 10_000, 30)
        team.add_member(TeamMember("alice", 1000, 10_00))
        team.add_member(TeamMember("bob", 1000, 10_00))
        assert team.member_count() == 2

    def test_workflow_count(self):
        team = TeamBudget("eng", 100_000, 10_000, 30)
        team.add_workflow(WorkflowBudget.create("chat", ModelId.GPT4O, 1000, 10_00))
        team.add_workflow(WorkflowBudget.create("search", ModelId.GPT4O_MINI, 1000, 5_00))
        assert team.workflow_count() == 2
