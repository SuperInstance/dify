# 🏆 SuperInstance Enhancement: Budget Watchdog

> **Same Dify. Won't bankrupt your team.**

Dify makes building AI apps easy. The Budget Watchdog makes running them affordable. Set per-workflow and team-level budgets, get warned before you exceed them, and let models auto-downgrade when you're getting close.

## Architecture

```
┌────────────────────────────────────────────────┐
│              Budget Watchdog Layer              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Workflow │  │   Team   │  │  Alert Store  │  │
│  │  Budgets │  │  Budgets │  │  (RingBuffer) │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │               │          │
│  ┌────▼──────────────▼───────────────▼───────┐  │
│  │        GraphEngine Layer (Layer)         │  │
│  │   Hooks into workflow execution at       │  │
│  │   on_node_run_start / on_node_run_end     │  │
│  └────────────────┬────────────────────────┘  │
│                   │                            │
└───────────────────┼────────────────────────────┘
                    │
    ┌───────────────▼────────────────┐
    │       Dify Workflow Engine     │
    │  LLMQuotaLayer → BudgetWdgLayer│
    │  → ExecutionLimitsLayer       │
    └────────────────────────────────┘
```

## Budget Phases

The watchdog uses a **one-sided conservation model**: spending only increases within a window.

| Phase | Trigger | What Happens |
|-------|---------|-------------|
| **Normal** | < 60% used | Business as usual |
| **PreTransition** | ≥ 60% used | Warnings logged, alerts fired |
| **Transitioning** | ≥ 85% used | Models auto-downgraded |
| **PostTransition** | Budget reset | Models restored to original |

### Model Downgrade Chain

```
GPT-4o → GPT-4o-mini → GPT-3.5 Turbo → ✗
Claude 3 Opus → Claude 3 Sonnet → Claude 3 Haiku → ✗
Gemini Pro → Gemini Flash → ✗
Llama 3 70B → Llama 3 8B → ✗
```

## Usage

### 1. Configure Per-Workflow Budget

```python
from controllers.service_api.budget_watchdog import WorkflowBudget, ModelId, BudgetWindow

budget = WorkflowBudget.create(
    workflow_name="customer-support",
    model=ModelId.GPT4O,
    token_limit=1_000_000,      # 1M tokens/day
    cost_limit_cents=50_000,     # $500/day
    window=BudgetWindow.DAILY,
)
```

### 2. Configure Team Budget

```python
from controllers.service_api.budget_watchdog import TeamBudget, TeamMember

team = TeamBudget(
    name="engineering",
    team_token_limit=10_000_000,    # 10M tokens/period
    team_cost_limit_cents=500_000,  # $5,000/period
    period_days=30,
)

team.add_member(TeamMember("alice@co.com", token_quota=2_000_000, cost_quota_cents=100_000))
team.add_member(TeamMember("bob@co.com", token_quota=3_000_000, cost_quota_cents=150_000))
```

### 3. Add Layer to Workflow Engine

The `BudgetWatchdogLayer` hooks into the existing GraphEngine alongside `LLMQuotaLayer`:

```python
from controllers.service_api.budget_watchdog.layer import BudgetWatchdogLayer

# In workflow_entry.py:
self.graph_engine.layer(LLMQuotaLayer(tenant_id=tenant_id))
self.graph_engine.layer(BudgetWatchdogLayer(tenant_id=tenant_id))
```

### 4. REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/budgets` | List all workflow budgets |
| `POST` | `/v1/budgets` | Create a workflow budget |
| `GET` | `/v1/budgets/:name` | Get budget details |
| `POST` | `/v1/budgets/:name/reset` | Reset a budget for new window |
| `GET` | `/v1/budgets/team` | Get team budget |
| `POST` | `/v1/budgets/team` | Configure team budget |
| `GET` | `/v1/budgets/alerts` | Get alert history |

## Alert Levels

| Level | Meaning | Trigger |
|-------|---------|---------|
| `INFO` | Normal operation | < 60% |
| `WARNING` | Budget nearing limit | ≥ 60% |
| `CRITICAL` | Auto-downgrade triggered | ≥ 85% |

## Storage

The current implementation uses in-memory storage (class variables on `BudgetWatchdogLayer`). For production use, swap to Redis or PostgreSQL:

```python
# Example: Redis-backed store
class RedisBudgetStore:
    def get_budget(self, tenant_id, workflow_name) -> WorkflowBudget | None:
        data = redis_client.get(f"budget:{tenant_id}:{workflow_name}")
        return WorkflowBudget.from_dict(json.loads(data)) if data else None

    def save_budget(self, tenant_id, workflow_name, budget):
        redis_client.setex(
            f"budget:{tenant_id}:{workflow_name}",
            timedelta(days=1),
            json.dumps(budget.to_dict()),
        )
```

## Testing

Run the test suite:

```bash
cd api
pytest tests/unit_tests/budget_watchdog/ -v
```

## Migration Guide (from LLMQuotaLayer only)

If you're already using Dify's built-in `LLMQuotaLayer`, adding the Budget Watchdog is simple:

1. Add the `BudgetWatchdogLayer` after `LLMQuotaLayer` in `workflow_entry.py`
2. Configure per-workflow budgets via the `/v1/budgets` API
3. The watchdog handles auto-downgrade automatically

## Configuration Reference

```python
# Default thresholds
thresholds = Thresholds(
    pre_transition=0.60,   # 60% → warning
    transitioning=0.85,    # 85% → downgrade
)

# Budget windows
BudgetWindow.DAILY    # Resets every 24h
BudgetWindow.WEEKLY   # Resets every 7 days
BudgetWindow.MONTHLY  # Resets every 30 days
```
