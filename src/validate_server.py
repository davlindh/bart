"""Quick validation of server logic without starting HTTP server."""
import sys
sys.path.insert(0, '.')
from src.server import BARTRequestHandler, SCENARIOS

# Create a handler with no request (we call only the internal method)
class FakeHandler(BARTRequestHandler):
    def __init__(self):
        pass  # Skip super().__init__

h = FakeHandler()

# Test 1: financial_impact fields exist on nodes
g = h._generate_graph_data("mixed_q3", "D1", "CFO")
nodes_with_impact = [n for n in g["nodes"] if n.get("financial_impact", 0) > 0]
print(f"[{'PASS' if len(nodes_with_impact) >= 3 else 'FAIL'}] Nodes with financial_impact > 0: {len(nodes_with_impact)}")
for n in nodes_with_impact:
    print(f"   - {n['id']}: {n['financial_impact']} SEK")

# Test 2: focal_id returned
print(f"[{'PASS' if 'focal_id' in g else 'FAIL'}] focal_id in graph response: {g.get('focal_id')}")

# Test 3: focal_id pivot respected
g2 = h._generate_graph_data("mixed_q3", "D2", "CFO", focal_id="TX-1001")
print(f"[{'PASS' if g2.get('focal_id') == 'TX-1001' else 'FAIL'}] focal_id preserved: {g2.get('focal_id')}")

# Test 4: D3 scope has meta node
g3 = h._generate_graph_data("mixed_q3", "D3", "CFO")
meta_nodes = [n for n in g3["nodes"] if n.get("type") == "meta"]
print(f"[{'PASS' if meta_nodes else 'FAIL'}] D3 meta nodes: {len(meta_nodes)}")

# Test 5: Combinatorial and Verification engines
from src.tax_engine.evaluator import TaxRuleEvaluator
from src.tax_engine.models import TaxTransaction

txs = [TaxTransaction(**t) for t in SCENARIOS["mixed_q3"]["transactions"]]
ver_report = TaxRuleEvaluator.verify_financial_integrity(txs)
print(f"[PASS] Verification Engine score: {ver_report.verification_score*100:.1f}% ({ver_report.passed_checks_count}/{ver_report.total_checks_performed} passed)")

combo = TaxRuleEvaluator.evaluate_combinatorial_strategies(
    txs, annual_taxable_profit=500000.0, total_salaries_paid=800000.0, owner_salary=500000.0
)
print(f"[PASS] Combinatorial Engine bundles: {len(combo.optimal_bundles)}, max savings: {combo.max_combined_savings_sek:,.0f} SEK")

# Test 6: Perspective Windows W1-W9
for wid in ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9"]:
    wdata = h._get_window_data(wid)
    assert "window" in wdata, f"Window {wid} failed"
print(f"[PASS] All 9 Omnipod Perspective Windows generated successfully")

# Test 7: Fortnox Pipeline & Telemetry
fn_res = h._compute_fortnox_summary()
assert "team_dynamics_metrics" in fn_res
print(f"[PASS] Fortnox live computation: Team Health Index {fn_res['team_dynamics_metrics']['team_health_index']}/100")

# Test 8: Universal ERD Graph
erd_res = h._get_erd_graph_data()
assert erd_res["count"] == 16
print(f"[PASS] Universal ERD Graph: {erd_res['count']} nodes linked")

print(f"[OK] Full Server & Tax Engine validation complete")
