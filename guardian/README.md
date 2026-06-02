# Guardian — Workflow Conservation Engine

Your workflow costs $12/day. Two nodes account for 78% of tokens. They both call GPT-4 for tasks GPT-4o-mini handles.

Guardian is a Python module that analyzes Dify workflows for cost efficiency and detects waste. It doesn't change your workflows — it tells you what to change and why.

## What It Does

**Budget tracking** — Set hard limits on tokens per run, cost per day, and node count. Know immediately when a workflow crosses a threshold.

**DAG analysis** — Parse any Dify workflow JSON and surface:
- Redundant LLM calls (same model, same upstream, same job)
- Dead branches (conditional paths that never execute)

**Per-node profiling** — Track tokens in/out, latency, and cost for every node across runs. Spot degradation before it hurts.

**Waste detection** — Find the expensive stuff nobody notices:
- **Overprompted nodes** — 4,200 tokens in, 180 out. You're paying for context the model ignores.
- **Idle nodes** — Running every time, contributing 0.1% of value.
- **Model mismatch** — Using GPT-4 for classification that GPT-4o-mini handles in 12ms.

**Reports** — Markdown summaries you can paste into Slack, Notion, or a PR comment.

## Install

```bash
cd guardian && pip install -e .
```

## Quick Start

```python
from guardian.budget import WorkflowBudget
from guardian.analyzer import WorkflowDAG
from guardian.profiler import Profiler, NodeSample
from guardian.detector import WasteDetector
from guardian.report import render_report

# 1. Load a workflow
dag = WorkflowDAG.from_dict(workflow_json)
print(f"{len(dag.llm_nodes())} LLM nodes, {len(dag.redundant_llm_calls())} redundant")

# 2. Profile some runs
profiler = Profiler()
profiler.record(NodeSample(
    node_id="summarizer",
    input_tokens=4200,
    output_tokens=180,
    latency_ms=820.0,
    cost_usd=0.015,
))

# 3. Detect waste
detector = WasteDetector(profiler)
findings = detector.detect()
for f in findings:
    print(f"[{f.severity}] {f.message}")
    print(f"  → {f.suggestion}")

# 4. Generate report
budget = WorkflowBudget()
report = render_report(budget=budget, dag=dag, profiler=profiler, findings=findings)
print(report)
```

## Example Output

```
# Conservation Report — Customer Support Pipeline

## Budget Summary
- Max tokens / run: 500,000
- Today's spend: $12.43

## DAG Analysis
- Total nodes: 14
- LLM nodes: 4
- Redundant LLM calls: 1
  - `Draft Email` ↔ `Draft Email 2` (same model & upstream)

## Waste Findings

### 🔴 Overprompted — Summarizer
Node 'summarizer' receives 4,200 tokens avg but outputs 180 (ratio 23.3×).

> **Suggestion:** Consider extractive pre-filtering, summarization, or
> reducing the prompt template size.

### 🔴 Expensive Model — classify, summarize
Two nodes account for 78% of tokens. If they use GPT-4, consider
downgrading for simple tasks.

> **Suggestion:** Classification and extraction run fine on gpt-4o-mini.
```

## Module Structure

| File | Purpose |
|------|---------|
| `budget.py` | `WorkflowBudget` — token/cost/node limits and daily tracking |
| `analyzer.py` | `WorkflowDAG` — parse workflow JSON, find redundancies and dead branches |
| `profiler.py` | `Profiler`, `NodeProfile`, `NodeSample` — per-node stats and trends |
| `detector.py` | `WasteDetector`, `WasteFinding` — surface actionable waste |
| `report.py` | `render_report()` — Markdown conservation reports |
| `tests/test_guardian.py` | Full pytest suite |

## Tests

```bash
cd guardian && python -m pytest tests/ -v
```

## Philosophy

Guardian doesn't optimize your workflows. It tells you where the money goes and what to do about it. The fixes are yours to make — but at least you'll know where to look.

Built for [SuperInstance](https://github.com/SuperInstance).
