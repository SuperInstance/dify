"""
REST API controller for Budget Watchdog management.

Exposes endpoints for configuring and inspecting budget state:
- GET /budgets — list all workflow budgets
- POST /budgets — configure a new workflow budget
- GET /budgets/<workflow_name> — get specific budget
- POST /budgets/<workflow_name>/reset — reset a budget
- GET /budgets/team — get team budget
- POST /budgets/team — configure team budget
- GET /budgets/alerts — get alert history
"""

from __future__ import annotations

import logging
from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.exceptions import BadRequest, NotFound

from controllers.service_api import service_api_ns
from controllers.service_api.wraps import validate_app_token
from models.model import App

from .budget import BudgetWindow, WorkflowBudget
from .layer import BudgetWatchdogLayer
from .model import ModelId
from .team import TeamBudget, TeamMember

logger = logging.getLogger(__name__)

# Create a sub-namespace under service_api for budget watchdog endpoints
budget_ns = Namespace(
    "budgets",
    description="Budget Watchdog — API spending limits for Dify workflows",
    path="/budgets",
)


# ── Request/ Response models ───────────────────────────────────────────

budget_model = budget_ns.model("BudgetStatus", {
    "workflow_name": fields.String(required=True, description="Workflow name"),
    "model": fields.String(required=True, description="Current model ID"),
    "model_label": fields.String(required=True, description="Current model label"),
    "token_limit": fields.Integer(required=True, description="Token limit"),
    "cost_limit_cents": fields.Integer(required=True, description="Cost limit in US cents"),
    "tokens_consumed": fields.Integer(required=True, description="Tokens consumed"),
    "cost_consumed_cents": fields.Integer(required=True, description="Cost consumed in US cents"),
    "phase": fields.String(required=True, description="Current budget phase"),
    "token_utilisation": fields.Float(required=True, description="Token utilisation ratio"),
    "cost_utilisation": fields.Float(required=True, description="Cost utilisation ratio"),
    "downgrade_count": fields.Integer(required=True, description="Number of model downgrades"),
    "window_start": fields.String(required=True, description="Window start timestamp"),
    "window_end": fields.String(required=True, description="Window end timestamp"),
})

budget_create_model = budget_ns.model("BudgetCreate", {
    "workflow_name": fields.String(required=True, description="Workflow name"),
    "model": fields.String(required=True, description="Model ID (e.g. gpt-4o, gpt-4o-mini)"),
    "token_limit": fields.Integer(required=True, description="Token limit", min=1),
    "cost_limit_cents": fields.Integer(required=True, description="Cost limit in US cents", min=1),
    "window": fields.String(required=False, default="daily", description="Budget window (daily/weekly/monthly)"),
})

budget_reset_model = budget_ns.model("BudgetReset", {
    "token_limit": fields.Integer(required=True, description="New token limit", min=1),
    "cost_limit_cents": fields.Integer(required=True, description="New cost limit in US cents", min=1),
    "window": fields.String(required=False, default="daily", description="Budget window (daily/weekly/monthly)"),
})

team_budget_model = budget_ns.model("TeamBudget", {
    "team_name": fields.String(required=True, description="Team name"),
    "team_token_limit": fields.Integer(required=True, description="Team token limit"),
    "team_cost_limit_cents": fields.Integer(required=True, description="Team cost limit in cents"),
    "team_tokens_consumed": fields.Integer(required=True, description="Team tokens consumed"),
    "team_cost_consumed_cents": fields.Integer(required=True, description="Team cost consumed in cents"),
    "member_count": fields.Integer(required=True, description="Number of members"),
    "workflow_count": fields.Integer(required=True, description="Number of managed workflows"),
    "period_start": fields.String(required=True, description="Period start timestamp"),
    "period_end": fields.String(required=True, description="Period end timestamp"),
})

team_budget_create_model = budget_ns.model("TeamBudgetCreate", {
    "team_name": fields.String(required=True, description="Team name"),
    "token_limit": fields.Integer(required=True, description="Team token limit", min=1),
    "cost_limit_cents": fields.Integer(required=True, description="Team cost limit in cents", min=1),
    "period_days": fields.Integer(required=False, default=30, description="Budget period in days"),
})

alert_model = budget_ns.model("AlertRecord", {
    "timestamp": fields.String(required=True, description="Alert timestamp"),
    "workflow": fields.String(required=True, description="Workflow name"),
    "level": fields.String(required=True, description="Alert level (info/warning/critical)"),
    "message": fields.String(required=True, description="Alert message"),
})

alert_list_model = budget_ns.model("AlertList", {
    "alerts": fields.List(fields.Nested(alert_model), required=True, description="List of alerts"),
    "total": fields.Integer(required=True, description="Total alert count"),
})


# ── Register models with parent namespace ──────────────────────────────

service_api_ns.add_model("BudgetStatus", budget_model)
service_api_ns.add_model("BudgetCreate", budget_create_model)
service_api_ns.add_model("BudgetReset", budget_reset_model)
service_api_ns.add_model("TeamBudget", team_budget_model)
service_api_ns.add_model("TeamBudgetCreate", team_budget_create_model)
service_api_ns.add_model("AlertRecord", alert_model)
service_api_ns.add_model("AlertList", alert_list_model)


# ── Helper ─────────────────────────────────────────────────────────────

def _validate_model(model_str: str) -> ModelId:
    """Validate and return a ModelId from string."""
    try:
        return ModelId(model_str)
    except ValueError:
        valid = [m.value for m in ModelId]
        raise BadRequest(f"Invalid model '{model_str}'. Valid options: {', '.join(valid)}")


