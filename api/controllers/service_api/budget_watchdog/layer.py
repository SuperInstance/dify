"""
GraphEngine layer for Budget Watchdog enforcement.

Hooks into Dify's workflow execution to enforce per-workflow and team
budgets at each LLM-backed node. This layer sits alongside the existing
LLMQuotaLayer and provides budget-aware model routing.
"""

from __future__ import annotations

import logging
from typing import ClassVar, final, override

from core.app.llm import deduct_llm_quota_for_model, ensure_llm_quota_available_for_model
from core.errors.error import QuotaExceededError
from graphon.enums import BuiltinNodeTypes
from graphon.graph_engine.entities.commands import AbortCommand, CommandType
from graphon.graph_engine.layers import GraphEngineLayer
from graphon.graph_events import GraphEngineEvent, GraphNodeEventBase, NodeRunSucceededEvent
from graphon.node_events import NodeRunResult
from graphon.nodes.base.node import Node

from .alert import AlertLevel, AlertStore
from .budget import WorkflowBudget
from .error import BudgetExceededError, WatchdogError
from .model import ModelId, downgrade_model, resolve_model_id
from .phase import BudgetPhase, Thresholds, DEFAULT_THRESHOLDS, detect_phase
from .team import TeamBudget, TeamMember

logger = logging.getLogger(__name__)

# Node types that consume LLM quota — same as LLMQuotaLayer
_QUOTA_NODE_TYPES: frozenset[str] = frozenset([
    BuiltinNodeTypes.LLM,
    BuiltinNodeTypes.PARAMETER_EXTRACTOR,
    BuiltinNodeTypes.QUESTION_CLASSIFIER,
])


