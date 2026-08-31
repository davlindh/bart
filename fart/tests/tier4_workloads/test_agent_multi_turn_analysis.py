"""
Tier 4: Real-World Application Workload - Autonomous Agent Multi-Turn Data Science Analysis.
Simulates a multi-turn autonomous AI agent performing complex data analysis:
- Turn 1: Ingests/generates synthetic financial transaction records and calculates summary statistics.
- Turn 2: Filters anomalies and groups transactions by product category.
- Turn 3: Computes profit margins and growth trends.
- Turn 4: Produces structured summary and visual chart representation (base64).
"""

import json
import pytest

try:
    from antigravity.sandbox.manager import SandboxManager
except ImportError:
    from tests.conftest import SandboxManager


class TestAgentMultiTurnAnalysis:
    """Real-world workload test simulating an autonomous data science agent."""

    def test_multi_turn_financial_dataset_analysis_workflow(self, sandbox_manager: SandboxManager):
        """
        Executes a 4-turn data analysis pipeline maintaining REPL state:
        Turn 1: Generate synthetic transactions and compute basic stats.
        Turn 2: Group by category and compute sub-totals.
        Turn 3: Compute profit margins.
        Turn 4: Generate JSON summary output with simulated chart encoding.
        """
        sandbox = sandbox_manager.create_sandbox()
        assert sandbox is not None

        # Turn 1: Data Generation & Descriptive Statistics
        turn1_code = (
            "import math, json\n"
            "transactions = [\n"
            "    {'id': i, 'category': 'Cloud' if i % 2 == 0 else 'Hardware', 'rev': 1000 + i * 50, 'cost': 600 + i * 30}\n"
            "    for i in range(20)\n"
            "]\n"
            "total_rev = sum(t['rev'] for t in transactions)\n"
            "total_cost = sum(t['cost'] for t in transactions)\n"
            "mean_rev = total_rev / len(transactions)\n"
            "print(f'Turn1: TotalRev={total_rev}, MeanRev={mean_rev}')\n"
        )
        t1_res = sandbox.execute(turn1_code, repl=True)
        assert t1_res.exit_code == 0
        if t1_res.stdout:
            assert "TotalRev=" in t1_res.stdout

        # Turn 2: Category Grouping & Aggregation
        turn2_code = (
            "category_stats = {}\n"
            "for t in transactions:\n"
            "    cat = t['category']\n"
            "    if cat not in category_stats:\n"
            "        category_stats[cat] = {'rev': 0, 'cost': 0, 'count': 0}\n"
            "    category_stats[cat]['rev'] += t['rev']\n"
            "    category_stats[cat]['cost'] += t['cost']\n"
            "    category_stats[cat]['count'] += 1\n"
            "print(f'Categories={list(category_stats.keys())}')\n"
        )
        t2_res = sandbox.execute(turn2_code, repl=True)
        assert t2_res.exit_code == 0
        if t2_res.stdout:
            assert "Cloud" in t2_res.stdout
            assert "Hardware" in t2_res.stdout

        # Turn 3: Margin & Growth Metric Calculation
        turn3_code = (
            "for cat, stats in category_stats.items():\n"
            "    margin = (stats['rev'] - stats['cost']) / stats['rev']\n"
            "    stats['margin_pct'] = round(margin * 100, 2)\n"
            "print(json.dumps(category_stats))\n"
        )
        t3_res = sandbox.execute(turn3_code, repl=True)
        assert t3_res.exit_code == 0
        if t3_res.stdout:
            assert "margin_pct" in t3_res.stdout

        # Turn 4: Final Summary & Artifact Preparation
        turn4_code = (
            "final_report = {\n"
            "    'transaction_count': len(transactions),\n"
            "    'total_revenue': total_rev,\n"
            "    'total_cost': total_cost,\n"
            "    'net_profit': total_rev - total_cost,\n"
            "    'categories': category_stats,\n"
            "    'chart_artifact': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='\n"
            "}\n"
            "print(json.dumps(final_report))\n"
        )
        t4_res = sandbox.execute(turn4_code, repl=True)
        assert t4_res.exit_code == 0
        if t4_res.stdout:
            assert "transaction_count" in t4_res.stdout
            assert "chart_artifact" in t4_res.stdout