# ── Endpoints ──────────────────────────────────────────────────────────

@budget_ns.route("")
class BudgetListApi(Resource):
    @budget_ns.doc("list_budgets")
    @budget_ns.doc(description="List all configured workflow budgets")
    @budget_ns.response(200, "Success", [budget_model])
    def get(self, app_model: App):
        """List all workflow budgets for this tenant."""
        budgets = BudgetWatchdogLayer.get_workflow_budgets(app_model.tenant_id)
        return [b.to_dict() for b in budgets], 200

    @budget_ns.expect(budget_create_model)
    @budget_ns.doc("create_budget")
    @budget_ns.doc(description="Create a new workflow budget")
    @budget_ns.response(201, "Created", budget_model)
    @budget_ns.response(400, "Bad request")
    @validate_app_token
    def post(self, app_model: App):
        """Create a new workflow budget."""
        data = request.get_json(force=True)
        workflow_name = data.get("workflow_name")
        if not workflow_name:
            raise BadRequest("workflow_name is required")

        model = _validate_model(data["model"])
        token_limit = int(data["token_limit"])
        cost_limit_cents = int(data["cost_limit_cents"])

        window_str = data.get("window", "daily")
        try:
            window = BudgetWindow(window_str)
        except ValueError:
            raise BadRequest(f"Invalid window '{window_str}'. Valid: daily, weekly, monthly")

        budget = BudgetWatchdogLayer.configure_workflow_budget(
            app_model.tenant_id,
            workflow_name,
            model,
            token_limit,
            cost_limit_cents,
        )
        return budget.to_dict(), 201


@budget_ns.route("/<string:workflow_name>")
@budget_ns.param("workflow_name", "Workflow name")
class BudgetDetailApi(Resource):
    @budget_ns.doc("get_budget")
    @budget_ns.doc(description="Get budget details for a workflow")
    @budget_ns.response(200, "Success", budget_model)
    @budget_ns.response(404, "Not found")
    @validate_app_token
    def get(self, app_model: App, workflow_name: str):
        """Get budget details for a specific workflow."""
        budget = BudgetWatchdogLayer.get_workflow_budget(app_model.tenant_id, workflow_name)
        if budget is None:
            raise NotFound(f"Budget for workflow '{workflow_name}' not found")
        return budget.to_dict(), 200


@budget_ns.route("/<string:workflow_name>/reset")
@budget_ns.param("workflow_name", "Workflow name")
class BudgetResetApi(Resource):
    @budget_ns.expect(budget_reset_model)
    @budget_ns.doc("reset_budget")
    @budget_ns.doc(description="Reset a workflow budget for a new window")
    @budget_ns.response(200, "Success", budget_model)
    @budget_ns.response(404, "Not found")
    @validate_app_token
    def post(self, app_model: App, workflow_name: str):
        """Reset a workflow budget."""
        budget = BudgetWatchdogLayer.get_workflow_budget(app_model.tenant_id, workflow_name)
        if budget is None:
            raise NotFound(f"Budget for workflow '{workflow_name}' not found")

        data = request.get_json(force=True)
        token_limit = int(data.get("token_limit", budget.token_limit))
        cost_limit_cents = int(data.get("cost_limit_cents", budget.cost_limit_cents))
        window_str = data.get("window", "daily")
        try:
            window = BudgetWindow(window_str)
        except ValueError:
            raise BadRequest(f"Invalid window '{window_str}'. Valid: daily, weekly, monthly")

        budget.reset(token_limit, cost_limit_cents, window)
        return budget.to_dict(), 200


@budget_ns.route("/team")
class TeamBudgetApi(Resource):
    @budget_ns.doc("get_team_budget")
    @budget_ns.doc(description="Get the team budget configuration")
    @budget_ns.response(200, "Success", team_budget_model)
    @budget_ns.response(404, "Not found")
    @validate_app_token
    def get(self, app_model: App):
        """Get the team budget."""
        team = BudgetWatchdogLayer.get_team_budget(app_model.tenant_id)
        if team is None:
            raise NotFound("No team budget configured")
        return team.to_dict(), 200

    @budget_ns.expect(team_budget_create_model)
    @budget_ns.doc("create_team_budget")
    @budget_ns.doc(description="Create or update the team budget")
    @budget_ns.response(201, "Created", team_budget_model)
    @budget_ns.response(400, "Bad request")
    @validate_app_token
    def post(self, app_model: App):
        """Create a team budget."""
        data = request.get_json(force=True)
        team_name = data.get("team_name")
        if not team_name:
            raise BadRequest("team_name is required")

        token_limit = int(data["token_limit"])
        cost_limit_cents = int(data["cost_limit_cents"])
        period_days = int(data.get("period_days", 30))

        BudgetWatchdogLayer.configure_team_budget(
            app_model.tenant_id,
            team_name,
            token_limit,
            cost_limit_cents,
            period_days,
        )
        team = BudgetWatchdogLayer.get_team_budget(app_model.tenant_id)
        return team.to_dict(), 201


@budget_ns.route("/alerts")
class BudgetAlertsApi(Resource):
    @budget_ns.doc("get_alerts")
    @budget_ns.doc(description="Get budget alert history")
    @budget_ns.response(200, "Success", alert_list_model)
    @validate_app_token
    def get(self, app_model: App):
        """Get all budget alerts for this tenant."""
        alerts = BudgetWatchdogLayer.get_alerts(app_model.tenant_id)
        return {
            "alerts": [{
                "timestamp": a.timestamp,
                "workflow": a.workflow,
                "level": a.level.value,
                "message": a.message,
            } for a in alerts],
            "total": len(alerts),
        }, 200
