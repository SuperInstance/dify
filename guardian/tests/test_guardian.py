"""Tests for the guardian module."""

from __future__ import annotations

import pytest

from guardian.budget import WorkflowBudget
from guardian.analyzer import WorkflowDAG
from guardian.profiler import Profiler, NodeSample
from guardian.detector import WasteDetector, WasteFinding
from guardian.report import render_report


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class TestWorkflowBudget:
    def test_default_limits(self):
        b = WorkflowBudget()
        assert b.max_tokens_per_run == 500_000
        assert b.max_cost_per_day == 50.0
        assert b.max_nodes_per_workflow == 100

    def test_is_within_budget_ok(self):
        b = WorkflowBudget()
        assert b.is_within_budget(100_000, 50_000) is True

    def test_is_within_budget_exceeds_tokens(self):
        b = WorkflowBudget(max_tokens_per_run=1_000)
        assert b.is_within_budget(800, 300) is False

    def test_is_within_budget_exceeds_daily_cost(self):
        b = WorkflowBudget(max_cost_per_day=0.01)
        b.record_run(100_000, 50_000)
        assert b.is_within_budget(100_000, 50_000) is False

    def test_record_run_returns_cost(self):
        b = WorkflowBudget()
        cost = b.record_run(1_000, 1_000)
        assert cost > 0
        assert b.daily_spend() == cost

    def test_check_node_count(self):
        b = WorkflowBudget(max_nodes_per_workflow=5)
        assert b.check_node_count(5) is True
        assert b.check_node_count(6) is False

    def test_avg_tokens_per_run(self):
        b = WorkflowBudget()
        b.record_run(1_000, 500)
        b.record_run(2_000, 500)
        assert b.avg_tokens_per_run() == 2_000.0

    def test_avg_tokens_no_runs(self):
        b = WorkflowBudget()
        assert b.avg_tokens_per_run() == 0.0


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class TestWorkflowDAG:
    @pytest.fixture()
    def sample_dag(self) -> WorkflowDAG:
        raw = {
            "graph": {
                "nodes": [
                    {"id": "start", "data": {"type": "start", "title": "Start"}},
                    {"id": "llm1", "data": {"type": "llm", "title": "Draft Email", "model": {"provider": "openai", "name": "gpt-4"}}},
                    {"id": "llm2", "data": {"type": "llm", "title": "Draft Email 2", "model": {"provider": "openai", "name": "gpt-4"}}},
                    {"id": "if1", "data": {"type": "if-else", "title": "Check Urgency"}},
                    {"id": "tool1", "data": {"type": "tool", "title": "Send Slack"}},
                    {"id": "end", "data": {"type": "end", "title": "End"}},
                ],
                "edges": [
                    {"sourceId": "start", "targetId": "llm1"},
                    {"sourceId": "start", "targetId": "llm2"},
                    {"sourceId": "llm1", "targetId": "if1"},
                    {"sourceId": "if1", "targetId": "tool1"},
                    {"sourceId": "if1", "targetId": "end"},
                ],
            }
        }
        return WorkflowDAG.from_dict(raw)

    def test_parse_nodes(self, sample_dag: WorkflowDAG):
        assert len(sample_dag.nodes) == 6
        assert sample_dag.entry_node == "start"

    def test_llm_nodes(self, sample_dag: WorkflowDAG):
        llms = sample_dag.llm_nodes()
        assert len(llms) == 2

    def test_redundant_llm_calls(self, sample_dag: WorkflowDAG):
        redundant = sample_dag.redundant_llm_calls()
        assert len(redundant) == 1
        a, b = redundant[0]
        assert "llm" in a.id and "llm" in b.id

    def test_from_empty_dict(self):
        dag = WorkflowDAG.from_dict({})
        assert len(dag.nodes) == 0


# ---------------------------------------------------------------------------
# Profiler
# ---------------------------------------------------------------------------