@final
class BudgetWatchdogLayer(GraphEngineLayer):
    """Graph layer that enforces per-workflow and per-tenant budget limits.

    This layer:
    - Tracks token/cost consumption per workflow run
    - Enforces daily/weekly/monthly budget windows
    - Auto-downgrades models when budgets approach limits (60%/85%/100%)
    - Generates alerts for audit trails
    - Aggregates into team budgets with per-member quotas
    """

    tenant_id: str
    _abort_sent: bool

    # Static budget stores (tenant-scoped) — in production this would use
    # Redis or the database, but for now we provide an in-memory store
    # that matches the Rust crate's architecture.
    _workflow_budgets: ClassVar[dict[str, dict[str, WorkflowBudget]]] = {}
    _team_budgets: ClassVar[dict[str, TeamBudget]] = {}

    def __init__(
        self,
        tenant_id: str,
        thresholds: Thresholds = DEFAULT_THRESHOLDS,
    ) -> None:
        super().__init__()
        self.tenant_id = tenant_id
        self._abort_sent = False
        self._thresholds = thresholds

    # ── Public API for configuring budgets ──────────────────────────────

    @classmethod
    def configure_workflow_budget(
        cls,
        tenant_id: str,
        workflow_name: str,
        model: ModelId,
        token_limit: int,
        cost_limit_cents: int,
    ) -> WorkflowBudget:
        """Configure a budget for a specific workflow."""
        if tenant_id not in cls._workflow_budgets:
            cls._workflow_budgets[tenant_id] = {}

        budget = WorkflowBudget.create(
            workflow_name=workflow_name,
            model=model,
            token_limit=token_limit,
            cost_limit_cents=cost_limit_cents,
        )
        cls._workflow_budgets[tenant_id][workflow_name] = budget
        return budget

    @classmethod
    def configure_team_budget(
        cls,
        tenant_id: str,
        team_name: str,
        token_limit: int,
        cost_limit_cents: int,
        period_days: int = 30,
    ) -> TeamBudget:
        """Configure a team budget."""
        budget = TeamBudget(
            name=team_name,
            team_token_limit=token_limit,
            team_cost_limit_cents=cost_limit_cents,
            period_days=period_days,
        )
        cls._team_budgets[tenant_id] = budget
        return budget

    @classmethod
    def get_workflow_budgets(cls, tenant_id: str) -> list[WorkflowBudget]:
        """Get all workflow budgets for a tenant."""
        return list(cls._workflow_budgets.get(tenant_id, {}).values())

    @classmethod
    def get_workflow_budget(cls, tenant_id: str, workflow_name: str) -> WorkflowBudget | None:
        """Get a specific workflow budget."""
        return cls._workflow_budgets.get(tenant_id, {}).get(workflow_name)

    @classmethod
    def get_team_budget(cls, tenant_id: str) -> TeamBudget | None:
        """Get the team budget for a tenant."""
        return cls._team_budgets.get(tenant_id)

    @classmethod
    def get_alerts(cls, tenant_id: str) -> list:
        """Get all alerts for a tenant."""
        alerts = []
        # From workflow budgets
        for wf_budget in cls._workflow_budgets.get(tenant_id, {}).values():
            alerts.extend(wf_budget._alert_store.all())
        # From team budget
        team = cls._team_budgets.get(tenant_id)
        if team:
            alerts.extend(team.alerts.all())
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    # ── GraphEngineLayer lifecycle hooks ────────────────────────────────

    @override
    def on_graph_start(self) -> None:
        self._abort_sent = False

    @override
    def on_event(self, event: GraphEngineEvent) -> None:
        pass

    @override
    def on_graph_end(self, error: Exception | None) -> None:
        pass

    @override
    def on_node_run_start(self, node: Node) -> None:
        """Check budgets before node execution."""
        if self._abort_sent:
            return

        if not self._is_quota_node(node):
            return

        # Resolve the model for this node
        model_identity = self._extract_model_identity_from_node(node)
        if model_identity is None:
            return  # LLMQuotaLayer handles this case

        provider, model_name = model_identity
        model_id = resolve_model_id(provider, model_name)

        # Check workflow budget
        workflow_name = self._resolve_workflow_name(node)
        if workflow_name:
            wf_budget = self._get_or_create_budget(workflow_name, model_id)
            phase = wf_budget.current_phase()

            # If in Transitioning phase, auto-downgrade the model config
            if phase == BudgetPhase.TRANSITIONING:
                cheaper = downgrade_model(model_id)
                if cheaper is not None:
                    self._override_node_model(node, provider, cheaper.value)
                    logger.info(
                        "BudgetWatchdog: downgraded %s → %s for node %s in workflow %s",
                        model_id.label(), cheaper.label(), node.id, workflow_name,
                    )

        # Check team budget
        team_budget = self._team_budgets.get(self.tenant_id)
        if team_budget and team_budget.current_phase() in (
            BudgetPhase.TRANSITIONING, BudgetPhase.POST_TRANSITION
        ):
            logger.warning(
                "BudgetWatchdog: team '%s' in restricted phase — node %s may be throttled",
                team_budget.name, node.id,
            )

    @override
    def on_node_run_end(
        self,
        node: Node,
        error: Exception | None,
        result_event: GraphNodeEventBase | None = None,
    ) -> None:
        """Deduct usage from budgets after node execution."""
        if error is not None:
            return

        if not isinstance(result_event, NodeRunSucceededEvent):
            return

        if not self._is_quota_node(node):
            return

        llm_usage = result_event.node_run_result.llm_usage
        if llm_usage is None:
            return

        prompt_tokens = llm_usage.prompt_tokens or 0
        completion_tokens = llm_usage.completion_tokens or 0
        total_tokens = prompt_tokens + completion_tokens

        # Estimate cost (in cents) — a simplified model
        # Real implementation would use provider/ model pricing tables
        estimated_cost_cents = self._estimate_cost(
            node, prompt_tokens, completion_tokens
        )

        # Check workflow budget
        workflow_name = self._resolve_workflow_name(node)
        if workflow_name:
            wf_budget = self._get_or_create_budget(workflow_name, ModelId.GPT4O_MINI)
            try:
                phase, downgraded = wf_budget.spend_and_downgrade(
                    total_tokens, estimated_cost_cents
                )
                if downgraded is not None:
                    logger.info(
                        "BudgetWatchdog: workflow '%s' auto-downgraded to %s "
                        "(phase=%s, tokens=%d/%d, cost=%d/%d)",
                        workflow_name, downgraded.label(),
                        phase.value, wf_budget.tokens_consumed,
                        wf_budget.token_limit, wf_budget.cost_consumed_cents,
                        wf_budget.cost_limit_cents,
                    )
            except BudgetExceededError as exc:
                logger.warning(
                    "BudgetWatchdog: workflow '%s' budget exceeded: %s",
                    workflow_name, exc,
                )
                self._send_abort_command(reason=str(exc))

    # ── Internal helpers ────────────────────────────────────────────────

    def _resolve_workflow_name(self, node: Node) -> str | None:
        """Resolve the workflow name from the node's graph runtime state."""
        try:
            workflow_id = getattr(node.graph_runtime_state, "workflow_id", None)
            if workflow_id:
                return f"wf-{workflow_id[:8]}"
        except Exception:
            pass
        return None

    def _get_or_create_budget(self, workflow_name: str, model: ModelId) -> WorkflowBudget:
        """Get existing budget or create a default one."""
        budgets = self._workflow_budgets.setdefault(self.tenant_id, {})
        if workflow_name not in budgets:
            # Default budget: 1M tokens, $500/day
            budgets[workflow_name] = WorkflowBudget.create(
                workflow_name=workflow_name,
                model=model,
                token_limit=1_000_000,
                cost_limit_cents=50_000,
            )
        return budgets[workflow_name]

    def _estimate_cost(self, node: Node, prompt_tokens: int, completion_tokens: int) -> int:
        """Estimate API cost in US cents.

        Simplified pricing — real implementation should use actual provider
        pricing tables. These are approximate per-1K-token costs.
        """
        # Default rates (per 1K tokens, in cents)
        prompt_rate = 0.15   # ~$0.0015/1K
        completion_rate = 0.60  # ~$0.006/1K

        model_identity = self._extract_model_identity_from_node(node)
        if model_identity:
            provider, model_name = model_identity
            key = f"{provider}/{model_name}".lower()
            rates = _MODEL_COST_RATES.get(key)
            if rates:
                prompt_rate, completion_rate = rates

        cost_cents = (
            (prompt_tokens / 1000) * prompt_rate +
            (completion_tokens / 1000) * completion_rate
        )
        return max(1, round(cost_cents))

    def _override_node_model(self, node: Node, provider: str, model_name: str) -> None:
        """Override the model config on a node to enforce downgrade."""
        node_data = getattr(node, "node_data", None) or getattr(node, "data", None)
        if node_data is None:
            return

        model_config = getattr(node_data, "model", None)
        if model_config is None:
            return

        current_name = getattr(model_config, "name", None)
        if current_name and current_name != model_name:
            model_config.name = model_name
            logger.info(
                "BudgetWatchdog: overrode node model from %s to %s",
                current_name, model_name,
            )

    def _send_abort_command(self, *, reason: str) -> None:
        """Send an abort command to stop workflow execution."""
        if not self.command_channel or self._abort_sent:
            return
        try:
            self.command_channel.send_command(
                AbortCommand(
                    command_type=CommandType.ABORT,
                    reason=reason,
                )
            )
            self._abort_sent = True
        except Exception:
            logger.exception("BudgetWatchdog: failed to send abort command")

    @staticmethod
    def _is_quota_node(node: Node) -> bool:
        """Check if the node supports quota/budget tracking."""
        return node.node_type in _QUOTA_NODE_TYPES

    @staticmethod
    def _extract_model_identity_from_node(node: Node) -> tuple[str, str] | None:
        """Extract (provider, model_name) from node config."""
        node_data = getattr(node, "node_data", None)
        if node_data is None:
            node_data = getattr(node, "data", None)
        if node_data is None:
            return None

        model_config = getattr(node_data, "model", None)
        if model_config is None:
            return None

        provider = getattr(model_config, "provider", None)
        model_name = getattr(model_config, "name", None)
        if isinstance(provider, str) and provider and isinstance(model_name, str) and model_name:
            return provider, model_name
        return None


# Approximate per-1K-token costs in US cents (prompt, completion)
_MODEL_COST_RATES: dict[str, tuple[float, float]] = {
    "openai/gpt-4o": (2.50, 10.00),         # $0.025/$0.10 per 1K
    "openai/gpt-4o-mini": (0.15, 0.60),     # $0.0015/$0.006 per 1K
    "openai/gpt-3.5-turbo": (0.50, 1.50),   # $0.005/$0.015 per 1K
    "anthropic/claude-3-opus": (15.00, 75.00),  # $0.15/$0.75 per 1K
    "anthropic/claude-3-sonnet": (3.00, 15.00), # $0.03/$0.15 per 1K
    "anthropic/claude-3-haiku": (0.25, 1.25),   # $0.0025/$0.0125 per 1K
    "google/gemini-pro": (0.50, 1.50),
    "google/gemini-flash": (0.10, 0.40),
    "meta/llama-3-70b": (0.65, 2.75),
    "meta/llama-3-8b": (0.05, 0.15),
}