class TestProfiler:
    @pytest.fixture()
    def profiler_with_data(self) -> Profiler:
        p = Profiler()
        for i in range(20):
            p.record(NodeSample(
                node_id="summarizer",
                input_tokens=4_200,
                output_tokens=180,
                latency_ms=800.0 + i * 10,
                cost_usd=0.015,
                node_title="Summarizer",
            ))
        p.record(NodeSample(
            node_id="classifier",
            input_tokens=500,
            output_tokens=10,
            latency_ms=200.0,
            cost_usd=0.002,
            node_title="Classifier",
        ))
        return p

    def test_run_count(self, profiler_with_data: Profiler):
        p = profiler_with_data.get("summarizer")
        assert p is not None
        assert p.run_count == 20

    def test_avg_tokens(self, profiler_with_data: Profiler):
        p = profiler_with_data.get("summarizer")
        assert p.avg_input_tokens == 4_200.0
        assert p.avg_output_tokens == 180.0

    def test_input_output_ratio(self, profiler_with_data: Profiler):
        p = profiler_with_data.get("summarizer")
        assert p.input_output_ratio == pytest.approx(4200 / 180, rel=0.01)

    def test_top_by_cost(self, profiler_with_data: Profiler):
        top = profiler_with_data.top_by_cost(1)
        assert top[0].node_id == "summarizer"

    def test_is_degrading(self, profiler_with_data: Profiler):
        p = profiler_with_data.get("summarizer")
        # Record more with much higher latency to trigger degradation
        for i in range(10):
            profiler_with_data.record(NodeSample(
                node_id="summarizer",
                input_tokens=4_200,
                output_tokens=180,
                latency_ms=2000.0 + i * 100,
                cost_usd=0.015,
            ))
        assert p.is_degrading() is True

    def test_not_degrading(self):
        p = Profiler()
        for i in range(20):
            p.record(NodeSample(
                node_id="stable",
                input_tokens=100,
                output_tokens=100,
                latency_ms=500.0,
                cost_usd=0.01,
            ))
        profile = p.get("stable")
        assert profile is not None
        assert profile.is_degrading() is False


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class TestWasteDetector:
    @pytest.fixture()
    def detector(self) -> WasteDetector:
        p = Profiler()
        for _ in range(10):
            p.record(NodeSample(
                node_id="summarizer",
                input_tokens=4_200,
                output_tokens=180,
                latency_ms=800.0,
                cost_usd=0.015,
                node_title="Summarizer",
            ))
        for _ in range(10):
            p.record(NodeSample(
                node_id="rephraser",
                input_tokens=500,
                output_tokens=500,
                latency_ms=300.0,
                cost_usd=0.005,
                node_title="Rephraser",
            ))
        return WasteDetector(p)

    def test_detect_finds_overprompted(self, detector: WasteDetector):
        findings = detector.detect()
        categories = [f.category for f in findings]
        assert "overprompted" in categories

    def test_overprompted_message(self, detector: WasteDetector):
        findings = [f for f in detector.detect() if f.category == "overprompted"]
        assert len(findings) == 1
        assert "4,200" in findings[0].message
        assert "180" in findings[0].message

    def test_no_findings_on_empty(self):
        p = Profiler()
        d = WasteDetector(p)
        assert d.detect() == []


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_renders_markdown(self):
        b = WorkflowBudget()
        p = Profiler()
        p.record(NodeSample(
            node_id="test",
            input_tokens=1000,
            output_tokens=100,
            latency_ms=500.0,
            cost_usd=0.01,
            node_title="Test Node",
        ))
        findings = [WasteFinding(
            node_id="test",
            node_title="Test Node",
            category="overprompted",
            severity="high",
            message="Test message",
            suggestion="Test suggestion",
        )]
        report = render_report(budget=b, profiler=p, findings=findings, workflow_name="TestFlow")
        assert "# Conservation Report — TestFlow" in report
        assert "Budget Summary" in report
        assert "Top Nodes by Cost" in report
        assert "Waste Findings" in report
        assert "Test Node" in report

    def test_empty_report(self):
        report = render_report(workflow_name="Empty")
        assert "Conservation Report" in report
